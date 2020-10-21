"""Poll cog class"""
import discord
from discord import Embed
from discord.ext.commands import command, Cog
from services.extensions import firebase_handler
from services.config import color
from services.cogs.member_emote import get_default_emote_queue

MAX_POLL_OPTIONS = 10

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
        if len(args) > MAX_POLL_OPTIONS:
            # Error on max optionss
            await ctx.send('You can only use a maximum of 10 custom options.')
            return
        await ctx.message.delete()

        # Creating poll embed
        embed = Embed(
            title=f'Question:',
            description=question,
            color=color.YELLOW
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
        embed.set_footer(text='Check "!help poll" to make polls!')

        # Send poll and reacting options
        message = await ctx.send(embed=embed)
        for emote in reactions:
            await message.add_reaction(emote)

def setup(bot):
    """Add this cog"""
    bot.add_cog(Poll(bot))
