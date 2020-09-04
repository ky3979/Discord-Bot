"""Guy of the week cog"""
import discord
import logging
from discord import Embed
from discord.utils import get, find
from services.config import color, config
from apscheduler.triggers.cron import CronTrigger
from discord.ext.commands import Cog, command, has_any_role
from datetime import datetime, timedelta
from services.extensions import firebase_handler
from services.schemas.guy_of_week_data import (
    PreviousGuy,
    Nominee,
    PollData
)

NUMBERS = ["0⃣", "1️⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

class GuyOfWeek(Cog):
    """Guy of the week poll system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.is_cool_poll_done = False
        self.is_uncool_poll_done = False
        self.data_id = None
        self.update_job = None
        self.complete_poll_job = None

        settings_ref = firebase_handler.query_firestore(u'poll_settings', 'guy_of_week')
        settings = settings_ref.get().to_dict()
        self.poll_job = self.bot.scheduler.add_job(
            self.create_guy_of_week_poll,
            CronTrigger(
                day_of_week=settings['day'],
                hour=settings['hour'],
                minute=settings['minute'],
                second=0,
                timezone='EST5EDT'
            )
        )
        next_run_time = self.poll_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"GuyOfWeek.create_guy_of_week_poll" next run time: {next_run_time}')

    def generate_data(self, data_type):
        """Generate new poll data and store it into firebase"""
        if data_type == 'cool_guy':
            role_name = str(config['COOL_ROLE'])
        else:
            role_name = str(config['UNCOOL_ROLE'])

        data_ref = firebase_handler.query_firestore(data_type, self.data_id)

        # Get previous guy
        role = find(
            lambda r: r.name == role_name,
            self.bot.guild.roles
        )
        prev_cool_guy = next(
            (PreviousGuy(member.display_name, member.id) for member \
             in self.bot.guild.members \
             if role in member.roles),
             PreviousGuy()
        )

        # Get nominees
        nominees = [Nominee(
                        member.display_name,
                        member.id
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
        """Generate poll embed"""
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
    
    async def create_guy_of_week_poll(self):
        """Send weekly guy of week polls"""

        # Get guy of week data or create new data
        today = datetime.now()
        self.data_id = f'{today.year}{today.month:02}{today.day:02}'

        cool_guy_ref = self.generate_data('cool_guy')
        cool_guy_data = cool_guy_ref.get().to_dict()
        uncool_guy_ref = self.generate_data('uncool_guy')
        uncool_guy_data = uncool_guy_ref.get().to_dict()

        # Construct and send polls
        settings_ref = firebase_handler.query_firestore(u'poll_settings', 'guy_of_week')
        settings = settings_ref.get().to_dict()
        deadline = today + timedelta(seconds=int(settings['duration']))
        
        cool_guy_embed = self.generate_embed(
            title='Cool Guy of the Week Poll',
            description=f'{self.bot.guild.default_role}',
            color=color['PURPLE'],
            fields=[
                ('Previous Cool Guy:', cool_guy_data['previous_guy']['name'], True),
                ('Deadline:', "Today @ " + deadline.strftime('%I:%M %p'), True),
                ('\n**Nominees:**', '\n'.join([f"{NUMBERS[cool_guy_data['nominees'].index(nominee)]} {nominee['name']}" for nominee in cool_guy_data['nominees']]), False)
            ],
            footer='React to cast a vote!'
        )
        uncool_guy_embed = self.generate_embed(
            title='Uncool Guy of the Week Poll',
            description=f'{self.bot.guild.default_role}',
            color=color['BROWN'],
            fields=[
                ('Previous Uncool Guy:', uncool_guy_data['previous_guy']['name'], True),
                ('Deadline:', "Today @ " + deadline.strftime('%I:%M %p'), True),
                ('\n**Nominees:**', '\n'.join([f"{NUMBERS[uncool_guy_data['nominees'].index(nominee)]} {nominee['name']}" for nominee in uncool_guy_data['nominees']]), False)
            ],
            footer='React to cast a vote!'
        )
        cool_guy_message = await self.bot.general_channel.send(embed=cool_guy_embed)
        uncool_guy_message = await self.bot.general_channel.send(embed=uncool_guy_embed)
        
        cool_guy_data['message_id'] = cool_guy_message.id
        cool_guy_data['channel_id'] = cool_guy_message.channel.id
        cool_guy_ref.update(cool_guy_data)

        uncool_guy_data['message_id'] = uncool_guy_message.id
        uncool_guy_data['channel_id'] = uncool_guy_message.channel.id
        uncool_guy_ref.update(uncool_guy_data)

        # Add bot reactions and pin message
        for emoji in NUMBERS[:len(cool_guy_data['nominees'])]:
            await cool_guy_message.add_reaction(emoji)
            await uncool_guy_message.add_reaction(emoji)
        try:
            await cool_guy_message.pin()
            await uncool_guy_message.pin()
        except:
            pass

        # Setup jobs
        self.update_job = self.bot.scheduler.add_job(
            self.update_vote, 
            "interval", 
            minutes=1,
        )
        self.complete_poll_job = self.bot.scheduler.add_job(
            self.complete_poll, 
            "date", 
            run_date=deadline, 
            args=[cool_guy_data, uncool_guy_data]
        )

    async def update_vote(self):
        """Update the vote count every minute"""
        cool_guy_ref = firebase_handler.query_firestore(u'cool_guy', self.data_id)
        cool_guy_data = cool_guy_ref.get().to_dict()
        uncool_guy_ref = firebase_handler.query_firestore(u'uncool_guy', self.data_id)
        uncool_guy_data = uncool_guy_ref.get().to_dict()

        # Update cool guy vote counts and check if everyone already voted
        cool_guy_votes = 0
        cool_guy_message = await self.bot.get_channel(cool_guy_data['channel_id']).fetch_message(cool_guy_data['message_id'])
        for reaction, nominee in zip(cool_guy_message.reactions, cool_guy_data['nominees']):
            nominee['votes'] = reaction.count
            cool_guy_votes += (reaction.count - 1)
        cool_guy_ref.update(cool_guy_data)

        if cool_guy_votes >= len(cool_guy_data['nominees']) - 1:
            self.is_cool_poll_done = True

        # Update uncool guy vote counts and check if everyone already voted
        uncool_guy_votes = 0
        uncool_guy_message = await self.bot.get_channel(uncool_guy_data['channel_id']).fetch_message(uncool_guy_data['message_id'])
        for reaction, nominee in zip(uncool_guy_message.reactions, uncool_guy_data['nominees']):
            nominee['votes'] = reaction.count
            uncool_guy_votes += (reaction.count - 1)
        uncool_guy_ref.update(uncool_guy_data)

        if uncool_guy_votes >= len(uncool_guy_data['nominees']) - 1:
            self.is_uncool_poll_done = True

        # Check if everyone votes, end polls
        if self.is_cool_poll_done and self.is_uncool_poll_done:
            await self.complete_poll(cool_guy_data, uncool_guy_data)
            self.complete_poll_job.pause()
            self.complete_poll_job.remove()

    async def complete_poll(self, cool_guy_data, uncool_guy_data):
        """Find winner of poll and change their roles"""

        # Stop vote updater job
        self.update_job.pause()
        self.update_job.remove()
        self.is_cool_poll_done = False
        self.is_uncool_poll_done = False

        # Get results
        cool_guy_message = await self.bot.get_channel(cool_guy_data['channel_id']).fetch_message(cool_guy_data['message_id'])
        cool_guy_results = max(cool_guy_message.reactions, key=lambda r: r.count)
        cool_guy_idx = cool_guy_message.reactions.index(cool_guy_results)
        new_cool_guy = self.bot.guild.get_member(cool_guy_data['nominees'][cool_guy_idx]['id'])

        uncool_guy_message = await self.bot.get_channel(uncool_guy_data['channel_id']).fetch_message(uncool_guy_data['message_id'])
        uncool_guy_results = max(uncool_guy_message.reactions, key=lambda r: r.count)
        uncool_guy_idx = uncool_guy_message.reactions.index(uncool_guy_results)
        new_uncool_guy = self.bot.guild.get_member(uncool_guy_data['nominees'][uncool_guy_idx]['id'])

        # Create embeds and send results
        cool_guy_embed = self.generate_embed(
            title='Cool Guy Results',
            description=f'{new_cool_guy.mention}',
            color=color['PURPLE'],
            fields=[('Winning Votes', cool_guy_results.count, False)]
        )
        uncool_guy_embed = self.generate_embed(
            title='Uncool Guy Results',
            description=f'{new_uncool_guy.mention} sucks',
            color=color['BROWN'],
            fields=[('Winning Votes', uncool_guy_results.count, False)]
        )
        await cool_guy_message.channel.send(embed=cool_guy_embed)
        await uncool_guy_message.channel.send(embed=uncool_guy_embed)

        # Remove previous cool guy 'cool guy of the week' role
        cool_guy_role = find(
            lambda r: r.name == str(config['COOL_ROLE']),
            self.bot.guild.roles
        )
        if cool_guy_data['previous_guy']['id'] is not None:
            old_cool_guy = self.bot.guild.get_member(cool_guy_data['previous_guy']['id'])
            try:
                await old_cool_guy.remove_roles(cool_guy_role)
            except Exception as e:
                await message.channel.send(f'**Error:** {e}')

        uncool_guy_role = find(
            lambda r: r.name == str(config['UNCOOL_ROLE']),
            self.bot.guild.roles
        )
        if uncool_guy_data['previous_guy']['id'] is not None:
            old_uncool_guy = self.bot.guild.get_member(uncool_guy_data['previous_guy']['id'])
            try:
                await old_uncool_guy.remove_roles(uncool_guy_role)
            except Exception as e:
                await message.channel.send(f'**Error:** {e}')

        # Give winner 'cool guy of the week' role
        try:
            await new_cool_guy.add_roles(cool_guy_role)
        except Exception as e:
            await message.channel.send(f'**Error:** {e}')
        
        try:
            await new_uncool_guy.add_roles(uncool_guy_role)
        except Exception as e:
            await message.channel.send(f'**Error:** {e}')
        
        # Unpin and delete message
        try:
            await cool_guy_message.unpin()
            await uncool_guy_message.unpin()
            await cool_guy_message.delete()
            await uncool_guy_message.delete()
        except:
            pass

        next_run_time = self.poll_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"GuyOfWeek.create_guy_of_week_poll" next run time: {next_run_time}')

    @command(aliases=['end'])
    @has_any_role('Developer', 'Dusty Boy')
    async def force_end(self, ctx):
        """Force end the poll"""
        cool_guy_ref = firebase_handler.query_firestore(u'cool_guy', self.data_id)
        cool_guy_data = cool_guy_ref.get().to_dict()
        uncool_guy_ref = firebase_handler.query_firestore(u'uncool_guy', self.data_id)
        uncool_guy_data = uncool_guy_ref.get().to_dict()
        await self.complete_poll(cool_guy_data, uncool_guy_data)
        self.complete_poll_job.pause()
        self.complete_poll_job.remove()

    @command(aliases=['set'])
    @has_any_role('Developer', 'Dusty Boy')
    async def settings(self, ctx, arg: str, value: int):
        """
        Change when polls occur\n
        Valid args: day, duration, hour, minute\n
        Valid arg values:\n
        \tday - 0, 1, 2, .., 6 (MON = 0, SUN = 6)\n
        \tduration - seconds (Ex. 21600 = 6 hours)\n
        \thour - 0, 1, 2, ..., 23 (Military hours)\n
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
        await ctx.send(f"Guy of the week polls will now be sent every {DAYS[date.weekday()]} at {date.strftime('%I:%M %p')}")

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle multiple reactions from same user"""
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not message.embeds or payload.member.bot:
            return

        if message.embeds[0].title == 'Cool Guy of the Week Poll':
            cool_guy_ref = firebase_handler.query_firestore(u'cool_guy', self.data_id)
            cool_guy_data = cool_guy_ref.get().to_dict()
            if message.id != cool_guy_data['message_id']:
                return
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and reaction.emoji != payload.emoji.name):
                    await message.remove_reaction(reaction.emoji, payload.member)
        elif message.embeds[0].title == 'Uncool Guy of the Week Poll':
            uncool_guy_ref = firebase_handler.query_firestore(u'uncool_guy', self.data_id)
            uncool_guy_data = uncool_guy_ref.get().to_dict()
            if message.id != uncool_guy_data['message_id']:
                return
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and reaction.emoji != payload.emoji.name):
                    await message.remove_reaction(reaction.emoji, payload.member)

def setup(bot):
    """Add this cog"""
    bot.add_cog(GuyOfWeek(bot))
