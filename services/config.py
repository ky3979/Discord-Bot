"""Config file to hold project level configuration"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    """Base config object"""
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    DEV_ID: str = os.getenv('DEV_ID', '')
    GENERAL_CHANNEL_ID: str = os.getenv('GENERAL_CHANNEL_ID', '')
    GUILD_ID: str = os.getenv('GUILD_ID', '')
    BOT_CHANNEL_ID: str = os.getenv('BOT_CHANNEL_ID', '')
    FIREBASE_CREDENTIALS: str = os.getenv('FIREBASE_CREDENTIALS', '')
    FRIDAY_VIDEO_1: str = 'https://twitter.com/Killer7Friday/status/1296914978830561281?s=20'
    FRIDAY_VIDEO_2: str = 'https://cdn.discordapp.com/attachments/284467072979828747/747220691073499206/fridaynight.mov'
    SATURDAY_VIDEO_1: str = 'https://twitter.com/and_dads_car/status/1238751722476011520?s=21'
    SATURDAT_VIDEO_2: str = 'https://cdn.discordapp.com/attachments/284467072979828747/766770256164683807/viQI8AX_tsxEtOlj.mp4'
    SUNDAY_VIDEO_1: str = 'https://twitter.com/fckitsasunday/status/1246686644243234818'
    SUNDAY_VIDEO_2: str = 'https://www.youtube.com/watch?v=cU1E3Bxo2ww&feature=youtu.be'
    COOL_ROLE: str = os.getenv('COOL_ROLE', '')
    UNCOOL_ROLE: str = os.getenv('UNCOOL_ROLE', '')

@dataclass
class Color:
    PURPLE: int = 0xd14fcd
    BROWN: int = 0x593018
    YELLOW: int = 0xe7c90b
    RED: int = 0xff0000

config = Config()
color = Color()
