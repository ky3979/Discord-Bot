"""Discord member emote schema"""
from marshmallow_dataclass import dataclass

@dataclass
class MemberEmoteSchema:
    """A member emote in the discord guild"""
    name: str
    emote: str
