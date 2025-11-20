# local search - aarushi
import time
from typing import List, Tuple, Dict, Optional
from src.core.board import Board
from src.core.domino import Domino
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
        
        for restart in range(max_restarts):
            # clone board - don't modify original
            working_board = board.clone()
            
            # initial random placement
            self._random_initial_placement(working_board)
            
            current_reward = self._calculate_reward(working_board)
            best_reward = current_reward
            best_board = working_board.clone()
            
            # simulated annealing parameters
            initial_temp = 2000.0  # even higher temp to allow more exploration
            cooling_rate = 0.998  # slower cooling
            temperature = initial_temp
            
            no_improvement_count = 0
            max_no_improvement = iterations_per_restart // 2  # be more persistent before restarting

            iterations = 0
            while (time.time() - self.start_time < self.timeout and 
                   iterations < iterations_per_restart):
                
                if working_board.is_complete() and working_board.is_valid_state():
                    return self._extract_solution(working_board), self.stats

                # select a random conflict and try to resolve it
                conflict = self._get_random_conflict(working_board)
                if conflict:
                    old_reward = current_reward
                    old_board_state = working_board.clone()
                    
                    self._resolve_conflict(working_board, conflict)
                    new_reward = self._calculate_reward(working_board)
                    self.stats['nodes_explored'] += 1
                    
                    # simulated annealing: accept better moves, sometimes accept worse
                    delta = new_reward - old_reward
                    accept = False
                    
                    if delta > 0:
                        # better move (higher reward) - always accept
                        accept = True
                        current_reward = new_reward
                        if new_reward > best_reward:
                            best_reward = new_reward
                            best_board = working_board.clone()
                            no_improvement_count = 0
                    elif temperature > 0:
                        # worse move - accept with probability based on temperature
                        import math
                        # for negative delta, we want lower probability
                        prob = math.exp(delta / temperature)  # delta is negative, so this is < 1
                        if random.random() < prob:
                            accept = True
                            current_reward = new_reward
                    
                    if not accept:
                        # revert to old state
                        working_board = old_board_state
                        current_reward = old_reward
                    else:
                        no_improvement_count = 0 if delta > 0 else no_improvement_count + 1
                    
                    # cool down temperature
                    temperature *= cooling_rate
                else:
                    # if no conflicts found but board not complete, try to fill empty spaces
                    if not working_board.is_complete():
                        empty_positions = self._get_empty_positions(working_board)
                        if len(empty_positions) >= 2:
                            # try multiple placements to find one that improves reward
                            random.shuffle(empty_positions)
                            best_placement_reward = current_reward
                            best_placement = None
                            
                            # try up to 10 pairs of adjacent empty positions
                            for i in range(min(10, len(empty_positions) - 1)):
                                pos1 = empty_positions[i]
                                # find adjacent empty cell
                                row, col = pos1
                                neighbors = [(row-1, col), (row+1, col), (row, col-1), (row, col+1)]
                                for pos2 in neighbors:
                                    if pos2 in empty_positions and self._are_adjacent(pos1, pos2):
                                        if working_board.available_dominoes:
                                            # try a few dominoes
                                            available = list(working_board.available_dominoes)
                                            random.shuffle(available)
                                            for domino in available[:5]:
                                                if working_board.place_domino(domino, pos1, pos2):
                                                    reward = self._calculate_reward(working_board)
                                                    if reward > best_placement_reward:
                                                        best_placement_reward = reward
                                                        best_placement = (domino, pos1, pos2)
                                                    working_board.remove_domino(pos1, pos2)
                            
                            # place the best option found
                            if best_placement and best_placement_reward > current_reward:
                                domino, pos1, pos2 = best_placement
                                working_board.place_domino(domino, pos1, pos2)
                                current_reward = best_placement_reward
                                if current_reward > best_reward:
                                    best_reward = current_reward
                                    best_board = working_board.clone()
                                    no_improvement_count = 0
                            elif empty_positions and working_board.available_dominoes:
                                # fallback: just place something
                                pos1, pos2 = empty_positions[0], empty_positions[1]
                                if self._are_adjacent(pos1, pos2):
                                    domino = random.choice(list(working_board.available_dominoes))
                                    if working_board.place_domino(domino, pos1, pos2):
                                        current_reward = self._calculate_reward(working_board)

                # restart if stuck for too long
                if no_improvement_count > max_no_improvement:
                    # restore best state before restarting
                    working_board = best_board
                    break

                iterations += 1
            
            self.stats['restarts'] = restart + 1
            
            # check if we found a solution in best state
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
    
    # initial positions - places fewer dominoes to start, builds up gradually
    def _random_initial_placement(self, board: Board):
        empty_positions = self._get_empty_positions(board)
        random.shuffle(empty_positions)
        
        # start with fewer placements - maybe 25-50% of board
        target_placements = max(1, len(empty_positions) // 4)  # start with 25% filled
        placed_count = 0
        
        for i in range(0, len(empty_positions) - 1, 2):
            if placed_count >= target_placements:
                break
                
            pos1 = empty_positions[i]
            pos2 = empty_positions[i + 1]
            
            # check if positions are adjacent
            if self._are_adjacent(pos1, pos2):
                if board.available_dominoes:
                    # try multiple dominoes to find one that keeps board solvable
                    available = list(board.available_dominoes)
                    random.shuffle(available)
                    
                    placed = False
                    for domino in available[:10]:  # try up to 10 dominoes
                        if board.place_domino(domino, pos1, pos2):
                            # check if board is still solvable
                            if board.can_satisfy_constraints() and not board.has_isolated_cells():
                                placed_count += 1
                                placed = True
                                break
                            else:
                                # undo if not solvable
                                board.remove_domino(pos1, pos2)
                    
                    if not placed:
                        # if we can't place here, skip this pair
                        continue
    
    # check if positions are adjacent (perpendicular)
    def _are_adjacent(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        row1, col1 = pos1
        row2, col2 = pos2
        return (row1 == row2 and abs(col1 - col2) == 1) or (col1 == col2 and abs(row1 - row2) == 1)
    
    # find random conflict on board
    def _get_random_conflict(self, board: Board) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        if not board._placed_dominoes:
            return None
        
        # get all placed domino positions
        placed_positions = []
        for domino_id, (pos1, pos2) in board._placed_dominoes.items():
            placed_positions.append((pos1, pos2))
        
        if not placed_positions:
            return None
        
        # checks constraints, find violations
        cell_values = {}
        for pos, (value, domino_id) in board._grid.items():
            if value != -1:
                cell_values[pos] = value
        
        # find regions with violations
        violating_regions = []
        for region in board.regions:
            if not region.validate(cell_values):
                violating_regions.append(region)
        
        # if violation, pick random domino from incorrect region
        if violating_regions:
            region = random.choice(violating_regions)
            region_cells = [cell for cell in region.cells if cell in cell_values]
            if region_cells:
                # find a domino that covers one of these cells
                for pos1, pos2 in placed_positions:
                    if pos1 in region_cells or pos2 in region_cells:
                        return (pos1, pos2)
        
        # if no clear violations, just pick a random placed domino
        return random.choice(placed_positions)
    
    # calculate reward for board state - higher is better
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