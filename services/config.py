"""Config file to hold project level configuration"""
import os
from dotenv import load_dotenv

load_dotenv()
config = {
    'BOT_TOKEN': os.getenv('BOT_TOKEN', ''),
    'DEV_ID': os.getenv('DEV_ID', ''),
    'GENERAL_CHANNEL_ID': os.getenv('GENERAL_CHANNEL_ID', ''),
    'GUILD_ID': os.getenv('GUILD_ID', ''),
    'BOT_CHANNEL_ID': os.getenv('BOT_CHANNEL_ID', ''),
    'FIREBASE_CREDENTIALS': os.getenv('FIREBASE_CREDENTIALS', ''),
    'FRIDAY_VIDEO_1': 'https://twitter.com/Killer7Friday/status/1296914978830561281?s=20',
    'FRIDAY_VIDEO_2': 'https://cdn.discordapp.com/attachments/284467072979828747/747220691073499206/fridaynight.mov',
    'SATURDAY_VIDEO': 'https://twitter.com/and_dads_car/status/1238751722476011520?s=21',
    'SUNDAY_VIDEO_1': 'https://twitter.com/fckitsasunday/status/1246686644243234818',
    'SUNDAY_VIDEO_2': 'https://www.youtube.com/watch?v=cU1E3Bxo2ww&feature=youtu.be',
    'COOL_ROLE': os.getenv('COOL_ROLE', ''),
    'UNCOOL_ROLE': os.getenv('UNCOOL_ROLE', ''),
}
color = {
    'PURPLE': 0xd14fcd,
    'BROWN': 0x593018,
    'YELLOW': 0xe7c90b,
}
version_updates = "```\n\
0.0.4v (Latest):\n\
\t- Added a simple poll command. Use '!help poll' to learn more! \n\
0.0.34v:\n\
\t- Display name bug fix on set_emote command \n\
\t- Added custom emotes for polls \n\
```"
