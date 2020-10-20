"""Poll cog class"""
import discord
from discord import Embed
from discord.ext.commands import command, Cog
from services.extensions import firebase_handler
from services.config import color
from services.cogs.member_emote import get_default_emote_queue

class Poll(Cog):
    """Simple poll system"""

    def __init__(self, bot):
        self.bot = bot

    @command()
    async def poll(self, ctx, question, *args):
        """
        Create a simple poll
        
        Parameters:
        -----------
        question - The poll question
        args... - Custom options separated by spaces

        Examples:
        ---------
        Yes/No poll - !poll "Do you like Issac?"
        Custom options poll - !poll "Do you like Issac?" "I love him" "He's okay" "No" "I hate him"
        """
        if len(args) > 10:
            await ctx.send('You can only use a maximum of 10 custom options.')
            return

        await ctx.message.delete()

        embed = Embed(
            title=f'Question:',
            description=question,
            color=color['YELLOW']
        )

        if args:
            emotes = get_default_emote_queue()
            options = '\n'.join([f'{emotes.pop(0)} {opt}' for opt in args])
            emotes = get_default_emote_queue()
            reactions = [emotes.pop(0) for x in args]
            fields = [(
                '**Options:**',
                options,
                False
            )]
        else:
            reactions = ['👍', '👎']
            fields = [
                ('**Options**', ':thumbsup: Yes', True),
                ('--------', ':thumbsdown: No', True),
            ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text='Check "!help poll" to make polls!')

        message = await ctx.send(embed=embed)

        for emote in reactions:
            await message.add_reaction(emote)

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
        elif message.embeds[0].title == 'Question:':
            for reaction in message.reactions:
                if (payload.member in await reaction.users().flatten()
                    and reaction.emoji != payload.emoji.name):
                    await message.remove_reaction(reaction.emoji, payload.member)

def setup(bot):
    """Add this cog"""
    bot.add_cog(Poll(bot))
