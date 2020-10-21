"""Member custom emote cog"""
import discord
from discord.utils import find
from discord.ext.commands import command, Cog, has_any_role
from services.extensions import firebase_handler
from services.schemas.member_emote import (
    MemberEmoteSchema
)

def get_default_emote_queue():
    """Return the default emotes"""
    return ["0⃣", "1️⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]

class MemberEmote(Cog):
    """Member display emote in cool/uncool polls"""
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=['emote'])
    @has_any_role('Developer', 'Daddies')
    async def set_emote(self, ctx, emote, member_name=None):
        """
        Set a member's emote

        Parameters:
        -----------
        emote - emoji, the emote to set to
        member_name (optional) - string, specified member to change. Defaulted to yourself
        """

        # Get member object
        if member_name is None:
            member = ctx.author
        else:
            member = find(
                lambda m: m.display_name == member_name or m.name == member_name,
                self.bot.guild.members
            )
        
        # Update member's emote in the firestore
        doc_ref = firebase_handler.query_firestore(u'member_emotes', str(member.id))
        member_emote = doc_ref.get().to_dict()
        if member_emote is None:
            member_emote = MemberEmoteSchema(member.display_name, emote)
            doc_ref.set(MemberEmoteSchema.Schema().dump(member_emote))
            await ctx.send(f'New profile created for **{str(member)}** with emote "{emote}"')
        else:
            member_emote['emote'] = emote
            doc_ref.update(member_emote)
            await ctx.send(f'Update profile for **{str(member)}** with emote "{emote}"')

def setup(bot):
    """Add this cog"""
    bot.add_cog(MemberEmote(bot))
