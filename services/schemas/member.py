"""Discord member schema"""
from typing import List
from dataclasses import field
from marshmallow_dataclass import dataclass
from marshmallow import Schema, fields

@dataclass
class Member:
    """A member in the discord guild"""
    roles: List[str]
    name: str
    id: int
