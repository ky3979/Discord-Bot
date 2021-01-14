"""Valorant rank tracking cog"""
import re
import requests
import discord
import asyncio
from aiohttp import ClientSession
from discord import Embed, File
from discord.ext.commands import command, Cog
from services.extensions import firebase_handler
from services.schemas.valorant_auth import ValorantAuthSchema
from services.config import color

class ValorantRankTracker(Cog):
    """Apex Legends API handler"""
    def __init__(self, bot):
        self.bot = bot
        self.ranks = ''

    @command(aliases=['vallogin'])
    async def valorant_login(self, ctx, username, password):
        """
        Authenticate yourself to the Dusty Bot Valorant rank tracker
        
        Parameters:
        -----------
        username - Your login username
        password - Your login password

        Examples:
        ---------
        !vallogin USERNAME PASSWORD
        """
        await self.authenticate(username, password, ctx.message.author.id)

        # Delete message
        await ctx.send("**Logged In Successfully!**")

    async def authenticate(self, username, password, discord_id):
        """Authenticate and store the user's credentials to firebase"""
        session = ClientSession()
        data = {
            'client_id': 'play-valorant-web-prod',
            'nonce': '1',
            'redirect_uri': 'https://playvalorant.com/opt_in',
            'response_type': 'token id_token',
        }
        await session.post('https://auth.riotgames.com/api/v1/authorization', json=data)

        data = {
            'type': 'auth',
            'username': username,
            'password': password
        }

        # Get access token
        async with session.put('https://auth.riotgames.com/api/v1/authorization', json=data) as r:
            data = await r.json()
        print(data)
        pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
        data = pattern.findall(data['response']['parameters']['uri'])[0]
        access_token = data[0]

        # Get entitlements token
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        async with session.post('https://entitlements.auth.riotgames.com/api/token/v1', headers=headers, json={}) as r:
            data = await r.json()
        entitlements_token = data['entitlements_token']

        # Get user id
        async with session.post('https://auth.riotgames.com/userinfo', headers=headers, json={}) as r:
            data = await r.json()
        user_id = data['sub']

        # Store data in firebase
        doc_ref = firebase_handler.query_firestore(u'valorant_auth', str(discord_id))
        data = ValorantAuthSchema(
            access_token,
            entitlements_token,
            user_id,
            discord_id
        )
        doc_ref.set(ValorantAuthSchema.Schema().dump(data))

        data = doc_ref.get().to_dict()
        if data is None:
            raise Exception("Failed to login.")
        await session.close()

    @command(aliases=['valrank'])
    async def valorant_rank(self, ctx):
        """Show your Valorant RP, ELO, and RP progression"""
        # Get user credentials from firebase
        doc_ref = firebase_handler.query_firestore(u'valorant_auth', str(ctx.message.author.id))
        data = doc_ref.get().to_dict()
        if data is None:
            await ctx.send("You have not authenticated yourself yet. DM bot and do this command to login: ```!vallogin USERNAME PASSWORD```")
            return

        # Get RP and rank
        await self.get_cloud_rank()
        current_rp, rank_num = await self.update_comp_rank(data)
        elo = (rank_num * 100) - 300 + current_rp

        if current_rp == -1:
            progression = await self.progression_text(data)
            embed = Embed(
                title='UNRANKED',
                description=f'```HTTP\nUNKNOWN```',
                color=color.RED
            )
            embed.add_field(name='Progression', value=progression, inline=True)
            await ctx.send(embed=embed) 
        elif current_rp == -2:
            await ctx.send("Your login has timed out. Please relog.")
            return
        elif current_rp == -3:
            await ctx.send("Something wrong happened while getting your rank.")
            return
        else:
            progression = await self.progression_text(data)
            img_file = File(f'assets/valorant/TX_CompetitiveTier_Large_{rank_num}.png', filename='rank.png')
            embed = Embed(
                title=self.ranks[f'{rank_num}'].upper(),
                description=f'```HTTP\n{current_rp} RP | {elo} ELO```',
                color=color.RED
            )
            embed.set_thumbnail(url='attachment://rank.png')
            embed.add_field(name='Progression', value=progression, inline=True)
            await ctx.send(file=img_file, embed=embed) 
        
    async def get_cloud_rank(self):
        res = requests.get('https://502.wtf/ValorrankInfo.json')
        if res.ok:
            self.ranks = res.json()['Ranks']

    async def update_comp_rank(self, data):
        """Get the updated rank"""
        try:
            res = requests.get(
                f'https://pd.na.a.pvp.net/mmr/v1/players/{data["user_id"]}/competitiveupdates?startIndex=0&endIndex=20',
                headers={
                    'Authorization': 'Bearer ' + data['access_token'],
                    'X-Riot-Entitlements-JWT': data['entitlements_token']
                }
            )
            if res.ok:
                for game in res.json()['Matches']:
                    if game['TierAfterUpdate'] != 0:
                        return game["RankedRatingAfterUpdate"], game['TierAfterUpdate']
                return -1, 3
            return -2, 0
        except Exception:
            return -3, 0

    async def progression_text(self, data):
        """Get the tier progression history"""
        progression = '```diff\n'
        try:
            res = requests.get(
                f'https://pd.na.a.pvp.net/mmr/v1/players/{data["user_id"]}/competitiveupdates?startIndex=0&endIndex=20',
                headers={
                    'Authorization': 'Bearer ' + data['access_token'],
                    'X-Riot-Entitlements-JWT': data['entitlements_token']
                }
            )
            if res.ok:
                counter = 0
                for game in res.json()['Matches']:
                    if counter == 5:
                        break
                    if game['TierAfterUpdate'] != 0:
                        if game['TierAfterUpdate'] > game['TierBeforeUpdate']:
                            # Promoted
                            progress_diff = (game['RankedRatingAfterUpdate'] + 100) -game['RankedRatingBeforeUpdate']
                        elif game['TierAfterUpdate'] < game['TierBeforeUpdate']:
                            # Demoted
                            progress_diff = (game['RankedRatingAfterUpdate'] - 100) - game['RankedRatingBeforeUpdate']
                        else:
                            progress_diff = game['RankedRatingAfterUpdate'] - game['RankedRatingBeforeUpdate']
                        if progress_diff > 0:
                            progress_diff = f'+{progress_diff}'
                        counter += 1
                progression += '```'
                return progression
            progression += 'No Data Available```'
            return progression
        except Exception:
            progression += 'No Data Available```'
            return progression

def setup(bot):
    """Add this cog"""
    bot.add_cog(ValorantRankTracker(bot))
