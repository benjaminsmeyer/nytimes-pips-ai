"""
Region constraint classes for NYTimes Pips solver.
Implements Strategy pattern for five constraint types:
Sum, Equal, NotEqual, GreaterThan, LessThan.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class Region(ABC):
    """
    Abstract base class for constraint regions.
    
    A region is a collection of board cells with a validation constraint.
    Uses Strategy pattern - each constraint type implements validation logic.
    
    Attributes:
        cells (List[Tuple[int, int]]): List of (row, col) positions in region
        name (str): Optional identifier for the region
    """
    
    def __init__(self, cells: List[Tuple[int, int]], name: str = None):
        """
        Initialize a constraint region.
        
        Args:
            cells: List of (row, col) tuples defining the region
            name: Optional identifier (defaults to class name + count)
        """
        self.cells = cells
        self.name = name or f"{self.__class__.__name__}_{id(self)}"
    
    @abstractmethod
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate if current cell values satisfy the constraint.
        
        Args:
            cell_values: Dict mapping (row, col) -> pip_value
        
        Returns:
            bool: True if constraint satisfied, False otherwise
        """
        pass
    
    @abstractmethod
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int], 
                   available_pips: List[int]) -> bool:
        """
        Check if constraint can still be satisfied (look-ahead validation).
        
        Critical optimization: determines if partial solution can become valid.
        
        Args:
            partial_values: Currently filled cells in region
            available_pips: List of pip values from remaining dominoes
        
        Returns:
            bool: True if constraint could still be satisfied
        """
        pass
    
    def _is_complete(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Check if all cells in region are filled.
        
        Args:
            cell_values: Dict mapping (row, col) -> pip_value
        
        Returns:
            bool: True if all region cells have values
        """
        return all(cell in cell_values for cell in self.cells)
    
    def _get_region_values(self, cell_values: Dict[Tuple[int, int], int]) -> List[int]:
        """
        Extract pip values for cells in this region.
        
        Args:
            cell_values: Dict mapping (row, col) -> pip_value
        
        Returns:
            List[int]: Pip values for cells in region (only filled cells)
        """
        return [cell_values[cell] for cell in self.cells if cell in cell_values]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cells={len(self.cells)}, name={self.name})"


class SumRegion(Region):
    """
    Constraint: Sum of all pips in region must equal target value.
    
    Example: Region marked "12" with 2 cells must be [6|6]
    """
    
    def __init__(self, cells: List[Tuple[int, int]], target: int, name: str = None):
        """
        Initialize sum constraint region.
        
        Args:
            cells: List of (row, col) positions
            target: Required sum value
            name: Optional identifier
        """
        super().__init__(cells, name)
        self.target = target
    
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate that sum equals target.
        
        Returns False if:
        - Not all cells filled
        - Sum != target
        """
        if not self._is_complete(cell_values):
            return False
        
        values = self._get_region_values(cell_values)
        return sum(values) == self.target
    
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int],
                   available_pips: List[int]) -> bool:
        """
        Check if sum target is still achievable.
        
        Uses knapsack-style validation: can remaining pips fill gap?
        """
        values = self._get_region_values(partial_values)
        current_sum = sum(values)
        
        # If current sum already exceeds target, impossible
        if current_sum > self.target:
            return False
        
        remaining_cells = len(self.cells) - len(values)
        if remaining_cells == 0:
            return current_sum == self.target
        
        needed_sum = self.target - current_sum
        
        # Check if we have enough high values to reach target
        sorted_pips = sorted(available_pips, reverse=True)
        max_possible = sum(sorted_pips[:remaining_cells]) if len(sorted_pips) >= remaining_cells else sum(sorted_pips)
        
        # Check if we have enough low values (can't go below 0)
        min_possible = sum(sorted_pips[-remaining_cells:]) if len(sorted_pips) >= remaining_cells else 0
        
        return min_possible <= needed_sum <= max_possible
    
    def __repr__(self) -> str:
        return f"SumRegion(target={self.target}, cells={len(self.cells)})"


