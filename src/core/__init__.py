"""
NYTimes Pips Solver - Core Game Logic

Provides:
- Domino: Immutable domino value object
- Region constraints: Sum, Equal, NotEqual, GreaterThan, LessThan
- Board: Game board with placement logic and AI interface
"""

from .domino import Domino, DominoSet
from .region import (
    Region,
    SumRegion,
    EqualRegion,
    NotEqualRegion,
    GreaterThanRegion,
    LessThanRegion
)
from .board import Board

__all__ = [
    'Domino',
    'DominoSet',
    'Region',
    'SumRegion',
    'EqualRegion',
    'NotEqualRegion',
    'GreaterThanRegion',
    'LessThanRegion',
    'Board'
]

__version__ = '1.0.0'