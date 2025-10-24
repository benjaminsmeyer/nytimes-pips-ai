"""
Unit tests for Region constraint classes - TDD approach.
Tests all five constraint types with edge cases.
"""
import pytest
from src.core.region import (
    SumRegion, EqualRegion, NotEqualRegion,
    GreaterThanRegion, LessThanRegion
)


class TestRegionBase:
    """Test base Region abstract functionality."""
    
    def test_region_has_cells(self):
        """Region should track its cell positions."""
        cells = [(0, 0), (0, 1), (1, 0)]
        region = SumRegion(cells, target=10)
        assert set(region.cells) == set(cells)
    
    def test_region_has_name(self):
        """Region should have an identifying name."""
        region = SumRegion([(0, 0)], target=5, name="A")
        assert region.name == "A"
    
    def test_region_default_name(self):
        """Region should have default name if not provided."""
        region = EqualRegion([(0, 0)])
        assert region.name is not None


class TestSumRegion:
    """Test SumRegion constraint validation."""
    
    def test_sum_region_creation(self):
        """Should create sum region with target value."""
        region = SumRegion([(0, 0), (0, 1)], target=12)
        assert region.target == 12
    
    def test_sum_validates_correct_sum(self):
        """Should validate when sum equals target."""
        region = SumRegion([(0, 0), (0, 1), (1, 0)], target=15)
        cell_values = {(0, 0): 6, (0, 1): 6, (1, 0): 3}
        assert region.validate(cell_values)
    
    def test_sum_rejects_incorrect_sum(self):
        """Should reject when sum doesn't equal target."""
        region = SumRegion([(0, 0), (0, 1)], target=10)
        cell_values = {(0, 0): 6, (0, 1): 3}  # Sum is 9, not 10
        assert not region.validate(cell_values)
    
    def test_sum_rejects_exceeding_sum(self):
        """Should reject when sum exceeds target."""
        region = SumRegion([(0, 0), (0, 1)], target=8)
        cell_values = {(0, 0): 6, (0, 1): 5}  # Sum is 11 > 8
        assert not region.validate(cell_values)
    
    def test_sum_validates_with_zeros(self):
        """Should correctly handle zeros in sum."""
        region = SumRegion([(0, 0), (0, 1), (1, 0)], target=6)
        cell_values = {(0, 0): 0, (0, 1): 0, (1, 0): 6}
        assert region.validate(cell_values)
    
    def test_sum_rejects_incomplete_region(self):
        """Should reject validation when not all cells are filled."""
        region = SumRegion([(0, 0), (0, 1), (1, 0)], target=10)
        cell_values = {(0, 0): 5, (0, 1): 3}  # Missing (1,0)
        assert not region.validate(cell_values)
    
    def test_sum_can_satisfy_with_remaining_dominoes(self):
        """Should check if partial sum can still reach target."""
        region = SumRegion([(0, 0), (0, 1), (1, 0), (1, 1)], target=24)
        partial_values = {(0, 0): 6, (0, 1): 6}
        available_pips = [6, 6, 5, 5, 4, 4]  # Remaining domino halves
        
        # Need 24 - 12 = 12 more from 2 cells, possible with 6+6
        assert region.can_satisfy(partial_values, available_pips)
    
    def test_sum_cannot_satisfy_impossible_target(self):
        """Should detect impossible sum targets early."""
        region = SumRegion([(0, 0), (0, 1)], target=15)
        partial_values = {(0, 0): 6}
        available_pips = [0, 1, 2, 3, 4, 5]  # Max remaining is 5
        
        # Need 15 - 6 = 9, but max available is 5
        assert not region.can_satisfy(partial_values, available_pips)


