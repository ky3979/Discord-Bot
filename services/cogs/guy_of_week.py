"""Guy of the week cog"""
import discord
import logging
from discord import Embed
from discord.utils import get, find
from services.config import color, config
from apscheduler.triggers.cron import CronTrigger
from discord.ext.commands import Cog, command, has_any_role, has_role
from datetime import datetime, timedelta
from pytz import timezone
from services.extensions import firebase_handler
from services.cogs.member_emote import get_default_emote_queue
from services.schemas.guy_of_week_data import (
    PreviousGuy,
    Nominee,
    PollData
)

class GuyOfWeek(Cog):
    """Guy of the week poll system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_id = None
        self.complete_poll_job = None

        settings_ref = firebase_handler.query_firestore(u'poll_settings', 'guy_of_week')
        settings = settings_ref.get().to_dict()
        self.poll_job = self.bot.scheduler.add_job(
            self.send_guy_of_week_polls,
            CronTrigger(
                day_of_week=settings['day'],
                hour=settings['hour'],
                minute=settings['minute'],
                second=0,
                timezone='EST5EDT'
            )
        )
        next_run_time = self.poll_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"GuyOfWeek.send_guy_of_week_polls" next run time: {next_run_time}')
    
    def get_poll_deadline(self, today):
        """Return the deadline for the polls"""
        settings_ref = firebase_handler.query_firestore(u'poll_settings', 'guy_of_week')
        settings = settings_ref.get().to_dict()
        return today + timedelta(seconds=int(settings['duration']))

    def generate_data(self, data_type):
        """Generate, store, and return poll data"""
        if data_type == 'cool_guy':
            role_name = str(config.COOL_ROLE)
        else:
            role_name = str(config.UNCOOL_ROLE)
        data_ref = firebase_handler.query_firestore(data_type, self.data_id)

        # Get previous guy
        role = find(
            lambda r: r.name == role_name,
            self.bot.guild.roles
        )
        prev_cool_guy = next(
            (PreviousGuy(member.display_name, f'{member.id}') for member \
             in self.bot.guild.members \
             if role in member.roles),
             PreviousGuy()
        )

        # Get nominees
        nominees = [Nominee(
                        member.display_name,
                        f'{member.id}'
                    ) for member 
                      in self.bot.guild.members
                      if not member.top_role.name == 'Bots'
                      and not member.bot]

        # Construct, store, and return data
        data = PollData(
            prev_cool_guy,
            nominees,
            datetime.now().strftime('%Y-%m-%d'),
        )
        data_ref.set(PollData.Schema().dump(data))
        return data_ref

    def generate_embed(self, title, description, color, fields, footer=None):
        """Generate and return poll embed"""
        embed = Embed(
            title=title,
            description=description,
            color=color
        )
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=self.bot.guild.icon_url)
        if footer is not None:
            embed.set_footer(text=footer)
        return embed

    def generate_nominees_text(self, poll_data):
        """Generate and return the nominees value"""
        nominees = ""
        default_emotes = get_default_emote_queue()
        for nominee in poll_data['nominees']:
            emote_ref = firebase_handler.query_firestore(u'member_emotes', str(nominee['id']))
            member_emote = emote_ref.get().to_dict()
            if member_emote is None:
                # Use defaults
                emote = default_emotes.pop(0)
            else:
                # Use custom
                emote = member_emote['emote']
            nominees += f"{emote} {nominee['name']}\n"
        return nominees

    async def generate_guy_poll(self, title, color, fields, doc_ref, data):
        """Generate, send, and return the poll message"""

        # Create poll embed
        embed = self.generate_embed(
            title=title,
            description=f'{self.bot.guild.default_role}',
            color=color,
            fields=fields,
            footer='React to cast a vote!'
        )
        message = await self.bot.general_channel.send(embed=embed)
        data['message_id'] = f'{message.id}'
        data['channel_id'] = f'{message.channel.id}'
        doc_ref.update(data)

        # Add reaction options and pin poll
        default_emotes = get_default_emote_queue()
        for nominee in data['nominees']:
            emote_ref = firebase_handler.query_firestore(u'member_emotes', str(nominee['id']))
            member_emote = emote_ref.get().to_dict()
            if member_emote is None:
                # Use defaults
                emote = default_emotes.pop(0)
            else:
                # Use custom
                emote = member_emote['emote']
            await message.add_reaction(emote)
        try:
            await message.pin()
        except:
            pass
        return message

    async def get_results(self, cool_data, uncool_data):
        """Return the person with the most votes from each poll"""
        cool_guy_message = await self.bot.get_channel(int(cool_data['channel_id'])).fetch_message(cool_data['message_id'])
        cool_guy_results = max(cool_guy_message.reactions, key=lambda r: r.count)
        cool_guy_idx = cool_guy_message.reactions.index(cool_guy_results)
        new_cool_guy = self.bot.guild.get_member(int(cool_data['nominees'][cool_guy_idx]['id']))

        uncool_guy_message = await self.bot.get_channel(int(uncool_data['channel_id'])).fetch_message(uncool_data['message_id'])
        uncool_guy_results = max(uncool_guy_message.reactions, key=lambda r: r.count)
        uncool_guy_idx = uncool_guy_message.reactions.index(uncool_guy_results)
        new_uncool_guy = self.bot.guild.get_member(int(uncool_data['nominees'][uncool_guy_idx]['id']))

        return {
            'cool': {
                'user': new_cool_guy,
                'votes': cool_guy_results.count,
                'message': cool_guy_message
            },
            'uncool': {
                'user': new_uncool_guy,
                'votes': uncool_guy_results.count,
                'message': uncool_guy_message
            }
        }
    
    async def set_new_roles(self, pre_cool_id, pre_uncool_id, results):
        """Give winner their roles and remove previous winners of roles"""
        cool_guy_role = get(self.bot.guild.roles, name=config.COOL_ROLE)
        if pre_cool_id is not None:
            old_cool_guy = self.bot.guild.get_member(pre_cool_id)
            try:
                await old_cool_guy.remove_roles(cool_guy_role)
            except Exception as e:
                await self.bot.general_channel.send(f'**Error:** {e}')

        uncool_guy_role = get(self.bot.guild.roles, name=config.UNCOOL_ROLE)
        if pre_uncool_id is not None:
            old_uncool_guy = self.bot.guild.get_member(pre_uncool_id)
            try:
                await old_uncool_guy.remove_roles(uncool_guy_role)
            except Exception as e:
                await self.bot.general_channel.send(f'**Error:** {e}')

        # Give winner 'cool guy of the week' role
        try:
            await results['cool']['user'].add_roles(cool_guy_role)
        except Exception as e:
            await self.bot.general_channel.send(f'**Error:** {e}')
        
        try:
            await results['uncool']['user'].add_roles(uncool_guy_role)
        except Exception as e:
            await self.bot.general_channel.send(f'**Error:** {e}')

    async def send_guy_of_week_polls(self):
        """Send weekly guy of week polls"""

        # Generate this week's data
        today = datetime.now(timezone('US/Eastern'))
        self.data_id = f'{today.year}{today.month:02}{today.day:02}'

        cool_guy_ref = self.generate_data('cool_guy')
        uncool_guy_ref = self.generate_data('uncool_guy')
        cool_guy_data = cool_guy_ref.get().to_dict()
        uncool_guy_data = uncool_guy_ref.get().to_dict()

        # Get poll deadline
        deadline = self.get_poll_deadline(today)

        # Get poll nominees
        nominees = self.generate_nominees_text(cool_guy_data)

        # Send polls
        cool_guy_poll = await self.generate_guy_poll(
            title='Cool Guy of the Week Poll',
            color=color.PURPLE,
            fields=[
                ('Previous Cool Guy:', cool_guy_data['previous_guy']['name'], True),
                ('Deadline:', "Today @ " + deadline.strftime('%I:%M %p'), True),
                ('\n**Nominees:**', nominees, False)
            ],
            doc_ref=cool_guy_ref,
            data=cool_guy_data
        )
        uncool_guy_poll = await self.generate_guy_poll(
            title='Uncool Guy of the Week Poll',
            color=color.BROWN,
            fields=[
                ('Previous Uncool Guy:', uncool_guy_data['previous_guy']['name'], True),
                ('Deadline:', "Today @ " + deadline.strftime('%I:%M %p'), True),
                ('\n**Nominees:**', nominees, False)
            ],
            doc_ref=uncool_guy_ref,
            data=uncool_guy_data
        )

        # Setup jobs to finish polls
        self.complete_poll_job = self.bot.scheduler.add_job(
            self.complete_poll, 
            "date", 
            run_date=deadline, 
            args=[cool_guy_data, uncool_guy_data]
        )

    async def complete_poll(self, cool_guy_data, uncool_guy_data):
        """Find winner of poll and change their roles"""

        # Get results
        results = await self.get_results(cool_guy_data, uncool_guy_data)

        # Create embeds and send results
        cool_guy_embed = self.generate_embed(
            title='Cool Guy Results',
            description=f"{results['cool']['user'].mention}",
            color=color.PURPLE,
            fields=[('Winning Votes', results['cool']['votes'], False)]
        )
        uncool_guy_embed = self.generate_embed(
            title='Uncool Guy Results',
            description=f"{results['uncool']['user'].mention} sucks",
            color=color.BROWN,
            fields=[('Winning Votes', results['uncool']['votes'], False)]
        )
        await self.bot.general_channel.send(embed=cool_guy_embed)
        await self.bot.general_channel.send(embed=uncool_guy_embed)

        # Remove previous cool guy 'cool guy of the week' role and
        # give winner 'cool guy of the week' role
        await self.set_new_roles(
            int(cool_guy_data['previous_guy']['id']),
            int(uncool_guy_data['previous_guy']['id']),
            results
        )
        
        # Unpin and delete message
        try:
            await results['cool']['message'].unpin()
            await results['uncool']['message'].unpin()
            await results['cool']['message'].delete()
            await results['uncool']['message'].delete()
        except:
            pass

        next_run_time = self.poll_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"GuyOfWeek.create_guy_of_week_poll" next run time: {next_run_time}')

    @command()
    @has_role('Developer')
    async def start_poll(self, ctx):
        """Start the guy of week polls"""
        await self.send_guy_of_week_polls()

    @command()
    @has_any_role('Developer', 'Daddies')
    async def end_poll(self, ctx):
        """Force end the poll"""
        cool_guy_ref = firebase_handler.query_firestore(u'cool_guy', self.data_id)
        uncool_guy_ref = firebase_handler.query_firestore(u'uncool_guy', self.data_id)
        cool_guy_data = cool_guy_ref.get().to_dict()
        uncool_guy_data = uncool_guy_ref.get().to_dict()
        await self.complete_poll(cool_guy_data, uncool_guy_data)
        self.complete_poll_job.pause()
        self.complete_poll_job.remove()

    @command()
    @has_any_role('Developer', 'Daddies')
    async def next_poll(self, ctx):
        """Show the next poll run time"""
        date = self.poll_job.next_run_time
        await ctx.send(f"The next poll will be send on {date.strftime('%A, %b %d')} at {date.strftime('%I:%M %p')}")

    @command(aliases=['set'])
    @has_any_role('Developer', 'Daddies')
    async def set_poll_time(self, ctx, arg: str, value: int):
        """
        Set when the poll happens

        Parameters:
        -----------
        arg - string, either day, duration, hour, or minute
        value - int, 
        \tday - 0, 1, 2, .., 6 (MON = 0, SUN = 6)
        \tduration - seconds (Ex. 21600 = 6 hours)
        \tthour - 0, 1, 2, ..., 23 (Military hours)
        \tminute - 0, 1, 2, ..., 59
        """
        settings_ref = firebase_handler.query_firestore(u'poll_settings', 'guy_of_week')
        settings = settings_ref.get().to_dict()

        arg = arg.lower()
        if arg == 'day':
            if value > 6 or value < 0:
                await ctx.send('Please use a value between 0 and 6')
                return
            settings['day'] = value
        elif arg == 'duration':
            settings['duration'] = value
        elif arg == 'hour':
            if value > 23 or value < 0:
                await ctx.send('Please use a value between 0 and 23')
                return
            settings['hour'] = value
        elif arg == 'minute':
            if value > 59 or value < 0:
                await ctx.send('Please use a value between 0 and 59')
                return
            settings['minute'] = value
        else:
            await ctx.send('Invalid type to change. Try again')
            return
        
        settings_ref.update(settings)
        self.poll_job.reschedule(
            CronTrigger(
                day_of_week=settings['day'],
                hour=settings['hour'],
                minute=settings['minute'],
                second=0
            )
        )
        date = self.poll_job.next_run_time
        await ctx.send(f"Guy of the week polls will now be sent every {date.strftime('%A')} at {date.strftime('%I:%M %p')}")

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle multiple reactions on the same message"""

        # Get the message
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not message.embeds or payload.member.bot:
            return

        # Remove previous reaction from message
        if message.embeds[0].title == 'Cool Guy of the Week Poll':
            cool_guy_ref = firebase_handler.query_firestore(u'cool_guy', self.data_id)
            cool_guy_data = cool_guy_ref.get().to_dict()
            if message.id != int(cool_guy_data['message_id']):
                return
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and (reaction.emoji != payload.emoji and reaction.emoji != payload.emoji.name)):
                    await message.remove_reaction(reaction.emoji, payload.member)
        elif message.embeds[0].title == 'Uncool Guy of the Week Poll':
            uncool_guy_ref = firebase_handler.query_firestore(u'uncool_guy', self.data_id)
            uncool_guy_data = uncool_guy_ref.get().to_dict()
            if message.id != int(uncool_guy_data['message_id']):
                return
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and (reaction.emoji != payload.emoji and reaction.emoji != payload.emoji.name)):
                    await message.remove_reaction(reaction.emoji, payload.member)
        elif message.embeds[0].title == 'Question:':
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and reaction.emoji != payload.emoji.name):
                    await message.remove_reaction(reaction.emoji, payload.member)

def setup(bot):
    """Add this cog"""
    bot.add_cog(GuyOfWeek(bot))
