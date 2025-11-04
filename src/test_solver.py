
"""
Batch Puzzle Solver for NYTimes Pips
====================================

Usage:
    python test_solver.py <difficulty> [--base-dir <path>]

Where difficulty is: easy, medium, hard, or all

Example:
    python test_solver.py easy
    python test_solver.py medium
    python test_solver.py hard
    python test_solver.py all

"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List

from src.csp_solver import CSPSolver
from src.core.board import Board
from src.core.domino import Domino
from src.core.region import SumRegion, EqualRegion, NotEqualRegion, GreaterThanRegion, LessThanRegion


def parse_puzzle(puzzle_data: Dict) -> Board:
    """Parse puzzle JSON data into a Board object."""
    # Parse dominoes
    dominoes = set()
    for d in puzzle_data.get('dominoes', []):
        dominoes.add(Domino(d[0], d[1]))

    # If no dominoes specified, use standard set
    if not dominoes:
        dominoes = Domino.create_standard_set()

    # Get board dimensions from regions
    all_indices = []
    for region in puzzle_data.get('regions', []):
        indices = region.get('indices', [])
        all_indices.extend(indices)

    if not all_indices:
        raise ValueError("No regions found in puzzle data")

    max_row = max(idx[0] for idx in all_indices) + 1
    max_col = max(idx[1] for idx in all_indices) + 1

    # Parse regions
    regions = []
    valid_cells = set()

    for region_data in puzzle_data['regions']:
        indices = region_data['indices']
        cells = [(idx[0], idx[1]) for idx in indices]
        valid_cells.update(cells)

        region_type = region_data.get('type', '').lower()

        # Skip empty regions
        if region_type == 'empty' or not cells:
            continue

        # Create appropriate region type
        if region_type == 'sum':
            target = region_data.get('target')
            if target is not None:
                regions.append(SumRegion(cells, target=target))

        elif region_type in ['equals', 'equal']:
            regions.append(EqualRegion(cells))

        elif region_type in ['notequals', 'notequal']:
            regions.append(NotEqualRegion(cells))

        elif region_type in ['greater', 'greaterthan']:
            threshold = region_data.get('target') or region_data.get('threshold')
            if threshold is not None:
                regions.append(GreaterThanRegion(cells, threshold=threshold))

        elif region_type in ['less', 'lessthan']:
            threshold = region_data.get('target') or region_data.get('threshold')
            if threshold is not None:
                regions.append(LessThanRegion(cells, threshold=threshold))

    # Create board
    board = Board(
        rows=max_row,
        cols=max_col,
        regions=regions,
        dominoes=dominoes,
        valid_cells=valid_cells
    )

    return board


def solve_puzzle(filepath: Path, solver: CSPSolver) -> Dict:
    """
    Solve a single puzzle.

    Returns dictionary with results.
    """
    result = {
        'file': filepath.name,
        'success': False,
        'time': 0.0,
        'nodes': 0,
        'backtracks': 0,
        'forced_moves': 0,
        'error': None
    }

    try:
        # Load puzzle
        with open(filepath, 'r') as f:
            puzzle_data = json.load(f)

        # Parse puzzle
        board = parse_puzzle(puzzle_data)

        # Solve
        start_time = time.time()
        solution, stats = solver.solve(board)
        solve_time = time.time() - start_time

        # Update results
        result['time'] = solve_time
        result['nodes'] = stats['nodes_explored']
        result['backtracks'] = stats['backtracks']
        result['forced_moves'] = stats['forced_moves']
        result['success'] = solution is not None

    except Exception as e:
        result['error'] = str(e)

    return result


def solve_difficulty(difficulty: str, base_dir: Path) -> List[Dict]:
    """Solve all puzzles of a given difficulty."""
    puzzle_dir = base_dir / difficulty

    if not puzzle_dir.exists():
        print(f"Error: Directory not found - {puzzle_dir}")
        return []

    # Get all JSON files
    puzzle_files = sorted(puzzle_dir.glob("*.json"))

    if not puzzle_files:
        print(f"No puzzle files found in {puzzle_dir}")
        return []

    print(f"\nSolving {len(puzzle_files)} {difficulty} puzzles...")
    print("-" * 60)

    solver = CSPSolver(timeout=30.0)
    results = []

    for i, filepath in enumerate(puzzle_files, 1):
        result = solve_puzzle(filepath, solver)
        results.append(result)

        # Progress indicator
        if result['success']:
            print(f"  [{i}/{len(puzzle_files)}] ✓ {result['file']}: {result['time']:.3f}s")
        else:
            error_msg = f" - {result['error']}" if result['error'] else ""
            print(f"  [{i}/{len(puzzle_files)}] ✗ {result['file']}{error_msg}")

    return results


def print_summary(results: List[Dict], difficulty: str):
    """Print summary of results."""
    if not results:
        return

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print("\n" + "=" * 60)
    print(f"SUMMARY - {difficulty.upper()}")
    print("=" * 60)

    print(f"\nTotal puzzles: {len(results)}")
    print(f"Solved: {len(successful)} ({100 * len(successful) / len(results):.1f}%)")
    print(f"Failed: {len(failed)}")

    if successful:
        total_time = sum(r['time'] for r in successful)
        avg_time = total_time / len(successful)
        avg_nodes = sum(r['nodes'] for r in successful) / len(successful)
        avg_backtracks = sum(r['backtracks'] for r in successful) / len(successful)
        total_forced = sum(r['forced_moves'] for r in successful)

        print(f"\nPerformance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Average nodes: {avg_nodes:.1f}")
        print(f"  Average backtracks: {avg_backtracks:.1f}")
        print(f"  Total forced moves: {total_forced}")

        # Find hardest puzzles
        by_time = sorted(successful, key=lambda x: x['time'], reverse=True)
        if len(by_time) >= 3:
            print(f"\nHardest puzzles (by time):")
            for r in by_time[:3]:
                print(f"  {r['file']}: {r['time']:.3f}s ({r['nodes']} nodes)")

    if failed:
        print(f"\nFailed puzzles:")
        for r in failed:
            error = f" - {r['error']}" if r['error'] else ""
            print(f"   {r['file']}{error}")


def main():
    """Main entry point."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    difficulty = sys.argv[1].lower()

    # Check valid difficulty
    if difficulty not in ['easy', 'medium', 'hard', 'all']:
        print(f"Error: Invalid difficulty '{difficulty}'")
        print("Must be one of: easy, medium, hard, all")
        sys.exit(1)

    # Get base directory
    base_dir = None
    if len(sys.argv) > 2:
        if sys.argv[2] == '--base-dir' and len(sys.argv) > 3:
            base_dir = Path(sys.argv[3])

    # If not specified, try to find it
    if not base_dir:
        # Try common locations
        possible_dirs = [
            Path("boards"),
            Path("NYT pips/boards"),
            Path("/mnt/user-data/uploads/boards"),
            Path("C:/NYT pips/boards"),
            Path("~/NYT pips/boards").expanduser()
        ]

        for dir_path in possible_dirs:
            if dir_path.exists():
                base_dir = dir_path
                break

        if not base_dir:
            print("Error: Could not find puzzle directory.")
            print("Please specify with --base-dir <path>")
            print("\nExample:")
            print('  python batch_solver.py easy --base-dir "C:/NYT pips/boards"')
            sys.exit(1)

    print("NYTimes Pips Solver")
    print(f"Base directory: {base_dir}")
    print("=" * 60)

    # Solve puzzles
    if difficulty == 'all':
        # Solve all difficulties
        total_results = {
            'easy': [],
            'medium': [],
            'hard': []
        }

        for diff in ['easy', 'medium', 'hard']:
            results = solve_difficulty(diff, base_dir)
            total_results[diff] = results
            print_summary(results, diff)

        # Overall summary
        print("\n" + "=" * 60)
        print("OVERALL SUMMARY")
        print("=" * 60)

        grand_total = 0
        grand_solved = 0

        for diff, results in total_results.items():
            total = len(results)
            solved = sum(1 for r in results if r['success'])
            grand_total += total
            grand_solved += solved

            if total > 0:
                print(f"{diff.capitalize()}: {solved}/{total} ({100 * solved / total:.1f}%)")

        if grand_total > 0:
            print(f"\nTotal: {grand_solved}/{grand_total} ({100 * grand_solved / grand_total:.1f}%)")

    else:
        # Solve single difficulty
        results = solve_difficulty(difficulty, base_dir)
        print_summary(results, difficulty)

    print("\nDone!")


if __name__ == "__main__":
    main()