class TestEqualRegion:
    """Test EqualRegion constraint validation."""
    
    def test_equal_region_creation(self):
        """Should create equal region."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0)])
        assert len(region.cells) == 3
    
    def test_equal_validates_all_same_value(self):
        """Should validate when all cells have same pip value."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0), (1, 1)])
        cell_values = {(0, 0): 3, (0, 1): 3, (1, 0): 3, (1, 1): 3}
        assert region.validate(cell_values)
    
    def test_equal_rejects_different_values(self):
        """Should reject when cells have different values."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 4, (0, 1): 4, (1, 0): 5}
        assert not region.validate(cell_values)
    
    def test_equal_validates_all_zeros(self):
        """Should validate when all cells are zero."""
        region = EqualRegion([(0, 0), (0, 1)])
        cell_values = {(0, 0): 0, (0, 1): 0}
        assert region.validate(cell_values)
    
    def test_equal_rejects_incomplete_region(self):
        """Should reject when not all cells filled."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 2, (0, 1): 2}  # Missing (1,0)
        assert not region.validate(cell_values)
    
    def test_equal_can_satisfy_with_available_pips(self):
        """Should check if enough matching pips remain."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0), (1, 1)])
        partial_values = {(0, 0): 6, (0, 1): 6}
        available_pips = [6, 6, 5, 4]  # Need 2 more 6s, we have them
        
        assert region.can_satisfy(partial_values, available_pips)
    
    def test_equal_cannot_satisfy_insufficient_pips(self):
        """Should detect when not enough matching pips remain."""
        region = EqualRegion([(0, 0), (0, 1), (1, 0)])
        partial_values = {(0, 0): 5}
        available_pips = [5, 3, 3, 2, 1]  # Need 2 more 5s, only have 1
        
        assert not region.can_satisfy(partial_values, available_pips)
    
    def test_equal_single_cell_always_valid(self):
        """Single cell equals region should always validate."""
        region = EqualRegion([(0, 0)])
        cell_values = {(0, 0): 4}
        assert region.validate(cell_values)


class TestNotEqualRegion:
    """Test NotEqualRegion constraint validation."""
    
    def test_not_equal_region_creation(self):
        """Should create not-equal region."""
        region = NotEqualRegion([(0, 0), (0, 1)])
        assert len(region.cells) == 2
    
    def test_not_equal_validates_all_different(self):
        """Should validate when all cells have different values."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 2, (0, 1): 5, (1, 0): 6}
        assert region.validate(cell_values)
    
    def test_not_equal_rejects_duplicate_values(self):
        """Should reject when any two cells have same value."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 3, (0, 1): 3, (1, 0): 5}
        assert not region.validate(cell_values)
    
    def test_not_equal_validates_with_zero(self):
        """Should handle zero as valid distinct value."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 0, (0, 1): 3, (1, 0): 6}
        assert region.validate(cell_values)
    
    def test_not_equal_max_size_seven(self):
        """Not-equal region can have at most 7 cells (0-6)."""
        cells = [(i, 0) for i in range(7)]
        region = NotEqualRegion(cells)
        cell_values = {(i, 0): i for i in range(7)}
        assert region.validate(cell_values)
    
    def test_not_equal_rejects_incomplete_region(self):
        """Should reject when not all cells filled."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        cell_values = {(0, 0): 1, (0, 1): 2}  # Missing (1,0)
        assert not region.validate(cell_values)
    
    def test_not_equal_can_satisfy_with_available_unique_values(self):
        """Should check if enough unique values remain."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        partial_values = {(0, 0): 2}
        available_pips = [3, 4, 5, 6]  # Need 2 more unique, we have plenty
        
        assert region.can_satisfy(partial_values, available_pips)
    
    def test_not_equal_cannot_satisfy_insufficient_unique_values(self):
        """Should detect when not enough unique values remain."""
        region = NotEqualRegion([(0, 0), (0, 1), (1, 0)])
        partial_values = {(0, 0): 2, (0, 1): 3}
        available_pips = [3, 3, 3]  # Need 1 more unique, but only 3s left
        
        assert not region.can_satisfy(partial_values, available_pips)


class TestGreaterThanRegion:
    """Test GreaterThanRegion constraint validation."""
    
    def test_greater_than_region_creation(self):
        """Should create greater-than region with threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1)], threshold=5)
        assert region.threshold == 5
    
    def test_greater_than_validates_exceeding_threshold(self):
        """Should validate when sum exceeds threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1), (1, 0)], threshold=10)
        cell_values = {(0, 0): 6, (0, 1): 5, (1, 0): 4}  # Sum is 15 > 10
        assert region.validate(cell_values)
    
    def test_greater_than_validates_exactly_one_above(self):
        """Should validate when sum is exactly threshold + 1."""
        region = GreaterThanRegion([(0, 0), (0, 1)], threshold=7)
        cell_values = {(0, 0): 5, (0, 1): 3}  # Sum is 8 = 7 + 1
        assert region.validate(cell_values)
    
    def test_greater_than_rejects_equal_to_threshold(self):
        """Should reject when sum equals threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1)], threshold=10)
        cell_values = {(0, 0): 4, (0, 1): 6}  # Sum is 10 = threshold
        assert not region.validate(cell_values)
    
    def test_greater_than_rejects_below_threshold(self):
        """Should reject when sum is below threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1)], threshold=8)
        cell_values = {(0, 0): 3, (0, 1): 2}  # Sum is 5 < 8
        assert not region.validate(cell_values)
    
    def test_greater_than_can_satisfy_with_high_values(self):
        """Should check if remaining pips can exceed threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1), (1, 0)], threshold=15)
        partial_values = {(0, 0): 6}
        available_pips = [6, 6, 5, 4]  # Can get 6+6=12, total 18 > 15
        
        assert region.can_satisfy(partial_values, available_pips)
    
    def test_greater_than_cannot_satisfy_low_maximum(self):
        """Should detect when max possible sum won't exceed threshold."""
        region = GreaterThanRegion([(0, 0), (0, 1)], threshold=10)
        partial_values = {(0, 0): 3}
        available_pips = [0, 1, 2, 3]  # Max is 3+3=6, won't exceed 10
        
        assert not region.can_satisfy(partial_values, available_pips)


