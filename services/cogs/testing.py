"""Testing cog class"""
import discord
from services.config import config
from discord.ext.commands import command, Cog, has_role
from discord.utils import find
from services.extensions import firebase_handler

class Testing(Cog):
    """Testing extension"""

    def __init__(self, bot):
        self.bot = bot

    @command(hidden=True)
    async def test(self, ctx):
        """Test command"""
        await ctx.send('Test!')

    @command(hidden=True)
    async def test_firebase(self, ctx):
        """Test firebase calls"""
        me = find(
            lambda m: m.id == 152950882315665410,
            self.bot.guild.members
        )
        doc_ref = firebase_handler.query_firestore(u'members', str(me.id))
        data = doc_ref.get().to_dict()
        if data is not None:
            await ctx.send(data['name'])

    @command(hidden=True)
    async def test_config(self, ctx):
        """Test firebase calls"""
        await ctx.send(f"{config['DEV_ID']}")
        await ctx.send(f"{config['COOL_ROLE']}")

    @command(hidden=True)
    async def test_mention(self, ctx):
        """Test firebase calls"""
        await self.bot.bot_channel.send(self.bot.guild.default_role)

def setup(bot):
    """Add this cog"""
    bot.add_cog(Testing(bot))
