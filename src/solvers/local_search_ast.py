# local search - aarushi
import time
import math
from typing import List, Tuple, Dict, Optional
from src.core.board import Board
from src.core.domino import Domino
from src.core.region import SumRegion, EqualRegion, NotEqualRegion, GreaterThanRegion, LessThanRegion
import random

# local search solver for pips json format
class LocalSearchSolver:
    # initialize solver, stop after timeout or max iterations reached
    def __init__(self, timeout: float = 30.0, max_iterations: int = 50000):
        self.timeout = timeout
        self.max_iterations = max_iterations
        self.start_time = 0.0
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'forced_moves': 0
        }

    # solves puzzle using local search with simulated annealing and restarts
    def solve(self, board: Board) -> Tuple[Optional[List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]], Dict]:
        self.start_time = time.time()
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'forced_moves': 0,
            'restarts': 0
        }

        max_restarts = 5  # fewer restarts, more iterations per restart
        iterations_per_restart = self.max_iterations // max_restarts
        
        # try multiple restarts with complete random placements
        for restart in range(max_restarts):
            # clone board - don't modify original
            working_board = board.clone()
            
            # fill board completely with random valid tiling
            if not self._random_initial_placement(working_board):
                continue  # failed to create valid tiling, try again
            
            current_cost = self._calculate_cost(working_board)
            best_cost = current_cost
            best_board = working_board.clone()
            
            if best_cost == 0:
                return self._extract_solution(best_board), self.stats
            
            # simulated annealing parameters
            temperature = 100.0
            cooling_rate = 0.995
            
            iterations = 0
            while (time.time() - self.start_time < self.timeout and 
                   iterations < iterations_per_restart and
                   temperature > 0.1):
                
                if working_board.is_complete() and working_board.is_valid_state():
                    return self._extract_solution(working_board), self.stats
                
                # generate neighbor state
                neighbor_board = self._get_neighbor(working_board)
                neighbor_cost = self._calculate_cost(neighbor_board)
                
                # simulated annealing acceptance
                delta = neighbor_cost - current_cost
                
                if delta < 0 or random.random() < math.exp(-delta / temperature):
                    working_board = neighbor_board
                    current_cost = neighbor_cost
                    
                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_board = working_board.clone()
                        self.stats['nodes_explored'] += 1
                        
                        if best_cost == 0:
                            return self._extract_solution(best_board), self.stats
                
                # cool down
                temperature *= cooling_rate
                iterations += 1
            
            self.stats['restarts'] = restart + 1
            
            # check best state from this restart
            if best_board.is_complete() and best_board.is_valid_state():
                return self._extract_solution(best_board), self.stats

        return None, self.stats
    
    # get list of empty positions on board
    def _get_empty_positions(self, board: Board) -> List[Tuple[int, int]]:
        empty = []
        for cell in board._valid_cells:
            if board.is_cell_empty(*cell):
                empty.append(cell)
        return empty
    
    # initial positions - fill board completely with random valid tiling
    def _random_initial_placement(self, board: Board) -> bool:
        """Fill board completely with random valid domino tiling using backtracking."""
        empty_positions = self._get_empty_positions(board)
        
        if not empty_positions:
            return True  # already filled
        
        # pick first empty cell
        cell = empty_positions[0]
        row, col = cell
        
        # find valid adjacent neighbors
        neighbors = [
            (row, col + 1),  # Right
            (row + 1, col),  # Down
            (row, col - 1),  # Left
            (row - 1, col)   # Up
        ]
        random.shuffle(neighbors)
        
        for neighbor in neighbors:
            if neighbor in board._valid_cells and board.is_cell_empty(*neighbor):
                # try random available dominoes
                available = list(board.available_dominoes)
                if not available:
                    return False
                
                random.shuffle(available)
                for domino in available:
                    if board.place_domino(domino, cell, neighbor):
                        # recursively fill rest of board
                        if self._random_initial_placement(board):
                            return True
                        # backtrack
                        board.remove_domino(cell, neighbor)
        
        return False
    
    # check if positions are adjacent (perpendicular)
    def _are_adjacent(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        return (row1 == row2 and abs(col1 - col2) == 1) or (col1 == col2 and abs(row1 - row2) == 1)
    
    # generate neighbor state by modifying board
    def _get_neighbor(self, board: Board) -> Board:
        """Generate neighbor by swapping, flipping, or retiling dominoes."""
        neighbor = board.clone()
        
        move_type = random.random()
        
        if move_type < 0.4:
            self._swap_dominoes(neighbor)
        elif move_type < 0.7:
            self._flip_domino(neighbor)
        else:
            self._retile_dominoes(neighbor)
        
        return neighbor
    
    def _swap_dominoes(self, board: Board):
        """Swap two random dominoes (their values, not positions)."""
        if len(board._placed_dominoes) < 2:
            return
        
        id1, id2 = random.sample(list(board._placed_dominoes.keys()), 2)
        pos1_a, pos1_b = board._placed_dominoes[id1]
        pos2_a, pos2_b = board._placed_dominoes[id2]
        
        # get values
        val1_a = board.get_cell_value(*pos1_a)
        val1_b = board.get_cell_value(*pos1_b)
        val2_a = board.get_cell_value(*pos2_a)
        val2_b = board.get_cell_value(*pos2_b)
        
        # remove both
        board.remove_domino(pos1_a, pos1_b)
        board.remove_domino(pos2_a, pos2_b)
        
        # swap: place d2 at pos1, d1 at pos2
        d1 = Domino(val1_a, val1_b)
        d2 = Domino(val2_a, val2_b)
        
        board.place_domino(d2, pos1_a, pos1_b)
        board.place_domino(d1, pos2_a, pos2_b)
    
    def _flip_domino(self, board: Board):
        """Flip a random domino (swap its two values)."""
        if not board._placed_dominoes:
            return
        
        domino_id = random.choice(list(board._placed_dominoes.keys()))
        pos_a, pos_b = board._placed_dominoes[domino_id]
        
        val_a = board.get_cell_value(*pos_a)
        val_b = board.get_cell_value(*pos_b)
        
        if val_a == val_b:
            return  # no point flipping a double
        
        board.remove_domino(pos_a, pos_b)
        new_domino = Domino(val_b, val_a)
        board.place_domino(new_domino, pos_a, pos_b)
    
    def _retile_dominoes(self, board: Board):
        """Retile two adjacent parallel dominoes (rotate 2x2 block)."""
        if len(board._placed_dominoes) < 2:
            return
        
        # pick random domino
        id1 = random.choice(list(board._placed_dominoes.keys()))
        pos1_a, pos1_b = board._placed_dominoes[id1]
        
        # determine orientation
        is_horizontal = pos1_a[0] == pos1_b[0]
        
        # find adjacent parallel domino
        row, col = pos1_a
        c1 = min(pos1_a[1], pos1_b[1])
        c2 = max(pos1_a[1], pos1_b[1])
        r1 = min(pos1_a[0], pos1_b[0])
        r2 = max(pos1_a[0], pos1_b[0])
        
        candidates = []
        
        if is_horizontal:
            # look for horizontal domino below or above
            if row + 1 < board.rows:
                val_a, id_a = board._grid.get((row+1, c1), (-1, None))
                val_b, id_b = board._grid.get((row+1, c2), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
            if row - 1 >= 0:
                val_a, id_a = board._grid.get((row-1, c1), (-1, None))
                val_b, id_b = board._grid.get((row-1, c2), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
        else:
            # look for vertical domino left or right
            if col + 1 < board.cols:
                val_a, id_a = board._grid.get((r1, col+1), (-1, None))
                val_b, id_b = board._grid.get((r2, col+1), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
            if col - 1 >= 0:
                val_a, id_a = board._grid.get((r1, col-1), (-1, None))
                val_b, id_b = board._grid.get((r2, col-1), (-1, None))
                if id_a is not None and id_a == id_b and id_a != id1:
                    candidates.append(id_a)
        
        if not candidates:
            return
        
        id2 = random.choice(candidates)
        pos2_a, pos2_b = board._placed_dominoes[id2]
        
        # get values
        val1_a = board.get_cell_value(*pos1_a)
        val1_b = board.get_cell_value(*pos1_b)
        val2_a = board.get_cell_value(*pos2_a)
        val2_b = board.get_cell_value(*pos2_b)
        
        # remove both
        board.remove_domino(pos1_a, pos1_b)
        board.remove_domino(pos2_a, pos2_b)
        
        # rotate: if horizontal, make vertical and vice versa
        cells = sorted([pos1_a, pos1_b, pos2_a, pos2_b])
        
        if is_horizontal:
            # new vertical pairs
            new_pos1_a = cells[0]  # top-left
            new_pos1_b = cells[2]  # bottom-left
            new_pos2_a = cells[1]  # top-right
            new_pos2_b = cells[3]  # bottom-right
        else:
            # new horizontal pairs
            new_pos1_a = cells[0]  # top-left
            new_pos1_b = cells[1]  # top-right
            new_pos2_a = cells[2]  # bottom-left
            new_pos2_b = cells[3]  # bottom-right
        
        # place with same dominoes
        d1 = Domino(val1_a, val1_b)
        d2 = Domino(val2_a, val2_b)
        
        if board.place_domino(d1, new_pos1_a, new_pos1_b):
            if not board.place_domino(d2, new_pos2_a, new_pos2_b):
                # revert
                board.remove_domino(new_pos1_a, new_pos1_b)
                board.place_domino(d1, pos1_a, pos1_b)
                board.place_domino(d2, pos2_a, pos2_b)
        else:
            # revert
            board.place_domino(d1, pos1_a, pos1_b)
            board.place_domino(d2, pos2_a, pos2_b)
    
    # calculate cost for board state - lower is better (0 = solved)
    def _calculate_cost(self, board: Board) -> float:
        """Calculate total cost (constraint violations). Lower is better, 0 = perfect."""
        total_cost = 0.0
        
        # get cell values
        cell_values = {}
        for pos, (value, _) in board._grid.items():
            if value != -1:
                cell_values[pos] = value
        
        # calculate cost for each region
        for region in board.regions:
            total_cost += self._calculate_region_cost(region, cell_values)
        
        return total_cost
    
    def _calculate_region_cost(self, region, cell_values: Dict) -> float:
        """Calculate cost for a single region."""
        # if region not complete, return high cost
        if not all(cell in cell_values for cell in region.cells):
            return 100.0
        
        values = [cell_values[cell] for cell in region.cells]
        
        if isinstance(region, SumRegion):
            current_sum = sum(values)
            return abs(current_sum - region.target)
        
        elif isinstance(region, EqualRegion):
            if not values:
                return 0
            # cost = number of values that don't match the most common
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            most_common_count = max(counts.values())
            return len(values) - most_common_count
        
        elif isinstance(region, NotEqualRegion):
            # cost = number of duplicates
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
    
    # calculate reward for board state - higher is better (for compatibility)
    def _calculate_reward(self, board: Board) -> float:
        reward = 0.0
        cell_values = {}
        for pos, (value, domino_id) in board._grid.items():
            if value != -1:
                cell_values[pos] = value
        
        # check if board is solvable (big negative reward if not)
        if not board.can_satisfy_constraints():
            return -50000.0  # huge penalty - reject immediately
        
        if board.has_isolated_cells():
            return -25000.0  # big penalty - reject immediately
        
        # rewards for satisfied constraints (prioritize these)
        satisfied_count = 0
        violated_count = 0
        incomplete_count = 0
        
        for region in board.regions:
            region_complete = all(cell in cell_values for cell in region.cells)
            if region_complete:
                if region.validate(cell_values):
                    # big reward for satisfied constraint
                    reward += 500.0  
                    satisfied_count += 1
                else:
                    # big penalty for violated constraint
                    reward -= 1000.0 
                    violated_count += 1
            else:
                incomplete_count += 1
                # partial credit for regions that can still be satisfied
                available_pips = [d.left for d in board.available_dominoes] + [d.right for d in board.available_dominoes]
                if region.can_satisfy(cell_values, available_pips):
                    # give reward based on how complete the region is
                    filled = len([c for c in region.cells if c in cell_values])
                    reward += 20.0 * (filled / len(region.cells))  # partial reward
                else:
                    reward -= 500.0  # penalty for unsolvable region
        
        # reward for filling cells (important but secondary to constraints)
        filled_cells = len([c for c in board._valid_cells if not board.is_cell_empty(*c)])
        total_cells = len(board._valid_cells)
        completion_ratio = filled_cells / total_cells
        reward += 50.0 * completion_ratio  # reward for progress
        
        # bonus for having more satisfied constraints than violated
        if satisfied_count > violated_count:
            reward += 200.0 * (satisfied_count - violated_count)
        
        # huge bonus if complete and valid
        if board.is_complete() and board.is_valid_state():
            reward += 100000.0  # massive bonus for solution
        
        return reward
    
    # evaluate board state - lower is better (for compatibility with existing code)
    def _evaluate_board(self, board: Board) -> int:
        reward = self._calculate_reward(board)
        # convert reward to cost (negate and scale)
        return int(-reward)
    
    # remove conflict and attempt domino replacement - uses reward system
    def _resolve_conflict(self, board: Board, conflict: Tuple[Tuple[int, int], Tuple[int, int]]):
        pos1, pos2 = conflict
        
        # get current reward
        current_reward = self._calculate_reward(board)
        
        # remove the domino
        if board.remove_domino(pos1, pos2):
            # try multiple dominoes and placements, pick the one with highest reward
            best_reward = current_reward
            best_domino = None
            best_pos = None
            
            # try a few random dominoes
            available = list(board.available_dominoes)
            random.shuffle(available)
            
            # try more dominoes to find better placements
            for domino in available[:min(20, len(available))]:  # try up to 20 dominoes
                # try placing in same position first
                if board.place_domino(domino, pos1, pos2):
                    reward = self._calculate_reward(board)
                    
                    if reward > best_reward:
                        best_reward = reward
                        best_domino = domino
                        best_pos = (pos1, pos2)
                    
                    board.remove_domino(pos1, pos2)
                
                # try other valid placements
                placements = board.get_valid_placements(domino)
                random.shuffle(placements)
                for new_pos1, new_pos2 in placements[:12]:  # try up to 12 placements
                    if board.place_domino(domino, new_pos1, new_pos2):
                        reward = self._calculate_reward(board)
                        
                        if reward > best_reward:
                            best_reward = reward
                            best_domino = domino
                            best_pos = (new_pos1, new_pos2)
                        
                        board.remove_domino(new_pos1, new_pos2)
            
            # place the best option found (even if worse, for exploration)
            if best_domino and best_pos:
                board.place_domino(best_domino, best_pos[0], best_pos[1])
            elif board.available_dominoes:
                # fallback: try to place any domino
                for domino in available[:5]:
                    placements = board.get_valid_placements(domino)
                    random.shuffle(placements)
                    for new_pos1, new_pos2 in placements[:3]:
                        if board.place_domino(domino, new_pos1, new_pos2):
                            return  # placed something
    
    # extract solution from board
    def _extract_solution(self, board: Board) -> List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]:
        solution = []
        for domino_id, (pos1, pos2) in board._placed_dominoes.items():
            # Reconstruct domino from grid values
            val1, _ = board._grid[pos1]
            val2, _ = board._grid[pos2]
            domino = Domino(val1, val2)
            solution.append((pos1, pos2, domino))
        return solution
    
    # maybe add simulated annealing later??

if __name__ == "__main__":
    pass
    # for testing purposes