class TestLessThanRegion:
    """Test LessThanRegion constraint validation."""
    
    def test_less_than_region_creation(self):
        """Should create less-than region with threshold."""
        region = LessThanRegion([(0, 0), (0, 1)], threshold=5)
        assert region.threshold == 5
    
    def test_less_than_validates_below_threshold(self):
        """Should validate when sum is below threshold."""
        region = LessThanRegion([(0, 0), (0, 1), (1, 0)], threshold=10)
        cell_values = {(0, 0): 2, (0, 1): 3, (1, 0): 1}  # Sum is 6 < 10
        assert region.validate(cell_values)
    
    def test_less_than_validates_exactly_one_below(self):
        """Should validate when sum is exactly threshold - 1."""
        region = LessThanRegion([(0, 0), (0, 1)], threshold=8)
        cell_values = {(0, 0): 4, (0, 1): 3}  # Sum is 7 = 8 - 1
        assert region.validate(cell_values)
    
    def test_less_than_rejects_equal_to_threshold(self):
        """Should reject when sum equals threshold."""
        region = LessThanRegion([(0, 0), (0, 1)], threshold=10)
        cell_values = {(0, 0): 4, (0, 1): 6}  # Sum is 10 = threshold
        assert not region.validate(cell_values)
    
    def test_less_than_rejects_above_threshold(self):
        """Should reject when sum exceeds threshold."""
        region = LessThanRegion([(0, 0), (0, 1)], threshold=5)
        cell_values = {(0, 0): 3, (0, 1): 4}  # Sum is 7 > 5
        assert not region.validate(cell_values)
    
    def test_less_than_tight_constraint_all_zeros(self):
        """Threshold < 1 requires all zeros."""
        region = LessThanRegion([(0, 0), (0, 1)], threshold=1)
        cell_values = {(0, 0): 0, (0, 1): 0}
        assert region.validate(cell_values)
    
    def test_less_than_can_satisfy_with_low_values(self):
        """Should check if sum can stay below threshold."""
        region = LessThanRegion([(0, 0), (0, 1), (1, 0)], threshold=5)
        partial_values = {(0, 0): 1}
        available_pips = [0, 1, 2, 3]  # Can stay below 5
        
        assert region.can_satisfy(partial_values, available_pips)
    
    def test_less_than_cannot_satisfy_current_already_exceeds(self):
        """Should detect when current sum already violates constraint."""
        region = LessThanRegion([(0, 0), (0, 1), (1, 0)], threshold=8)
        partial_values = {(0, 0): 6, (0, 1): 5}  # Already 11 > 8
        available_pips = [0, 1, 2]
        
        assert not region.can_satisfy(partial_values, available_pips)


class TestRegionEdgeCases:
    """Test edge cases across all region types."""
    
    def test_region_with_single_cell(self):
        """All region types should handle single-cell regions."""
        cells = [(0, 0)]
        
        # Sum region with single cell
        sum_region = SumRegion(cells, target=6)
        assert sum_region.validate({(0, 0): 6})
        
        # Equal region with single cell (always valid)
        equal_region = EqualRegion(cells)
        assert equal_region.validate({(0, 0): 3})
        
        # Not-equal with single cell (always valid)
        not_equal_region = NotEqualRegion(cells)
        assert not_equal_region.validate({(0, 0): 5})
    
    def test_region_ignores_cells_outside_region(self):
        """Validation should only consider cells within the region."""
        region = SumRegion([(0, 0), (0, 1)], target=10)
        cell_values = {
            (0, 0): 4,
            (0, 1): 6,
            (1, 0): 9,  # Outside region, should be ignored
            (1, 1): 9   # Outside region, should be ignored
        }
        assert region.validate(cell_values)
    
    def test_empty_cell_values_dict(self):
        """Should handle empty cell values gracefully."""
        region = SumRegion([(0, 0), (0, 1)], target=10)
        assert not region.validate({})  # No cells filled
