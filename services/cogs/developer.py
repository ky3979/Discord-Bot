"""Developer cog"""
import discord
from discord.utils import find, get
from discord.ext.commands import command, has_any_role, has_role, Cog

class Developer(Cog):
    """For use of a developer or server owner"""
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=['ld'], hidden=True)
    @has_role('Developer')
    async def load(self, ctx, ext):
        """Load a cog extension"""
        try:
            self.bot.load_extension(f'services.cogs.{ext}')
        except Exception as e:
            await ctx.send(f"** ERROR ** {e}")
        else:
            await ctx.send("** SUCCESS **")

    @command(aliases=['uld'], hidden=True)
    @has_role('Developer')
    async def unload(self, ctx, ext):
        """Unload a cog extension"""
        try:
            self.bot.unload_extension(f'services.cogs.{ext}')
        except Exception as e:
            await ctx.send(f"** ERROR ** {e}")
        else:
            await ctx.send("** SUCCESS **")

    @command(aliases=['rld'], hidden=True)
    @has_role('Developer')
    async def reload(self, ctx, ext):
        """Reload a cog extension"""
        try:
            self.bot.unload_extension(f'services.cogs.{ext}')
            self.bot.load_extension(f'services.cogs.{ext}')
        except Exception as e:
            await ctx.send(f"** ERROR ** {e}")
        else:
            await ctx.send("** SUCCESS **")

    @command(aliases=['rmrole'], hidden=True)
    @has_any_role('Developer')
    async def remove_role(self, ctx, member_name, role):
        """Remove a role from a member"""
        member = find(
            lambda m: m.display_name == member_name or m.name == member_name,
            self.bot.guild.members
        )
        role = get(self.bot.guild.roles, name=role)
        try:
            await member.remove_roles(role)
        except Exception as e:
            await ctx.send(f'Could not remove role from member. <{e}>')
        else:
            await ctx.send(f'Member no longer has role "{role}"')

    @command(aliases=['gvrole'], hidden=True)
    @has_any_role('Developer')
    async def give_role(self, ctx, member_name, role):
        """Add a role to a member"""
        member = find(
            lambda m: m.display_name == member_name or m.name == member_name,
            self.bot.guild.members
        )
        role = get(self.bot.guild.roles, name=role)
        try:
            await member.add_roles(role)
        except Exception as e:
            await ctx.send(f'Could not add role for member. <{e}>')
        else:
            await ctx.send(f'Member now has role "{role}"')
    
    @command(hidden=True)
    @has_role('Developer')
    async def patch_notes(self, ctx):
        await ctx.message.delete()
        await self.bot.general_channel.send(f'Dusty Bot **{self.bot.VERSION}** has been deloyed!\n{self.bot.VERSION_NOTES}')

def setup(bot):
    """Add this cog"""
    bot.add_cog(Developer(bot))
