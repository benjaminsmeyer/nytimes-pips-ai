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
        while time.time() - self.start_time < self.timeout and iterations < 10000:
            if working_board.is_solved():
                return self._extract_solution(working_board), self.stats

            # select a random conflict and try to resolve it
            conflict = working_board.get_random_conflict()
            if conflict:
                self._resolve_conflict(working_board, conflict)
                self.stats['nodes_explored'] += 1

            iterations += 1

        return None, self.stats
    
    def _random_initial_placement(self, board: Board):
        empty_positions = board.get_empty_positions()
        random.shuffle(empty_positions)
        for pos1, pos2 in zip(empty_positions[::2], empty_positions[1::2]):
            domino = board.get_random_domino()
            if domino:
                board.place_domino(pos1, pos2, domino)
    
    def _resolve_conflict(self, board: Board, conflict):
        # remove conflicting domino and try to place a new one
        pos1, pos2 = conflict
        board.remove_domino(pos1, pos2)
        new_domino = board.get_random_domino()
        if new_domino:
            board.place_domino(pos1, pos2, new_domino)
    
    def _extract_solution(self, board: Board) -> List[Tuple[Tuple[int, int], Tuple[int, int], Domino]]:
        solution = []
        for pos1, pos2, domino in board.get_placed_dominoes():
            solution.append((pos1, pos2, domino))
        return solution
    
    # maybe add simulated annealing later??

if __name__ == "__main__":
    pass
    # for testing purposes