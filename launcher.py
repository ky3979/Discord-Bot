"""Initializes the bot"""
import logging
import json
from services.dusty_bot import DustyBot

VERSION = '0.0.33v'

logging.basicConfig(level=logging.INFO)
dusty_bot = DustyBot()
dusty_bot.run(VERSION)
