"""
Unit tests for Board class - TDD approach.
Tests domino placement, validation, and AI interface.
"""
import pytest
from src.core.board import Board
from src.core.domino import Domino
from src.core.region import SumRegion, EqualRegion


class TestBoardCreation:
    """Test board initialization."""
    
    def test_create_empty_board(self):
        """Should create board with specified dimensions."""
        board = Board(rows=4, cols=5)
        assert board.rows == 4
        assert board.cols == 5
    
    def test_board_starts_with_standard_dominoes(self):
        """Board should start with all 28 dominoes available."""
        board = Board(rows=3, cols=4)
        assert len(board.available_dominoes) == 28
    
    def test_board_with_custom_dominoes(self):
        """Should allow creating board with subset of dominoes."""
        dominoes = {Domino(0, 1), Domino(2, 3), Domino(4, 5)}
        board = Board(rows=2, cols=3, dominoes=dominoes)
        assert len(board.available_dominoes) == 3
    
    def test_board_with_regions(self):
        """Should initialize board with constraint regions."""
        regions = [
            SumRegion([(0, 0), (0, 1)], target=10),
            EqualRegion([(1, 0), (1, 1)])
        ]
        board = Board(rows=2, cols=2, regions=regions)
        assert len(board.regions) == 2
    
    def test_board_all_cells_empty_initially(self):
        """All cells should be empty at creation."""
        board = Board(rows=3, cols=3)
        for row in range(3):
            for col in range(3):
                assert board.is_cell_empty(row, col)


class TestDominoPlacement:
    """Test placing dominoes on the board."""
    
    def test_place_domino_horizontally(self):
        """Should place domino in horizontal orientation."""
        board = Board(rows=3, cols=3)
        domino = Domino(3, 5)
        
        result = board.place_domino(domino, (0, 0), (0, 1))
        assert result is True
        assert board.get_cell_value(0, 0) == 3
        assert board.get_cell_value(0, 1) == 5
    
    def test_place_domino_vertically(self):
        """Should place domino in vertical orientation."""
        board = Board(rows=3, cols=3)
        domino = Domino(2, 6)
        
        result = board.place_domino(domino, (0, 0), (1, 0))
        assert result is True
        assert board.get_cell_value(0, 0) == 2
        assert board.get_cell_value(1, 0) == 6
    
    def test_place_domino_removes_from_available(self):
        """Placing domino should remove it from available set."""
        board = Board(rows=2, cols=2)
        domino = Domino(1, 4)
        initial_count = len(board.available_dominoes)
        
        board.place_domino(domino, (0, 0), (0, 1))
        assert len(board.available_dominoes) == initial_count - 1
        assert domino not in board.available_dominoes
    
    def test_place_domino_reversed_orientation(self):
        """Should handle domino placement in either orientation."""
        board = Board(rows=2, cols=2)
        domino = Domino(3, 5)
        
        # Place with values swapped
        board.place_domino(domino, (0, 0), (0, 1))
        values = {board.get_cell_value(0, 0), board.get_cell_value(0, 1)}
        assert values == {3, 5}
    
    def test_cannot_place_domino_on_occupied_cell(self):
        """Should reject placement on occupied cells."""
        board = Board(rows=2, cols=2)
        domino1 = Domino(1, 2)
        domino2 = Domino(3, 4)
        
        board.place_domino(domino1, (0, 0), (0, 1))
        result = board.place_domino(domino2, (0, 0), (1, 0))  # (0,0) occupied
        
        assert result is False
    
    def test_cannot_place_domino_out_of_bounds(self):
        """Should reject placement outside board boundaries."""
        board = Board(rows=3, cols=3)
        domino = Domino(2, 4)
        
        result = board.place_domino(domino, (2, 2), (2, 3))  # Col 3 is OOB
        assert result is False
    
    def test_cannot_place_domino_non_adjacent_cells(self):
        """Should reject placement on non-adjacent cells."""
        board = Board(rows=3, cols=3)
        domino = Domino(1, 5)
        
        result = board.place_domino(domino, (0, 0), (0, 2))  # Not adjacent
        assert result is False
    
    def test_cannot_place_domino_diagonally(self):
        """Should reject diagonal placement."""
        board = Board(rows=3, cols=3)
        domino = Domino(3, 6)
        
        result = board.place_domino(domino, (0, 0), (1, 1))  # Diagonal
        assert result is False
    
    def test_cannot_place_already_used_domino(self):
        """Should reject placing same domino twice."""
        board = Board(rows=3, cols=3)
        domino = Domino(2, 5)
        
        board.place_domino(domino, (0, 0), (0, 1))
        result = board.place_domino(domino, (1, 0), (1, 1))
        
        assert result is False


