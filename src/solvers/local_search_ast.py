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

    # solves puzzle using local search
    def solve(self, board: Board) -> Tuple[Optional[List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]], Dict]:
        self.start_time = time.time()
        self.stats = {
            'nodes_explored': 0,
            'backtracks': 0,
            'forced_moves': 0
        }

        # clone board - don't modify original
        working_board = board.clone()

        # initial random placement
        self._random_initial_placement(working_board)

        iterations = 0
        while time.time() - self.start_time < self.timeout and iterations < self.max_iterations:
            if working_board.is_complete() and working_board.is_valid_state():
                return self._extract_solution(working_board), self.stats

            # select a random conflict and try to resolve it
            conflict = self._get_random_conflict(working_board)
            if conflict:
                self._resolve_conflict(working_board, conflict)
                self.stats['nodes_explored'] += 1

            iterations += 1

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
                    board.place_domino(domino, pos1, pos2)
    
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
        
        # If no clear violations, just pick a random placed domino
        return random.choice(placed_positions)
    
    # remove conflict and attempt domino replacement
    def _resolve_conflict(self, board: Board, conflict: Tuple[Tuple[int, int], Tuple[int, int]]):
        pos1, pos2 = conflict
        
        # remove the domino
        if board.remove_domino(pos1, pos2):
            # try to place a random available domino
            if board.available_dominoes:
                domino = random.choice(list(board.available_dominoes))
                # try placing in same position
                if not board.place_domino(domino, pos1, pos2):
                    # if that doesn't work, try a different placement
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