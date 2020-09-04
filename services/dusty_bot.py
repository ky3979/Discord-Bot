"""Discord bot class"""
import os
import discord
from services.config import config, version_updates
from discord.errors import Forbidden
from discord.ext.commands import Bot, CommandNotFound, BadArgument, MissingRequiredArgument
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.extensions import firebase_handler
from services.schemas.member import (
    Member
)

PREFIX='!'
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)

class DustyBot(Bot):
    """The discord bot"""

    def __init__(self):
        """Bot constructor"""
        super().__init__(
            command_prefix=PREFIX,
            description='Official Dusty server bot',
            owner_id=int(config['DEV_ID'])
        )
        self.token = config['BOT_TOKEN']
        self.guild = None
        self.general_channel = None
        self.bot_channel = None
        self.ready = False
        self.scheduler = AsyncIOScheduler()
        self.VERSION = None

    def run(self, version):
        """Start the bot"""
        self.VERSION = version
        super().run(self.token, reconnect=True)

    def loadCogs(self):
        """Load the cogs"""
        for filename in os.listdir('./services/cogs'):
            if filename.endswith('.py'):
                try:
                    self.load_extension(f'services.cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load extension <{filename[:-3]}>.', e)

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            self.guild = self.get_guild(int(config['GUILD_ID']))
            self.general_channel = self.get_channel(int(config['GENERAL_CHANNEL_ID']))
            self.bot_channel = self.get_channel(int(config['BOT_CHANNEL_ID']))
            self.scheduler.start()
            self.loadCogs()
            print(f'\nLogged in as ({self.user.name} : {self.user.id})\n')
            # await self.general_channel.send(f'Dusty Bot **{self.VERSION}** has been deloyed!\n{version_updates}')

    async def on_member_join(self, member):
        doc_ref = firebase_handler.query_firestore(u'members', str(member.id))
        data = Member(
            [str(role) for role in member.roles],
            member.display_name,
            member.id
        )
        doc_ref.set(Member.Schema().dump(data))

    async def on_member_remove(self, member):
        firebase_handler.query_firestore(u'members', str(member.id)).delete()

    async def on_member_update(self, before, after):
        doc_ref = firebase_handler.query_firestore(u'members', str(after.id))
        data = doc_ref.get().to_dict()
        if data is None:
            return
        if before.nick != after.nick:
            data['name'] = after.display_name
        if before.roles != after.roles:
            data['roles'] = [str(role) for role in after.roles]
        doc_ref.update(data)

    async def on_command_error(self, ctx, err):
        if any([isinstance(err, error) for error in IGNORE_EXCEPTIONS]):
            await ctx.send(f'**Error:** {err}')
            raise err
        elif isinstance(err, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")
        elif hasattr(err, "original"):
            if isinstance(err.original, Forbidden):
                await ctx.send("I do not have permission to do that.")
            else:
                await ctx.send(f'**Error:** {err}')
                raise err.original
        else:
            await ctx.send(f'**Error:** {err}')
            raise err

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

    async def close(self):
        await super().close()
        self.scheduler.shutdown()
        print(f'\nLogged off as ({self.user.name} : {self.user.id})\n')
        