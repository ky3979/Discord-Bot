"""Apex Legends API cog"""
import requests
import discord
from datetime import timedelta
from discord import Embed
from discord.utils import find
from discord.ext.commands import command, Cog

class ApexLegends(Cog):
    """Apex Legends API handler"""
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=['map'])
    async def apex_map(self, ctx):
        response = requests.get('https://fn.alphaleagues.com/v1/apex/map')
        if not response.ok:
            await ctx.send('Could not get the map data.')
            return
        map_data = response.json()

        map_name = map_data['map']
        time_remaining = str(timedelta(seconds=map_data['times']['remaining']['seconds']))

        embed = Embed()
        embed.description = f"The current map is **{map_name}**\nNext rotation: **{time_remaining}**"

        if map_name == 'Olympus':
            embed.set_image(url='https://sdcore.dev/cdn/ApexStats/Maps/Olympus.png')
        elif map_name == 'World\'s Edge':
            embed.set_image(url='https://sdcore.dev/cdn/ApexStats/Maps/WorldsEdge.png')
        elif map_name == 'King\'s Canyon':
            embed.set_image(url='https://sdcore.dev/cdn/ApexStats/Maps/KingsCanyon.png')

        await ctx.send(embed=embed)

def setup(bot):
    """Add this cog"""
    bot.add_cog(ApexLegends(bot))
