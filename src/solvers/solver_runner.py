"""
Runner module for Pips CSP Solver.
Can load puzzles from the API/filesystem and solve them.
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from src.api import create_board_from_json, BOARDS_DIR
from src.solvers.csp_solver import CSPSolver
from src.core.board import Board
from src.core.domino import Domino

def solve_puzzle(difficulty: str, date: str, timeout: float = 30.0) -> Dict:
    """
    Load and solve a specific puzzle.
    
    Args:
        difficulty: 'easy', 'medium', 'hard'
        date: 'YYYY-MM-DD'
        timeout: Max seconds to search
        
    Returns:
        Dict with results:
        {
            'success': bool,
            'solution': List[...],
            'stats': Dict,
            'time_taken': float
        }
    """
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
        
        solver = CSPSolver(timeout=timeout)
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
        return {
            'success': False,
            'error': str(e)
        }

def batch_solve(difficulty: str, limit: int = 5, timeout: float = 10.0) -> List[Dict]:
    """
    Solve multiple puzzles of a given difficulty.
    
    Args:
        difficulty: 'easy', 'medium', 'hard'
        limit: Max number of puzzles to attempt
        timeout: Timeout per puzzle
        
    Returns:
        List of result dicts
    """
    results = []
    difficulty_dir = BOARDS_DIR / difficulty
    
    if not difficulty_dir.exists():
        return results
        
    files = sorted(list(difficulty_dir.glob("*.json")))[:limit]
    
    print(f"Solving {len(files)} {difficulty} puzzles...")
    
    for file_path in files:
        date = file_path.stem
        print(f"  Solving {date}...", end="", flush=True)
        
        result = solve_puzzle(difficulty, date, timeout)
        result['date'] = date
        result['difficulty'] = difficulty
        
        status = "Success" if result['success'] else "Failed"
        print(f" {status} ({result.get('time_taken', 0):.2f}s)")
        
        results.append(result)
        
    return results
