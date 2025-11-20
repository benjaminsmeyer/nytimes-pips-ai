import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from src.api import create_board_from_json, BOARDS_DIR
from src.solvers.local_search_ast import LocalSearchSolver
from src.core.board import Board
from src.core.domino import Domino

# file to load specific puzzle and run local search
def solve_puzzle(difficulty: str, date: str, timeout: float = 30.0, max_iterations: int = 10000) -> Dict:
    board_path = BOARDS_DIR / difficulty / f"{date}.json"
    
    if not board_path.exists():
        return {
            'success': False,
            'error': f"Puzzle not found: {difficulty}/{date}"
        }
        
    try:
        with open(board_path, 'r') as f:
            board_data = json.load(f)
            
        board = create_board_from_json(board_data)
        
        solver = LocalSearchSolver(timeout=timeout, max_iterations=max_iterations)
        start_time = time.time()
        solution, stats = solver.solve(board)
        duration = time.time() - start_time
        
        # Format solution for return
        formatted_solution = []
        if solution:
            for pos1, pos2, domino in solution:
                formatted_solution.append({
                    'pos1': pos1,
                    'pos2': pos2,
                    'domino': str(domino),
                    'pips': [domino.left, domino.right]
                })
        
        return {
            'success': solution is not None,
            'solution': formatted_solution,
            'stats': stats,
            'time_taken': duration,
            'board_size': f"{board.rows}x{board.cols}",
            'dominoes': len(board.available_dominoes) + len(board._placed_dominoes)
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e) or 'Unknown',
            'traceback': traceback.format_exc()
        }

# batch solve - solves multiple puzzles of an inputted difficulty level
def batch_solve(difficulty: str, limit: int = 5, timeout: float = 30.0, max_iterations: int = 10000) -> List[Dict]:
    results = []
    difficulty_dir = BOARDS_DIR / difficulty
    
    if not difficulty_dir.exists():
        return results
        
    files = sorted(list(difficulty_dir.glob("*.json")))[:limit]
    
    print(f"Solving {len(files)} {difficulty} puzzles...")
    
    for file_path in files:
        date = file_path.stem
        print(f"  Solving {date}...", end="", flush=True)
        
        result = solve_puzzle(difficulty, date, timeout, max_iterations)
        result['date'] = date
        result['difficulty'] = difficulty
        
        status = "Success" if result['success'] else "Failed"
        print(f" {status} ({result.get('time_taken', 0):.2f}s)")
        
        results.append(result)
    
    return results

