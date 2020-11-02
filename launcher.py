"""Initializes the bot"""
import logging
import json
from services.dusty_bot import DustyBot

VERSION = '0.0.7v'
VERSION_NOTES = f"""```
{VERSION} (Latest):
\t- Upgrade bot to newest version of DiscordPy API
```"""

logging.basicConfig(level=logging.INFO)
dusty_bot = DustyBot()
dusty_bot.run(VERSION, VERSION_NOTES)
