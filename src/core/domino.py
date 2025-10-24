"""
Domino value object for NYTimes Pips solver.
Immutable representation of a domino piece with pip values 0-6.
"""
from typing import Tuple, Set
from dataclasses import dataclass


@dataclass(frozen=True)
class Domino:
    """
    Immutable value object representing a domino piece.
    
    A domino has two halves, each showing 0-6 pips.
    Dominoes are identified uniquely regardless of orientation
    (e.g., 2-4 and 4-2 are the same domino).
    
    Attributes:
        left (int): Pip count on left half (0-6)
        right (int): Pip count on right half (0-6)
        id (str): Normalized unique identifier
    
    Example:
        >>> domino = Domino(3, 5)
        >>> domino.left
        3
        >>> domino.right
        5
        >>> domino.is_double()
        False
    """
    
    left: int
    right: int
    
    def __post_init__(self):
        """Validate pip values after initialization."""
        if not (0 <= self.left <= 6):
            raise ValueError(f"Pip values must be between 0 and 6, got left={self.left}")
        if not (0 <= self.right <= 6):
            raise ValueError(f"Pip values must be between 0 and 6, got right={self.right}")
    
    @property
    def id(self) -> str:
        """
        Get normalized unique identifier for this domino.
        
        The ID is normalized so that 2-4 and 4-2 have the same ID.
        Format: "{min}-{max}" where min <= max.
        
        Returns:
            str: Normalized domino identifier (e.g., "2-4")
        """
        min_val = min(self.left, self.right)
        max_val = max(self.left, self.right)
        return f"{min_val}-{max_val}"
    
    def is_double(self) -> bool:
        """
        Check if this is a double domino (same value on both sides).
        
        Returns:
            bool: True if left == right, False otherwise
        
        Example:
            >>> Domino(4, 4).is_double()
            True
            >>> Domino(3, 5).is_double()
            False
        """
        return self.left == self.right
    
    def get_pips(self) -> Tuple[int, int]:
        """
        Get both pip values as a tuple.
        
        Returns:
            Tuple[int, int]: (left, right) pip values
        """
        return (self.left, self.right)
    
    def contains_pip(self, value: int) -> bool:
        """
        Check if this domino contains a specific pip value.
        
        Args:
            value (int): Pip value to check (0-6)
        
        Returns:
            bool: True if either half has this value
        
        Example:
            >>> Domino(3, 6).contains_pip(3)
            True
            >>> Domino(3, 6).contains_pip(5)
            False
        """
        return value in (self.left, self.right)
    
    def total_pips(self) -> int:
        """
        Calculate total pip count (sum of both halves).
        
        Returns:
            int: Sum of left and right pip values
        
        Example:
            >>> Domino(3, 5).total_pips()
            8
        """
        return self.left + self.right
    
    def __eq__(self, other) -> bool:
        """
        Check equality based on normalized ID.
        
        Dominoes are equal if they have the same pip values,
        regardless of left/right order.
        
        Args:
            other: Object to compare
        
        Returns:
            bool: True if same domino
        """
        if not isinstance(other, Domino):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """
        Hash based on normalized ID for use in sets/dicts.
        
        Returns:
            int: Hash value
        """
        return hash(self.id)
    
    def __str__(self) -> str:
        """
        Human-readable string representation.
        
        Returns:
            str: Format "[left|right]"
        """
        return f"[{self.left}|{self.right}]"
    
    def __repr__(self) -> str:
        """
        Unambiguous string representation for debugging.
        
        Returns:
            str: Format "Domino(left, right)"
        """
        return f"Domino({self.left}, {self.right})"
    
    @staticmethod
    def create_standard_set() -> Set['Domino']:
        """
        Create the standard double-six domino set (28 pieces).
        
        Generates all unique dominoes with pip values 0-6.
        Includes all doubles (0-0 through 6-6) and all combinations.
        
        Returns:
            Set[Domino]: Set of 28 unique dominoes
        
        Example:
            >>> dominoes = Domino.create_standard_set()
            >>> len(dominoes)
            28
            >>> Domino(3, 5) in dominoes
            True
        """
        dominoes = set()
        for left in range(7):  # 0 through 6
            for right in range(left, 7):  # Avoid duplicates like (2,4) and (4,2)
                dominoes.add(Domino(left, right))
        return dominoes


# Type alias for cleaner type hints
DominoSet = Set[Domino]
