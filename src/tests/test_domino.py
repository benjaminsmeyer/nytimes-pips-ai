"""
Unit tests for Domino class - TDD approach.
Tests written BEFORE implementation.
"""
import pytest
from src.core.domino import Domino


class TestDominoCreation:
    """Test domino instantiation and validation."""
    
    def test_create_valid_domino(self):
        """Should create domino with valid pip values 0-6."""
        domino = Domino(3, 5)
        assert domino.left == 3
        assert domino.right == 5
    
    def test_create_double_domino(self):
        """Should create double domino (same value on both sides)."""
        domino = Domino(6, 6)
        assert domino.left == 6
        assert domino.right == 6
        assert domino.is_double()
    
    def test_create_domino_with_zero(self):
        """Should allow zero as valid pip value."""
        domino = Domino(0, 4)
        assert domino.left == 0
        assert domino.right == 4
    
    def test_reject_negative_pip_value(self):
        """Should raise ValueError for negative pip values."""
        with pytest.raises(ValueError, match="Pip values must be between 0 and 6"):
            Domino(-1, 5)
    
    def test_reject_pip_value_above_six(self):
        """Should raise ValueError for pip values > 6."""
        with pytest.raises(ValueError, match="Pip values must be between 0 and 6"):
            Domino(3, 7)
    
    def test_domino_has_unique_id(self):
        """Each domino should have a unique identifier."""
        domino = Domino(2, 4)
        assert domino.id is not None
        assert isinstance(domino.id, str)
    
    def test_domino_id_is_normalized(self):
        """Domino ID should be normalized (e.g., 2-4 and 4-2 have same ID)."""
        domino1 = Domino(2, 4)
        domino2 = Domino(4, 2)
        assert domino1.id == domino2.id


class TestDominoEquality:
    """Test domino equality and hashing."""
    
    def test_dominoes_equal_same_order(self):
        """Dominoes with same values in same order should be equal."""
        domino1 = Domino(3, 5)
        domino2 = Domino(3, 5)
        assert domino1 == domino2
    
    def test_dominoes_equal_reversed_order(self):
        """Dominoes should be equal regardless of left/right order."""
        domino1 = Domino(2, 6)
        domino2 = Domino(6, 2)
        assert domino1 == domino2
    
    def test_dominoes_not_equal_different_values(self):
        """Dominoes with different values should not be equal."""
        domino1 = Domino(1, 3)
        domino2 = Domino(1, 4)
        assert domino1 != domino2
    
    def test_domino_hashable(self):
        """Dominoes should be hashable for use in sets."""
        domino1 = Domino(3, 5)
        domino2 = Domino(5, 3)
        domino_set = {domino1, domino2}
        assert len(domino_set) == 1  # Should be treated as same domino
    
    def test_double_domino_equality(self):
        """Double dominoes should equal themselves."""
        domino1 = Domino(4, 4)
        domino2 = Domino(4, 4)
        assert domino1 == domino2


class TestDominoProperties:
    """Test domino property methods."""
    
    def test_is_double_true(self):
        """Should return True for double dominoes."""
        assert Domino(0, 0).is_double()
        assert Domino(3, 3).is_double()
        assert Domino(6, 6).is_double()
    
    def test_is_double_false(self):
        """Should return False for non-double dominoes."""
        assert not Domino(1, 2).is_double()
        assert not Domino(0, 6).is_double()
    
    def test_get_pips_returns_both_values(self):
        """Should return tuple of both pip values."""
        domino = Domino(2, 5)
        pips = domino.get_pips()
        assert isinstance(pips, tuple)
        assert set(pips) == {2, 5}
    
    def test_contains_pip_value_true(self):
        """Should return True if domino contains specified pip value."""
        domino = Domino(3, 6)
        assert domino.contains_pip(3)
        assert domino.contains_pip(6)
    
    def test_contains_pip_value_false(self):
        """Should return False if domino doesn't contain pip value."""
        domino = Domino(2, 4)
        assert not domino.contains_pip(5)
        assert not domino.contains_pip(0)
    
    def test_total_pips_sum(self):
        """Should return sum of both pip values."""
        assert Domino(3, 5).total_pips() == 8
        assert Domino(0, 6).total_pips() == 6
        assert Domino(2, 2).total_pips() == 4


class TestDominoImmutability:
    """Test that Domino is immutable."""
    
    def test_cannot_modify_left_value(self):
        """Should not allow modification of left pip value."""
        domino = Domino(3, 5)
        with pytest.raises(AttributeError):
            domino.left = 4
    
    def test_cannot_modify_right_value(self):
        """Should not allow modification of right pip value."""
        domino = Domino(3, 5)
        with pytest.raises(AttributeError):
            domino.right = 2
    
    def test_cannot_modify_id(self):
        """Should not allow modification of domino ID."""
        domino = Domino(2, 4)
        with pytest.raises(AttributeError):
            domino.id = "new-id"


class TestDominoStringRepresentation:
    """Test domino string formatting."""
    
    def test_str_representation(self):
        """Should have readable string representation."""
        domino = Domino(3, 5)
        assert "3" in str(domino) and "5" in str(domino)
    
    def test_repr_representation(self):
        """Should have unambiguous repr representation."""
        domino = Domino(2, 6)
        repr_str = repr(domino)
        assert "Domino" in repr_str
        assert "2" in repr_str and "6" in repr_str


class TestDominoFactory:
    """Test creation of standard domino set."""
    
    def test_create_standard_set(self):
        """Should create all 28 dominoes in standard double-six set."""
        dominoes = Domino.create_standard_set()
        assert len(dominoes) == 28
        assert all(isinstance(d, Domino) for d in dominoes)
    
    def test_standard_set_has_all_doubles(self):
        """Standard set should include all 7 doubles (0-0 through 6-6)."""
        dominoes = Domino.create_standard_set()
        doubles = [d for d in dominoes if d.is_double()]
        assert len(doubles) == 7
        double_values = {d.left for d in doubles}
        assert double_values == {0, 1, 2, 3, 4, 5, 6}
    
    def test_standard_set_no_duplicates(self):
        """Standard set should have no duplicate dominoes."""
        dominoes = Domino.create_standard_set()
        domino_ids = [d.id for d in dominoes]
        assert len(domino_ids) == len(set(domino_ids))
    
    def test_standard_set_has_specific_dominoes(self):
        """Standard set should include specific expected dominoes."""
        dominoes = Domino.create_standard_set()
        domino_set = set(dominoes)
        
        # Check for a few specific dominoes
        assert Domino(0, 0) in domino_set
        assert Domino(6, 6) in domino_set
        assert Domino(3, 5) in domino_set
        assert Domino(2, 4) in domino_set  # Same as 4-2