class TestDominoRemoval:
    """Test removing dominoes from board."""
    
    def test_remove_domino_by_position(self):
        """Should remove domino and restore to available set."""
        board = Board(rows=2, cols=2)
        domino = Domino(1, 3)
        
        board.place_domino(domino, (0, 0), (0, 1))
        initial_count = len(board.available_dominoes)
        
        result = board.remove_domino((0, 0), (0, 1))
        assert result is True
        assert board.is_cell_empty(0, 0)
        assert board.is_cell_empty(0, 1)
        assert len(board.available_dominoes) == initial_count + 1
    
    def test_remove_domino_from_either_cell(self):
        """Should be able to remove domino by specifying either cell."""
        board = Board(rows=2, cols=2)
        domino = Domino(2, 4)
        
        board.place_domino(domino, (0, 0), (0, 1))
        
        # Remove using second cell position
        result = board.remove_domino((0, 1), (0, 0))
        assert result is True
        assert board.is_cell_empty(0, 0)
    
    def test_cannot_remove_from_empty_cell(self):
        """Should reject removal from empty cell."""
        board = Board(rows=2, cols=2)
        result = board.remove_domino((0, 0), (0, 1))
        assert result is False
    
    def test_cannot_remove_mismatched_domino(self):
        """Should reject removal if cells aren't from same domino."""
        board = Board(rows=3, cols=3)
        domino1 = Domino(1, 2)
        domino2 = Domino(3, 4)
        
        board.place_domino(domino1, (0, 0), (0, 1))
        board.place_domino(domino2, (1, 0), (1, 1))
        
        # Try to remove using cells from different dominoes
        result = board.remove_domino((0, 0), (1, 0))
        assert result is False


class TestConstraintValidation:
    """Test board-level constraint validation."""
    
    def test_validates_sum_constraint_satisfied(self):
        """Should validate when sum constraints are met."""
        regions = [SumRegion([(0, 0), (0, 1)], target=10)]
        board = Board(rows=2, cols=2, regions=regions)
        
        board.place_domino(Domino(4, 6), (0, 0), (0, 1))
        assert board.is_valid_state()
    
    def test_rejects_violated_sum_constraint(self):
        """Should detect violated sum constraints."""
        regions = [SumRegion([(0, 0), (0, 1)], target=10)]
        board = Board(rows=2, cols=2, regions=regions)
        
        board.place_domino(Domino(2, 3), (0, 0), (0, 1))  # Sum is 5, not 10
        assert not board.is_valid_state()
    
    def test_validates_equal_constraint_satisfied(self):
        """Should validate when equal constraints are met."""
        regions = [EqualRegion([(0, 0), (0, 1), (1, 0)])]
        board = Board(rows=2, cols=2, regions=regions)
        
        # Place dominoes to create 5, 5, 5
        board.place_domino(Domino(5, 5), (0, 0), (0, 1))
        board.place_domino(Domino(5, 1), (1, 0), (1, 1))
        assert board.is_valid_state()
    
    def test_validates_multiple_regions(self):
        """Should validate all regions simultaneously."""
        regions = [
            SumRegion([(0, 0), (0, 1)], target=8),
            EqualRegion([(1, 0), (1, 1)])
        ]
        board = Board(rows=2, cols=2, regions=regions)
        
        board.place_domino(Domino(2, 6), (0, 0), (0, 1))  # Sum = 8
        board.place_domino(Domino(4, 4), (1, 0), (1, 1))  # Equal = 4
        assert board.is_valid_state()
    
    def test_partial_state_not_complete(self):
        """Incomplete board should not be considered valid final state."""
        regions = [SumRegion([(0, 0), (0, 1)], target=10)]
        board = Board(rows=2, cols=2, regions=regions)
        
        # Only place one domino, leaving cells empty
        board.place_domino(Domino(4, 6), (0, 0), (0, 1))
        assert not board.is_complete()


class TestCrossRegionDominoes:
    """Test dominoes spanning multiple regions."""
    
    def test_domino_spanning_two_regions(self):
        """Should validate each half independently for different regions."""
        # Two adjacent sum regions
        regions = [
            SumRegion([(0, 0)], target=6, name="A"),
            SumRegion([(0, 1)], target=3, name="B")
        ]
        board = Board(rows=1, cols=2, regions=regions)
        
        board.place_domino(Domino(6, 3), (0, 0), (0, 1))
        assert board.is_valid_state()
    
    def test_domino_spanning_constraint_and_blank(self):
        """Should validate constrained half, ignore blank region."""
        regions = [SumRegion([(0, 0)], target=5)]
        board = Board(rows=1, cols=2, regions=regions)
        
        # (0,1) is in no region (blank area)
        board.place_domino(Domino(5, 2), (0, 0), (0, 1))
        assert board.is_valid_state()


class TestIsolatedCellDetection:
    """Test detection of isolated cells (critical optimization)."""
    
    def test_no_isolated_cells_in_valid_state(self):
        """Should not detect isolated cells in valid configuration."""
        board = Board(rows=2, cols=2)
        
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        # (1, 0) and (1, 1) still empty and adjacent
        
        assert not board.has_isolated_cells()


