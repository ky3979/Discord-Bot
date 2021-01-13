"""Valorant user auth schema"""
from marshmallow_dataclass import dataclass

@dataclass
class ValorantAuthSchema:
    """A user's valorent authentication"""
    access_token: str
    entitlements_token: str
    user_id: str
    discord_id: str
