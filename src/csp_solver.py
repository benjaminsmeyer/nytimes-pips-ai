"""
PRODUCTION CSP SOLVER for NYTimes Pips Puzzle
=============================================

A constraint satisfaction problem (CSP) solver using backtracking search
with constraint propagation, forward checking, and heuristics.

Key Features:
- Constraint propagation to identify forced moves
- MRV (Minimum Remaining Values) heuristic for variable ordering
- Forward checking to detect dead-ends early
- Efficient state validation with multiple pruning strategies
- Support for all constraint types (Sum, Equal, NotEqual, GreaterThan, LessThan)


"""

from typing import Optional, Dict, Tuple, List, Set
import time
from collections import Counter
from src.core.board import Board
from src.core.domino import Domino


class CSPSolver:
    """
    CSP solver for NYTimes Pips puzzles.

    Uses multiple optimization strategies:
    1. Constraint propagation - deduce cell values from constraints
    2. Forward checking - eliminate impossible values early
    3. MRV heuristic - choose variables with fewest legal values
    4. Forced move detection - apply moves with only one possibility
    5. State validation - comprehensive checking to prune invalid branches
    """

    def __init__(self, timeout: float = 120.0):
        """
        Initialize the solver.

        Args:
            timeout: Maximum time in seconds for solving (default: 120)
        """
        self.timeout = timeout
        self.start_time = None
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'constraint_checks': 0,
            'forced_moves': 0,
            'time_elapsed': 0.0,
            'solution_found': False,
            'max_depth': 0
        }

    def solve(self, board: Board) -> Tuple[Optional[Board], Dict]:
        """
        Solve the puzzle using CSP with backtracking.

        Args:
            board: Initial board state

        Returns:
            Tuple of (solution_board, statistics_dict)
            solution_board is None if no solution found
        """
        self.start_time = time.time()
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'constraint_checks': 0,
            'forced_moves': 0,
            'time_elapsed': 0.0,
            'solution_found': False,
            'max_depth': 0
        }

        # Start search with a clone of the board
        solution = self._backtrack(board.clone(), depth=0)

        self.stats['time_elapsed'] = time.time() - self.start_time
        self.stats['solution_found'] = solution is not None

        return solution, self.stats

    def _backtrack(self, board: Board, depth: int = 0) -> Optional[Board]:
        """
        Main backtracking search with constraint propagation.

        Args:
            board: Current board state
            depth: Current search depth

        Returns:
            Solution board or None if no solution exists
        """
        # Check timeout
        if time.time() - self.start_time > self.timeout:
            return None

        self.stats['nodes_explored'] += 1
        self.stats['max_depth'] = max(self.stats['max_depth'], depth)

        # Base case: puzzle is complete
        if board.is_complete():
            if board.is_valid_state():
                return board
            return None

        # Validate current state
        self.stats['constraint_checks'] += 1
        if not self._is_state_valid(board):
            self.stats['backtracks'] += 1
            return None

        # Apply constraint propagation to find forced moves
        forced_moves = self._find_forced_moves(board)
        if forced_moves:
            # Apply all forced moves at once
            new_board = board.clone()
            for domino, pos1, pos2 in forced_moves:
                if not self._place_with_orientation(new_board, domino, pos1, pos2):
                    self.stats['backtracks'] += 1
                    return None
                self.stats['forced_moves'] += 1

            # Continue with the updated board
            return self._backtrack(new_board, depth + 1)

        # Select next move using MRV heuristic
        next_move = self._select_next_move(board)
        if not next_move:
            self.stats['backtracks'] += 1
            return None

        domino, placements = next_move

        # Try each placement in order
        for pos1, pos2 in placements:
            new_board = board.clone()

            if self._place_with_orientation(new_board, domino, pos1, pos2):
                # Recursively solve
                result = self._backtrack(new_board, depth + 1)
                if result is not None:
                    return result

        # No solution found in this branch
        self.stats['backtracks'] += 1
        return None

    def _get_cell_constraints(self, board: Board) -> Dict[Tuple[int, int], Set[int]]:
        """
        Determine possible values for each empty cell based on constraints.

        Key optimizations:
        - Single-cell sum regions fix exact values
        - Equal regions propagate known values
        - Consider available domino pip values

        Args:
            board: Current board state

        Returns:
            Dictionary mapping cell positions to sets of possible values
        """
        constraints = {}

        # Initialize with all possible values for empty cells
        for cell in board._valid_cells:
            if board.is_cell_empty(*cell):
                constraints[cell] = set(range(7))

        # Apply region constraints
        for region in board.regions:
            # Single-cell sum regions determine exact value
            if hasattr(region, 'target') and len(region.cells) == 1:
                cell = region.cells[0]
                if cell in constraints:
                    constraints[cell] = {region.target}

            # Equal regions - propagate known values
            elif region.__class__.__name__ == 'EqualRegion':
                filled_values = []
                empty_cells = []

                for cell in region.cells:
                    if not board.is_cell_empty(*cell):
                        filled_values.append(board.get_cell_value(*cell))
                    elif cell in constraints:
                        empty_cells.append(cell)

                # If some cells are filled, others must match
                if filled_values and empty_cells:
                    required_value = filled_values[0]
                    # Verify all filled values are the same
                    if all(v == required_value for v in filled_values):
                        for cell in empty_cells:
                            constraints[cell] = {required_value}

            # NotEqual regions - remove used values
            elif region.__class__.__name__ == 'NotEqualRegion':
                used_values = set()
                empty_cells = []

                for cell in region.cells:
                    if not board.is_cell_empty(*cell):
                        used_values.add(board.get_cell_value(*cell))
                    elif cell in constraints:
                        empty_cells.append(cell)

                # Remove used values from empty cells
                for cell in empty_cells:
                    constraints[cell] -= used_values

        # Further constrain based on available dominoes
        available_pips = Counter()
        for domino in board.available_dominoes:
            available_pips[domino.left] += 1
            available_pips[domino.right] += 1

        # Remove impossible values (not available in any domino)
        for cell in constraints:
            constraints[cell] &= set(available_pips.keys())

        return constraints

    def _find_forced_moves(self, board: Board) -> List[Tuple[Domino, Tuple[int, int], Tuple[int, int]]]:
        """
        Find placements that are forced by constraints.

        A move is forced if:
        1. A cell has only one possible value and only one domino can provide it
        2. A domino has only one valid placement

        Args:
            board: Current board state

        Returns:
            List of (domino, pos1, pos2) tuples for forced moves
        """
        forced = []
        constraints = self._get_cell_constraints(board)

        # Check for cells with unique value requirements
        for cell, possible_values in constraints.items():
            if len(possible_values) != 1:
                continue

            required_value = next(iter(possible_values))
            row, col = cell

            # Find dominoes containing this value
            matching_dominoes = [
                d for d in board.available_dominoes
                if d.contains_pip(required_value)
            ]

            if len(matching_dominoes) == 1:
                domino = matching_dominoes[0]

                # Find valid placements for this domino at this cell
                valid_placements = []
                other_value = domino.right if domino.left == required_value else domino.left

                # Check adjacent cells
                adjacent = [
                    (row - 1, col), (row + 1, col),  # vertical
                    (row, col - 1), (row, col + 1)  # horizontal
                ]

                for adj in adjacent:
                    if adj in board._valid_cells and board.is_cell_empty(*adj):
                        adj_constraints = constraints.get(adj, set(range(7)))
                        if other_value in adj_constraints:
                            valid_placements.append((cell, adj))

                if len(valid_placements) == 1:
                    # Normalize placement (sort positions)
                    pos1, pos2 = valid_placements[0]
                    if pos1 > pos2:
                        pos1, pos2 = pos2, pos1

                    # Check if not already added
                    move = (domino, pos1, pos2)
                    if move not in forced:
                        forced.append(move)

        return forced

    def _select_next_move(self, board: Board) -> Optional[Tuple[Domino, List[Tuple[Tuple[int, int], Tuple[int, int]]]]]:
        """
        Select next domino and placements using MRV heuristic.

        Returns the domino with the minimum number of valid placements,
        along with its list of valid placements.

        Args:
            board: Current board state

        Returns:
            Tuple of (domino, placements_list) or None if no moves available
        """
        if not board.available_dominoes:
            return None

        constraints = self._get_cell_constraints(board)
        best_domino = None
        best_placements = None
        min_placements = float('inf')

        for domino in board.available_dominoes:
            valid_placements = self._get_valid_placements(board, domino, constraints)

            if valid_placements and len(valid_placements) < min_placements:
                min_placements = len(valid_placements)
                best_domino = domino
                best_placements = valid_placements

                # Early termination if only one placement
                if min_placements == 1:
                    break

        if best_domino:
            return (best_domino, best_placements)
        return None

    def _get_valid_placements(
            self,
            board: Board,
            domino: Domino,
            constraints: Dict[Tuple[int, int], Set[int]]
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Get all valid placements for a domino considering constraints.

        Args:
            board: Current board state
            domino: Domino to place
            constraints: Cell value constraints

        Returns:
            List of (pos1, pos2) placement tuples
        """
        placements = []
        seen = set()

        for cell in board._valid_cells:
            if not board.is_cell_empty(*cell):
                continue

            row, col = cell
            cell_constraints = constraints.get(cell, set(range(7)))

            # Try horizontal placement (to the right)
            right = (row, col + 1)
            if right in board._valid_cells and board.is_cell_empty(*right):
                right_constraints = constraints.get(right, set(range(7)))

                # Check both orientations
                if ((domino.left in cell_constraints and domino.right in right_constraints) or
                        (domino.right in cell_constraints and domino.left in right_constraints)):

                    # Normalize placement
                    placement = tuple(sorted([cell, right]))
                    if placement not in seen:
                        seen.add(placement)
                        placements.append(placement)

            # Try vertical placement (downward)
            down = (row + 1, col)
            if down in board._valid_cells and board.is_cell_empty(*down):
                down_constraints = constraints.get(down, set(range(7)))

                # Check both orientations
                if ((domino.left in cell_constraints and domino.right in down_constraints) or
                        (domino.right in cell_constraints and domino.left in down_constraints)):

                    # Normalize placement
                    placement = tuple(sorted([cell, down]))
                    if placement not in seen:
                        seen.add(placement)
                        placements.append(placement)

        return placements

    def _place_with_orientation(
            self,
            board: Board,
            domino: Domino,
            pos1: Tuple[int, int],
            pos2: Tuple[int, int]
    ) -> bool:
        """
        Place domino with correct orientation based on constraints.

        Args:
            board: Board to modify
            domino: Domino to place
            pos1: First position
            pos2: Second position

        Returns:
            True if placement successful
        """
        constraints = self._get_cell_constraints(board)
        pos1_possible = constraints.get(pos1, set(range(7)))
        pos2_possible = constraints.get(pos2, set(range(7)))

        # Try standard orientation
        if domino.left in pos1_possible and domino.right in pos2_possible:
            return board.place_domino(domino, pos1, pos2)

        # Try flipped orientation
        elif domino.right in pos1_possible and domino.left in pos2_possible:
            flipped = Domino(domino.right, domino.left)
            return board.place_domino(flipped, pos1, pos2)

        return False

    def _is_state_valid(self, board: Board) -> bool:
        """
        Comprehensive state validation with multiple checks.

        Checks:
        1. Basic constraint satisfaction
        2. No isolated cells
        3. Region-specific validation
        4. Resource availability

        Args:
            board: Board state to validate

        Returns:
            True if state is valid and can lead to solution
        """
        # Quick checks first
        if not board.can_satisfy_constraints():
            return False

        if board.has_isolated_cells():
            return False

        # Detailed region validation
        cell_values = {}
        for pos, (value, _) in board._grid.items():
            if value != -1:
                cell_values[pos] = value

        # Get available resources
        available_pips = []
        for d in board.available_dominoes:
            available_pips.extend([d.left, d.right])

        pip_counts = Counter(available_pips)

        for region in board.regions:
            region_values = [cell_values[c] for c in region.cells if c in cell_values]
            empty_count = len(region.cells) - len(region_values)

            if not self._validate_region(region, region_values, empty_count, pip_counts):
                return False

        return True

    def _validate_region(
            self,
            region,
            filled_values: List[int],
            empty_count: int,
            pip_counts: Counter
    ) -> bool:
        """
        Validate a specific region based on its type.

        Args:
            region: Region to validate
            filled_values: Values already in the region
            empty_count: Number of empty cells
            pip_counts: Available pip value counts

        Returns:
            True if region constraints can be satisfied
        """
        # Sum regions
        if hasattr(region, 'target'):
            if len(region.cells) == 1 and filled_values:
                # Single cell must equal target
                return filled_values[0] == region.target

            if empty_count == 0:
                # Complete region
                return sum(filled_values) == region.target

            # Partial region - check achievability
            current_sum = sum(filled_values) if filled_values else 0
            needed = region.target - current_sum

            # Check if achievable with available pips
            if empty_count > 0:
                available = list(pip_counts.elements())
                if len(available) < empty_count:
                    return False

                sorted_pips = sorted(available)
                min_possible = sum(sorted_pips[:empty_count])
                max_possible = sum(sorted_pips[-empty_count:])

                if needed < min_possible or needed > max_possible:
                    return False

        # Equal regions
        elif region.__class__.__name__ == 'EqualRegion':
            if filled_values and len(set(filled_values)) > 1:
                return False

            if filled_values and empty_count > 0:
                required_value = filled_values[0]
                if pip_counts[required_value] < empty_count:
                    return False

        # NotEqual regions
        elif region.__class__.__name__ == 'NotEqualRegion':
            if filled_values and len(set(filled_values)) != len(filled_values):
                return False

            if empty_count > 0:
                used_values = set(filled_values)
                available_unique = len(set(pip_counts.keys()) - used_values)
                if available_unique < empty_count:
                    return False

        # GreaterThan regions
        elif hasattr(region, 'threshold'):
            region_name = region.__class__.__name__
            current_sum = sum(filled_values) if filled_values else 0

            if region_name == 'GreaterThanRegion':
                if empty_count == 0:
                    return current_sum > region.threshold

                # Check maximum achievable
                available = list(pip_counts.elements())
                if available:
                    max_additional = sum(sorted(available)[-empty_count:]) if len(available) >= empty_count else sum(
                        available)
                    return (current_sum + max_additional) > region.threshold

            elif region_name == 'LessThanRegion':
                if current_sum >= region.threshold:
                    return False

                if empty_count == 0:
                    return current_sum < region.threshold

                # Check minimum achievable
                available = list(pip_counts.elements())
                if available:
                    min_additional = sum(sorted(available)[:empty_count]) if len(available) >= empty_count else sum(
                        available)
                    return (current_sum + min_additional) < region.threshold

        return True


def solve_with_csp(board: Board, timeout: float = 120.0) -> Tuple[Optional[Board], Dict]:
    """
    Convenience function for backward compatibility.

    Args:
        board: Board to solve
        timeout: Maximum solving time in seconds

    Returns:
        Tuple of (solution_board, statistics)
    """
    solver = CSPSolver(timeout=timeout)
    return solver.solve(board)