class TestBoardStateQueries:
    """Test board state inspection methods."""
    
    def test_get_valid_placements_returns_positions(self):
        """Should return list of valid placement positions."""
        board = Board(rows=2, cols=2)
        placements = board.get_valid_placements(Domino(1, 2))
        
        assert len(placements) > 0
        assert all(isinstance(p, tuple) for p in placements)
    
    def test_get_valid_placements_excludes_occupied(self):
        """Should not return placements on occupied cells."""
        board = Board(rows=2, cols=2)
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        
        placements = board.get_valid_placements(Domino(3, 4))
        
        # Should not include positions using (0,0) or (0,1)
        for pos1, pos2 in placements:
            assert (0, 0) not in [pos1, pos2]
            assert (0, 1) not in [pos1, pos2]
    
    def test_is_complete_all_cells_filled(self):
        """Board is complete when all cells are filled."""
        board = Board(rows=2, cols=2)
        
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        board.place_domino(Domino(3, 4), (1, 0), (1, 1))
        
        assert board.is_complete()
    
    def test_is_complete_false_with_empty_cells(self):
        """Board is not complete with empty cells."""
        board = Board(rows=2, cols=2)
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        
        assert not board.is_complete()
    
    def test_get_available_pip_counts_after_placement(self):
        """Pip counts should decrease after placement."""
        board = Board(rows=2, cols=2)
        initial_counts = board.get_available_pip_counts()
        
        board.place_domino(Domino(3, 5), (0, 0), (0, 1))
        
        new_counts = board.get_available_pip_counts()
        assert new_counts[3] == initial_counts[3] - 1
        assert new_counts[5] == initial_counts[5] - 1


class TestBoardCloning:
    """Test board state cloning for AI search."""
    
    def test_clone_creates_independent_copy(self):
        """Cloned board should be independent of original."""
        board = Board(rows=2, cols=2)
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        
        cloned = board.clone()
        
        # Modify clone
        cloned.place_domino(Domino(3, 4), (1, 0), (1, 1))
        
        # Original should be unchanged
        assert board.is_cell_empty(1, 0)
        assert not cloned.is_cell_empty(1, 0)
    
    def test_clone_preserves_regions(self):
        """Cloned board should have same regions."""
        regions = [SumRegion([(0, 0), (0, 1)], target=10)]
        board = Board(rows=2, cols=2, regions=regions)
        
        cloned = board.clone()
        
        assert len(cloned.regions) == len(board.regions)
    
    def test_clone_preserves_available_dominoes(self):
        """Cloned board should have same available dominoes."""
        board = Board(rows=2, cols=2)
        board.place_domino(Domino(1, 2), (0, 0), (0, 1))
        
        cloned = board.clone()
        
        assert len(cloned.available_dominoes) == len(board.available_dominoes)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_board_with_non_rectangular_shape(self):
        """Should support non-rectangular board shapes."""
        # Define valid cells (not all cells in rectangle are valid)
        valid_cells = {(0, 0), (0, 1), (1, 0), (2, 0)}
        board = Board(rows=3, cols=2, valid_cells=valid_cells)
        
        # Should reject placement on invalid cell
        result = board.place_domino(Domino(1, 2), (1, 1), (2, 1))
        assert result is False
    
    def test_empty_board_has_28_available_dominoes(self):
        """Fresh board should have full double-six set."""
        board = Board(rows=5, cols=6)
        assert len(board.available_dominoes) == 28
    
    def test_board_to_string_representation(self):
        """Board should have readable string representation."""
        board = Board(rows=2, cols=2)
        board.place_domino(Domino(3, 5), (0, 0), (0, 1))
        
        board_str = str(board)
        assert "3" in board_str and "5" in board_str
    
    def test_board_handles_double_domino_placement(self):
        """Should correctly place double dominoes."""
        board = Board(rows=2, cols=2)
        double = Domino(4, 4)
        
        board.place_domino(double, (0, 0), (0, 1))
        assert board.get_cell_value(0, 0) == 4
        assert board.get_cell_value(0, 1) == 4


class TestConstraintEarlyPruning:
    """Test early constraint violation detection (optimization)."""
    
    def test_detects_impossible_sum_early(self):
        """Should detect when partial sum cannot reach target."""
        regions = [SumRegion([(0, 0), (0, 1), (1, 0)], target=18)]
        board = Board(rows=2, cols=2, regions=regions)
        
        board.place_domino(Domino(6, 6), (0, 0), (0, 1))
        # Current sum: 12, need 6 more, possible
        
        # Check if can still satisfy
        can_satisfy = board.can_satisfy_constraints()
        assert can_satisfy  # Should still be satisfiable
    
    def test_detects_exceeded_sum_constraint(self):
        """Should detect when sum already exceeds target."""
        regions = [SumRegion([(0, 0), (0, 1)], target=8)]
        board = Board(rows=2, cols=2, regions=regions)
        
        board.place_domino(Domino(5, 6), (0, 0), (0, 1))  # Sum = 11 > 8
        
        assert not board.is_valid_state()
