"""
Local Search Solver for NYTimes Pips puzzle.
Implements Simulated Annealing to find valid domino placements.
"""
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Set, Union
from src.core.board import Board
from src.core.domino import Domino
from src.core.region import Region, SumRegion, EqualRegion, NotEqualRegion, GreaterThanRegion, LessThanRegion

class LocalSearchSolver:
    """
    Simulated Annealing solver for Pips.
    
    Starts with a random complete board (ignoring constraints) and
    iteratively improves it by minimizing constraint violations.
    """
    
    def __init__(self, timeout: float = 30.0, initial_temp: float = 100.0, cooling_rate: float = 0.995, verbose: bool = False):
        """
        Initialize solver.
        
        Args:
            timeout: Maximum time in seconds to search
            initial_temp: Starting temperature for SA
            cooling_rate: Rate at which temperature decreases
            verbose: Whether to print debug info
        """
        self.timeout = timeout
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.verbose = verbose
        self.start_time = 0.0
        self.stats = {
            'iterations': 0,
            'best_cost': float('inf'),
            'restarts': 0
        }
    
    def solve(self, board: Board) -> Tuple[Optional[List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]], Dict]:
        """
        Solve the puzzle using Simulated Annealing.
        
        Args:
            board: Initial board state (empty)
            
        Returns:
            Tuple[Optional[Solution], Dict]: 
                - Solution is list of (pos1, pos2, domino) or None if failed
                - Stats dictionary
        """
        self.start_time = time.time()
        self.stats = {
            'iterations': 0,
            'best_cost': float('inf'),
            'restarts': 0
        }
        
        # We need a complete board to start. 
        # Since the input board is likely empty, we need to fill it.
        # We'll try multiple restarts if we get stuck in a local minimum.
        
        while time.time() - self.start_time < self.timeout:
            self.stats['restarts'] += 1
            
            # 1. Initialize with random complete placement
            current_board = board.clone()
            if not self._random_placement(current_board):
                continue  # Failed to generate a valid tiling, try again
            
            current_cost = self._calculate_total_cost(current_board)
            
            # Keep track of best solution found so far
            best_board = current_board.clone()
            best_cost = current_cost
            
            if best_cost == 0:
                return self._extract_solution(best_board), self.stats
            
            temp = self.initial_temp
            
            # Inner SA loop
            while temp > 0.1 and time.time() - self.start_time < self.timeout:
                self.stats['iterations'] += 1
                
                # 2. Generate neighbor
                neighbor_board = self._get_neighbor(current_board)
                neighbor_cost = self._calculate_total_cost(neighbor_board)
                
                # 3. Acceptance probability
                delta = neighbor_cost - current_cost
                
                if delta < 0 or random.random() < math.exp(-delta / temp):
                    current_board = neighbor_board
                    current_cost = neighbor_cost
                    
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_board = current_board.clone()
                        self.stats['best_cost'] = best_cost
                        
                        if best_cost == 0:
                            return self._extract_solution(best_board), self.stats
                
                # 4. Cool down
                temp *= self.cooling_rate
                
        return None, self.stats

    def _random_placement(self, board: Board) -> bool:
        """
        Fill the board with a random valid tiling of dominoes.
        Uses a randomized backtracking approach.
        """
        # Get all empty cells
        empty_cells = []
        for row in range(board.rows):
            for col in range(board.cols):
                if (row, col) in board._valid_cells and board.is_cell_empty(row, col):
                    empty_cells.append((row, col))
        
        if not empty_cells:
            return True
            
        # Sort by number of neighbors to fail fast (heuristic)
        # Actually, just picking the first one is fine for backtracking
        cell = empty_cells[0]
        
        # Find valid neighbors
        row, col = cell
        neighbors = [
            (row, col + 1), # Right
            (row + 1, col), # Down
            (row, col - 1), # Left
            (row - 1, col)  # Up
        ]
        random.shuffle(neighbors)
        
        for neighbor in neighbors:
            if (neighbor in board._valid_cells and 
                board.is_cell_empty(*neighbor)):
                
                # Pick a random available domino
                available = list(board.available_dominoes)
                if not available:
                    return False
                
                domino = random.choice(available)
                
                # Try to place
                if board.place_domino(domino, cell, neighbor):
                    if self._random_placement(board):
                        return True
                    
                    # Backtrack
                    board.remove_domino(cell, neighbor)
                    
        return False

    def _calculate_total_cost(self, board: Board) -> float:
        """
        Calculate total cost (constraint violations) of the board.
        """
        total_cost = 0.0
        
        # Get cell values once
        cell_values = {}
        for pos, (value, _) in board._grid.items():
            if value != -1:
                cell_values[pos] = value
                
        for region in board.regions:
            total_cost += self._calculate_region_cost(region, cell_values)
            
        return total_cost

    def _calculate_region_cost(self, region: Region, cell_values: Dict[Tuple[int, int], int]) -> float:
        """
        Calculate cost for a single region.
        """
        # If region is not fully filled, that's a problem (shouldn't happen in complete board)
        if not region._is_complete(cell_values):
            return 100.0
            
        values = region._get_region_values(cell_values)
        
        if isinstance(region, SumRegion):
            current_sum = sum(values)
            return abs(current_sum - region.target)
            
        elif isinstance(region, EqualRegion):
            if not values: return 0
            # Cost is number of elements that don't match the most common value
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            most_common_count = max(counts.values())
            return len(values) - most_common_count
            
        elif isinstance(region, NotEqualRegion):
            # Cost is number of duplicates
            return len(values) - len(set(values))
            
        elif isinstance(region, GreaterThanRegion):
            current_sum = sum(values)
            if current_sum > region.threshold:
                return 0
            return region.threshold - current_sum + 1
            
        elif isinstance(region, LessThanRegion):
            current_sum = sum(values)
            if current_sum < region.threshold:
                return 0
            return current_sum - region.threshold + 1
            
        return 0.0

    def _get_neighbor(self, board: Board) -> Board:
        """
        Generate a neighbor state by modifying the board.
        """
        neighbor = board.clone()
        
        # Randomly choose a move type
        move_type = random.random()
        
        if move_type < 0.4:
            self._move_swap_dominoes(neighbor)
        elif move_type < 0.7:
            self._move_flip_domino(neighbor)
        else:
            self._move_retile(neighbor)
            
        return neighbor

    def _move_swap_dominoes(self, board: Board):
        """
        Swap two random dominoes.
        """
        if len(board._placed_dominoes) < 2:
            return
            
        id1, id2 = random.sample(list(board._placed_dominoes.keys()), 2)
        pos1_a, pos1_b = board._placed_dominoes[id1]
        pos2_a, pos2_b = board._placed_dominoes[id2]
        
        # Get values
        val1_a = board.get_cell_value(*pos1_a)
        val1_b = board.get_cell_value(*pos1_b)
        val2_a = board.get_cell_value(*pos2_a)
        val2_b = board.get_cell_value(*pos2_b)
        
        # Remove both
        board.remove_domino(pos1_a, pos1_b)
        board.remove_domino(pos2_a, pos2_b)
        
        # Create new dominoes
        d1 = Domino(val1_a, val1_b)
        d2 = Domino(val2_a, val2_b)
        
        # Place in swapped positions
        # Note: We are swapping the *dominoes* (values), not the positions.
        # So d2 goes to pos1, d1 goes to pos2.
        
        # We need to be careful about availability.
        # remove_domino adds them back to available.
        # So we can just place them.
        
        board.place_domino(d2, pos1_a, pos1_b)
        board.place_domino(d1, pos2_a, pos2_b)

    def _move_flip_domino(self, board: Board):
        """
        Flip a random domino (swap its values).
        """
        if not board._placed_dominoes:
            return
            
        domino_id = random.choice(list(board._placed_dominoes.keys()))
        pos_a, pos_b = board._placed_dominoes[domino_id]
        
        val_a = board.get_cell_value(*pos_a)
        val_b = board.get_cell_value(*pos_b)
        
        if val_a == val_b:
            return # No point flipping a double
            
        board.remove_domino(pos_a, pos_b)
        
        # Place flipped
        new_domino = Domino(val_b, val_a)
        board.place_domino(new_domino, pos_a, pos_b)

    def _move_retile(self, board: Board):
        """
        Try to re-tile two adjacent dominoes.
        """
        if len(board._placed_dominoes) < 2:
            return

        # Pick a random domino
        id1 = random.choice(list(board._placed_dominoes.keys()))
        pos1_a, pos1_b = board._placed_dominoes[id1]
        
        # Determine orientation
        is_horizontal = pos1_a[0] == pos1_b[0]
        
        # Find a neighbor domino that is parallel and adjacent
        # For simplicity, let's look for a specific configuration
        
        neighbor_id = None
        
        if is_horizontal:
            # Look for domino below or above
            row, col = pos1_a
            # Check below: (row+1, col) and (row+1, col+1)
            # Assuming pos1_a is left of pos1_b
            c1 = min(pos1_a[1], pos1_b[1])
            c2 = max(pos1_a[1], pos1_b[1])
            
            candidates = []
            
            # Check below
            if row + 1 < board.rows:
                val_a, id_a = board._grid.get((row+1, c1), (-1, None))
                val_b, id_b = board._grid.get((row+1, c2), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
                    
            # Check above
            if row - 1 >= 0:
                val_a, id_a = board._grid.get((row-1, c1), (-1, None))
                val_b, id_b = board._grid.get((row-1, c2), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
            
            if candidates:
                neighbor_id = random.choice(candidates)
                
        else: # Vertical
            # Look for domino left or right
            r1 = min(pos1_a[0], pos1_b[0])
            r2 = max(pos1_a[0], pos1_b[0])
            col = pos1_a[1]
            
            candidates = []
            
            # Check right
            if col + 1 < board.cols:
                val_a, id_a = board._grid.get((r1, col+1), (-1, None))
                val_b, id_b = board._grid.get((r2, col+1), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
            
            # Check left
            if col - 1 >= 0:
                val_a, id_a = board._grid.get((r1, col-1), (-1, None))
                val_b, id_b = board._grid.get((r2, col-1), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
                    
            if candidates:
                neighbor_id = random.choice(candidates)

        if neighbor_id:
            # We found two parallel adjacent dominoes. 
            # They form a 2x2 square (or 2x1 + 2x1).
            # We can flip them to be perpendicular.
            
            # Get values before removing
            pos2_a, pos2_b = board._placed_dominoes[neighbor_id]
            
            val1_a = board.get_cell_value(*pos1_a)
            val1_b = board.get_cell_value(*pos1_b)
            val2_a = board.get_cell_value(*pos2_a)
            val2_b = board.get_cell_value(*pos2_b)
            
            # Remove them
            board.remove_domino(pos1_a, pos1_b)
            board.remove_domino(pos2_a, pos2_b)
            
            # New positions
            # If they were horizontal, they become vertical
            # The 4 cells involved are pos1_a, pos1_b, pos2_a, pos2_b
            
            cells = sorted([pos1_a, pos1_b, pos2_a, pos2_b])
            # cells[0] is top-left, cells[1] is top-right (or bottom-left if vertical)
            # Actually, sorting tuples works: (r, c).
            # Top-left, Top-right, Bottom-left, Bottom-right for a 2x2.
            
            # If is_horizontal, we had:
            # A A
            # B B
            # We want:
            # C D
            # C D
            
            # If is_vertical, we had:
            # A B
            # A B
            # We want:
            # C C
            # D D
            
            if is_horizontal:
                # New vertical pairs: (top-left, bottom-left) and (top-right, bottom-right)
                new_pos1_a = cells[0] # Top-left
                new_pos1_b = cells[2] # Bottom-left
                
                new_pos2_a = cells[1] # Top-right
                new_pos2_b = cells[3] # Bottom-right
            else:
                # New horizontal pairs: (top-left, top-right) and (bottom-left, bottom-right)
                new_pos1_a = cells[0]
                new_pos1_b = cells[1]
                
                new_pos2_a = cells[2]
                new_pos2_b = cells[3]
            
            # Re-use the dominoes (values)
            # We can assign them randomly to the new positions
            d1 = Domino(val1_a, val1_b)
            d2 = Domino(val2_a, val2_b)
            
            # Try to place
            # Note: place_domino checks if valid. 
            # Since we just cleared a 2x2 area, it should be valid unless the board shape is weird (holes).
            # But we checked adjacency.
            
            if board.place_domino(d1, new_pos1_a, new_pos1_b):
                if not board.place_domino(d2, new_pos2_a, new_pos2_b):
                    # Failed second placement, revert first
                    board.remove_domino(new_pos1_a, new_pos1_b)
                    # Revert to original
                    # (This is getting complicated to revert, but SA can just accept the broken state? 
                    # No, we need a valid complete board)
                    # If we fail, we should restore original.
                    
                    # Restore original
                    d1_orig = Domino(val1_a, val1_b)
                    d2_orig = Domino(val2_a, val2_b)
                    board.place_domino(d1_orig, pos1_a, pos1_b)
                    board.place_domino(d2_orig, pos2_a, pos2_b)
            else:
                # Failed first placement
                # Restore original
                d1_orig = Domino(val1_a, val1_b)
                d2_orig = Domino(val2_a, val2_b)
                board.place_domino(d1_orig, pos1_a, pos1_b)
                board.place_domino(d2_orig, pos2_a, pos2_b)

    def _extract_solution(self, board: Board) -> List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]:
        """
        Extract solution from completed board.
        """
        solution = []
        for domino_id, (pos1, pos2) in board._placed_dominoes.items():
            val1 = board.get_cell_value(*pos1)
            val2 = board.get_cell_value(*pos2)
            domino = Domino(val1, val2)
            solution.append((pos1, pos2, domino))
        return solution
