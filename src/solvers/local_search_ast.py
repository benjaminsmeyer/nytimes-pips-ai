# local search - aarushi
import time
from typing import List, Tuple, Dict, Optional
from src.core.board import Board
from src.core.domino import Domino
import random

# local search solver for pips json format
class LocalSearchSolver:
    # initialize solver, stop after timeout or max iterations reached
    def __init__(self, timeout: float = 30.0, max_iterations: int = 10000):
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

        max_restarts = 10
        iterations_per_restart = self.max_iterations // max_restarts
        
        for restart in range(max_restarts):
            # clone board - don't modify original
            working_board = board.clone()
            
            # initial random placement
            self._random_initial_placement(working_board)
            
            current_score = self._evaluate_board(working_board)
            best_score = current_score
            best_board = working_board.clone()
            
            # simulated annealing parameters
            initial_temp = 100.0
            cooling_rate = 0.99
            temperature = initial_temp
            
            no_improvement_count = 0
            max_no_improvement = iterations_per_restart // 5

            iterations = 0
            while (time.time() - self.start_time < self.timeout and 
                   iterations < iterations_per_restart):
                
                if working_board.is_complete() and working_board.is_valid_state():
                    return self._extract_solution(working_board), self.stats

                # select a random conflict and try to resolve it
                conflict = self._get_random_conflict(working_board)
                if conflict:
                    old_score = current_score
                    old_board_state = working_board.clone()
                    
                    self._resolve_conflict(working_board, conflict)
                    new_score = self._evaluate_board(working_board)
                    self.stats['nodes_explored'] += 1
                    
                    # simulated annealing: accept better moves, sometimes accept worse
                    delta = new_score - old_score
                    accept = False
                    
                    if delta < 0:
                        # better move - always accept
                        accept = True
                        current_score = new_score
                        if new_score < best_score:
                            best_score = new_score
                            best_board = working_board.clone()
                            no_improvement_count = 0
                    elif temperature > 0:
                        # worse move - accept with probability
                        import math
                        prob = math.exp(-delta / temperature)
                        if random.random() < prob:
                            accept = True
                            current_score = new_score
                    
                    if not accept:
                        # revert to old state
                        working_board = old_board_state
                        current_score = old_score
                    else:
                        no_improvement_count = 0 if delta < 0 else no_improvement_count + 1
                    
                    # cool down temperature
                    temperature *= cooling_rate
                else:
                    # if no conflicts found but board not complete, try random placement
                    if not working_board.is_complete():
                        empty_positions = self._get_empty_positions(working_board)
                        if len(empty_positions) >= 2:
                            random.shuffle(empty_positions)
                            pos1, pos2 = empty_positions[0], empty_positions[1]
                            if self._are_adjacent(pos1, pos2) and working_board.available_dominoes:
                                domino = random.choice(list(working_board.available_dominoes))
                                if working_board.place_domino(domino, pos1, pos2):
                                    current_score = self._evaluate_board(working_board)

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
    
    # initial positions - places randomly
    def _random_initial_placement(self, board: Board):
        empty_positions = self._get_empty_positions(board)
        random.shuffle(empty_positions)
        
        # try to place dominoes in pairs
        for i in range(0, len(empty_positions) - 1, 2):
            pos1 = empty_positions[i]
            pos2 = empty_positions[i + 1]
            
            # check if positions are adjacent
            if self._are_adjacent(pos1, pos2):
                if board.available_dominoes:
                    domino = random.choice(list(board.available_dominoes))
                    # only place if successful
                    if not board.place_domino(domino, pos1, pos2):
                        # if placement failed, try a different domino
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
    
    # evaluate board state - lower is better (0 = solved)
    def _evaluate_board(self, board: Board) -> int:
        """Count constraint violations and empty cells."""
        violations = 0
        cell_values = {}
        for pos, (value, domino_id) in board._grid.items():
            if value != -1:
                cell_values[pos] = value
        
        # count constraint violations (only count if region is complete but invalid)
        for region in board.regions:
            # check if region is complete
            region_complete = all(cell in cell_values for cell in region.cells)
            if region_complete:
                # only count as violation if complete but invalid
                if not region.validate(cell_values):
                    violations += 1
            else:
                # incomplete regions: check if they can still be satisfied
                if not region.can_satisfy(cell_values, 
                    [d.left for d in board.available_dominoes] + 
                    [d.right for d in board.available_dominoes]):
                    violations += 1
        
        # count empty cells
        empty_count = sum(1 for cell in board._valid_cells if board.is_cell_empty(*cell))
        
        return violations * 1000 + empty_count
    
    # remove conflict and attempt domino replacement
    def _resolve_conflict(self, board: Board, conflict: Tuple[Tuple[int, int], Tuple[int, int]]):
        pos1, pos2 = conflict
        
        # get current evaluation
        current_score = self._evaluate_board(board)
        
        # remove the domino
        if board.remove_domino(pos1, pos2):
            # try multiple dominoes and placements, pick the best
            best_score = current_score
            best_domino = None
            best_pos = None
            
            # try a few random dominoes
            available = list(board.available_dominoes)
            random.shuffle(available)
            
            for domino in available[:min(5, len(available))]:  # try up to 5 dominoes
                # try placing in same position first
                if board.place_domino(domino, pos1, pos2):
                    score = self._evaluate_board(board)
                    if score < best_score:
                        best_score = score
                        best_domino = domino
                        best_pos = (pos1, pos2)
                    board.remove_domino(pos1, pos2)
                
                # try other valid placements
                placements = board.get_valid_placements(domino)
                random.shuffle(placements)
                for new_pos1, new_pos2 in placements[:3]:  # try up to 3 placements
                    if board.place_domino(domino, new_pos1, new_pos2):
                        score = self._evaluate_board(board)
                        if score < best_score:
                            best_score = score
                            best_domino = domino
                            best_pos = (new_pos1, new_pos2)
                        board.remove_domino(new_pos1, new_pos2)
            
            # place the best option found, or random if no improvement
            if best_domino and best_pos:
                board.place_domino(best_domino, best_pos[0], best_pos[1])
            elif board.available_dominoes:
                # fallback to random placement
                domino = random.choice(list(board.available_dominoes))
                placements = board.get_valid_placements(domino)
                if placements:
                    new_pos1, new_pos2 = random.choice(placements)
                    board.place_domino(domino, new_pos1, new_pos2)
    
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