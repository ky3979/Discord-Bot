"""Data for guy of the week schema"""
from datetime import datetime
from typing import List
from dataclasses import field
from marshmallow_dataclass import dataclass

@dataclass
class PreviousGuy:
    """The previous guy"""
    name: str = field(default='None')
    id: int = field(default=None)

@dataclass
class Nominee:
    """Guy of the week nominee"""
    name: str = field(default='None')
    id: int = field(default=None)

@dataclass
class PollData:
    """Used to Poll data"""
    previous_guy: PreviousGuy
    nominees: List[Nominee]
    created_on: str = field(default=datetime.now().strftime('%Y-%m-%d'))
    message_id: int = field(default=None)
    channel_id: int = field(default=None)
