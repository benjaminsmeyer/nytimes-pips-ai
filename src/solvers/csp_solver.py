"""
CSP Solver for NYTimes Pips puzzle.
Implements backtracking search with forward checking and heuristics.
"""
import time
from typing import Dict, List, Optional, Tuple, Set
from src.core.board import Board
from src.core.domino import Domino

class CSPSolver:
    """
    Constraint Satisfaction Problem solver for Pips.
    
    Uses backtracking search with:
    - Minimum Remaining Values (MRV) variable ordering (implicit in board structure)
    - Forward checking (via board.can_satisfy_constraints)
    - Constraint propagation (via board.has_isolated_cells)
    """
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize solver.
        
        Args:
            timeout: Maximum time in seconds to search
        """
        self.timeout = timeout
        self.start_time = 0.0
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'forced_moves': 0
        }
    
    def solve(self, board: Board) -> Tuple[Optional[List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]], Dict]:
        """
        Solve the puzzle.
        
        Args:
            board: Initial board state
            
        Returns:
            Tuple[Optional[Solution], Dict]: 
                - Solution is list of (pos1, pos2, domino) or None if failed
                - Stats dictionary
        """
        self.start_time = time.time()
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'forced_moves': 0
        }
        
        # Clone board to avoid modifying original
        working_board = board.clone()
        
        # Start search
        if self._backtrack(working_board):
            return self._extract_solution(working_board), self.stats
        
        return None, self.stats
    
    def _backtrack(self, board: Board, depth: int = 0) -> bool:
        """
        Recursive backtracking search.
        
        Args:
            board: Current board state
            
        Returns:
            bool: True if solution found
        """
        self.stats['nodes_explored'] += 1
        indent = "  " * depth
        
        # Check timeout
        if time.time() - self.start_time > self.timeout:
            return False
        
        # Check if complete
        if board.is_complete():
            valid = board.is_valid_state()
            print(f"{indent}Complete. Valid: {valid}")
            return valid
        
        # Pruning: Check if constraints can still be satisfied
        if not board.can_satisfy_constraints():
            self.stats['backtracks'] += 1
            print(f"{indent}Pruned: Constraints not satisfiable")
            return False
            
        # Pruning: Check for isolated cells
        if board.has_isolated_cells():
            self.stats['backtracks'] += 1
            print(f"{indent}Pruned: Isolated cells")
            return False
        
        # Select an empty cell (Variable Ordering)
        target_cell = self._select_unassigned_variable(board)
        if not target_cell:
            return board.is_valid_state()
            
        print(f"{indent}Target: {target_cell}")
        
        row, col = target_cell
        neighbors = [
            (row, col + 1), # Right
            (row + 1, col), # Down
            (row, col - 1), # Left
            (row - 1, col)  # Up
        ]
        
        valid_neighbors = []
        for n_row, n_col in neighbors:
            neighbor = (n_row, n_col)
            if (neighbor in board._valid_cells and 
                board.is_cell_empty(n_row, n_col)):
                valid_neighbors.append(neighbor)
        
        if not valid_neighbors:
            self.stats['backtracks'] += 1
            print(f"{indent}Backtrack: No valid neighbors for {target_cell}")
            return False
            
        # Try each neighbor
        for neighbor in valid_neighbors:
            available_dominoes = list(board.available_dominoes)
            
            for domino in available_dominoes:
                # Try original orientation
                orientations = [domino]
                
                # If not a double, try flipped orientation too
                if not domino.is_double():
                    orientations.append(Domino(domino.right, domino.left))
                
                for d in orientations:
                    print(f"{indent}Trying {d} at {target_cell}-{neighbor}")
                    if board.place_domino(d, target_cell, neighbor):
                        if self._backtrack(board, depth + 1):
                            return True
                        
                        # Backtrack
                        board.remove_domino(target_cell, neighbor)
        
        # If we tried all neighbors and all dominoes and failed
        self.stats['backtracks'] += 1
        return False

    def _select_unassigned_variable(self, board: Board) -> Optional[Tuple[int, int]]:
        """
        Select next empty cell to fill.
        Simple heuristic: Top-left most empty cell.
        """
        for row in range(board.rows):
            for col in range(board.cols):
                if (row, col) in board._valid_cells and board.is_cell_empty(row, col):
                    return (row, col)
        return None

    def _extract_solution(self, board: Board) -> List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]:
        """
        Extract solution from completed board.
        """
        solution = []
        # We can reconstruct the placements from the board state
        # But board._placed_dominoes stores exactly what we need!
        
        for domino_id, (pos1, pos2) in board._placed_dominoes.items():
            # We need to reconstruct the Domino object or find it
            # The board stores (value, id) in the grid
            val1 = board.get_cell_value(*pos1)
            val2 = board.get_cell_value(*pos2)
            domino = Domino(val1, val2)
            solution.append((pos1, pos2, domino))
            
        return solution