class EqualRegion(Region):
    """
    Constraint: All cells in region must have same pip value.
    
    Example: Region marked "=" with 4 cells could be all 3s
    """
    
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate that all cells have identical values.
        
        Returns False if:
        - Not all cells filled
        - Any cell has different value
        """
        if not self._is_complete(cell_values):
            return False
        
        values = self._get_region_values(cell_values)
        return len(set(values)) == 1  # All values the same
    
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int],
                   available_pips: List[int]) -> bool:
        """
        Check if enough matching pips remain.
        
        If partially filled with value V, need enough spare V pips.
        """
        values = self._get_region_values(partial_values)
        
        if len(values) == 0:
            # No cells filled yet - always satisfiable
            return True
        
        # Check if existing values all match
        if len(set(values)) > 1:
            return False  # Already has conflicting values
        
        required_value = values[0]
        needed_count = len(self.cells) - len(values)
        
        # Count how many of required_value are in available pips
        available_count = sum(1 for pip in available_pips if pip == required_value)
        
        return available_count >= needed_count
    
    def __repr__(self) -> str:
        return f"EqualRegion(cells={len(self.cells)})"


class NotEqualRegion(Region):
    """
    Constraint: All cells in region must have different pip values.
    
    Example: Region marked "≠" with 3 cells could be [2], [5], [6]
    Maximum size: 7 cells (values 0-6)
    """
    
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate that all cells have unique values.
        
        Returns False if:
        - Not all cells filled
        - Any duplicate values exist
        """
        if not self._is_complete(cell_values):
            return False
        
        values = self._get_region_values(cell_values)
        return len(set(values)) == len(values)  # All unique
    
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int],
                   available_pips: List[int]) -> bool:
        """
        Check if enough unique values remain.
        
        Need distinct values different from already-used values.
        """
        values = self._get_region_values(partial_values)
        
        # Check if current values are already unique
        if len(set(values)) != len(values):
            return False  # Already has duplicates
        
        used_values = set(values)
        needed_count = len(self.cells) - len(values)
        
        # Find unique values available that aren't already used
        available_unique = set(available_pips) - used_values
        
        return len(available_unique) >= needed_count
    
    def __repr__(self) -> str:
        return f"NotEqualRegion(cells={len(self.cells)})"


class GreaterThanRegion(Region):
    """
    Constraint: Sum of all pips must exceed threshold.
    
    Example: Region marked ">5" with 2 cells needs sum >= 6
    """
    
    def __init__(self, cells: List[Tuple[int, int]], threshold: int, name: str = None):
        """
        Initialize greater-than constraint region.
        
        Args:
            cells: List of (row, col) positions
            threshold: Sum must exceed this value
            name: Optional identifier
        """
        super().__init__(cells, name)
        self.threshold = threshold
    
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate that sum > threshold.
        
        Returns False if:
        - Not all cells filled
        - Sum <= threshold
        """
        if not self._is_complete(cell_values):
            return False
        
        values = self._get_region_values(cell_values)
        return sum(values) > self.threshold
    
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int],
                   available_pips: List[int]) -> bool:
        """
        Check if sum can exceed threshold.
        
        Need to verify max possible sum > threshold.
        """
        values = self._get_region_values(partial_values)
        current_sum = sum(values)
        remaining_cells = len(self.cells) - len(values)
        
        if remaining_cells == 0:
            return current_sum > self.threshold
        
        # Calculate maximum possible sum with remaining cells
        sorted_pips = sorted(available_pips, reverse=True)
        max_additional = sum(sorted_pips[:remaining_cells]) if len(sorted_pips) >= remaining_cells else sum(sorted_pips)
        
        return (current_sum + max_additional) > self.threshold
    
    def __repr__(self) -> str:
        return f"GreaterThanRegion(threshold={self.threshold}, cells={len(self.cells)})"


class LessThanRegion(Region):
    """
    Constraint: Sum of all pips must be below threshold.
    
    Example: Region marked "<5" with 2 cells needs sum <= 4
    """
    
    def __init__(self, cells: List[Tuple[int, int]], threshold: int, name: str = None):
        """
        Initialize less-than constraint region.
        
        Args:
            cells: List of (row, col) positions
            threshold: Sum must be below this value
            name: Optional identifier
        """
        super().__init__(cells, name)
        self.threshold = threshold
    
    def validate(self, cell_values: Dict[Tuple[int, int], int]) -> bool:
        """
        Validate that sum < threshold.
        
        Returns False if:
        - Not all cells filled
        - Sum >= threshold
        """
        if not self._is_complete(cell_values):
            return False
        
        values = self._get_region_values(cell_values)
        return sum(values) < self.threshold
    
    def can_satisfy(self, partial_values: Dict[Tuple[int, int], int],
                   available_pips: List[int]) -> bool:
        """
        Check if sum can stay below threshold.
        
        Verify current sum not already over and minimum possible < threshold.
        """
        values = self._get_region_values(partial_values)
        current_sum = sum(values)
        
        # If already exceeds threshold, impossible
        if current_sum >= self.threshold:
            return False
        
        remaining_cells = len(self.cells) - len(values)
        
        if remaining_cells == 0:
            return current_sum < self.threshold
        
        # Calculate minimum possible sum with remaining cells
        sorted_pips = sorted(available_pips)
        min_additional = sum(sorted_pips[:remaining_cells]) if len(sorted_pips) >= remaining_cells else sum(sorted_pips)
        
        return (current_sum + min_additional) < self.threshold
    
    def __repr__(self) -> str:
        return f"LessThanRegion(threshold={self.threshold}, cells={len(self.cells)})"
