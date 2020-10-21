"""Initializes the bot"""
import logging
import json
from services.dusty_bot import DustyBot

VERSION = '0.0.4v'
VERSION_NOTES = "```\n\
0.0.5v (Latest):\n\
\t- Restructured config file \n\
\t- Fixed disconnect message bug \n\
\t- Code refactoring \n\
0.0.4v:\n\
\t- Added a simple poll command. Use '!help poll' to learn more! \n\
0.0.34v:\n\
\t- Display name bug fix on set_emote command \n\
\t- Added custom emotes for polls \n\
```"

logging.basicConfig(level=logging.INFO)
dusty_bot = DustyBot()
dusty_bot.run(VERSION, VERSION_NOTES)
