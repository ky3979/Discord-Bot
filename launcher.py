"""Initializes the bot"""
import logging
import json
from services.dusty_bot import DustyBot

VERSION = '0.0.6v'
VERSION_NOTES = f"""```
{VERSION} (Latest):
\t- Fixed patch notes sending bug
0.0.5v:
\t- Restructured config file
\t- Fixed disconnect message bug
\t- Code refactoring
0.0.4v:
\t- Added a simple poll command. Use '!help poll' to learn more!
```"""

logging.basicConfig(level=logging.INFO)
dusty_bot = DustyBot()
dusty_bot.run(VERSION, VERSION_NOTES)
