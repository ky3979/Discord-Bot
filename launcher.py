"""Initializes the bot"""
import logging
import json
from services.dusty_bot import DustyBot

VERSION = '0.0.12v'
VERSION_NOTES = f"""```
{VERSION} (Latest):
\t- Fixed guy of week voting bug
0.0.11v:
\t- Add valorant rank tracker (Need to authenticate with !vallogin then do !valrank)
0.0.10v:
\t- Add apex legends map rotation tracker
```"""

logging.basicConfig(level=logging.INFO)
dusty_bot = DustyBot()
dusty_bot.run(VERSION, VERSION_NOTES)
