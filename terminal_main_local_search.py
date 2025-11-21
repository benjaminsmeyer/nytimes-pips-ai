#!/usr/bin/env python3
"""
to run:
    python terminal_main_local_search.py solve <difficulty> <date>
    python terminal_main_local_search.py batch <difficulty>
"""
import argparse
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.solvers.local_search_runner_ast import solve_puzzle, batch_solve

def cmd_solve(args):
    print(f"Solving {args.difficulty} puzzle for {args.date}...")
    result = solve_puzzle(args.difficulty, args.date, timeout=args.timeout, max_iterations=args.max_iterations)
    
    if result['success']:
        print("\nSolution found!")
        print(f"Time: {result['time_taken']:.4f}s")
        print(f"Stats: {result['stats']}")
        print("\nMoves:")
        for move in result['solution']:
            print(f"  Place {move['domino']} at {move['pos1']}-{move['pos2']}")
    
    # error handling
    else:
        print("\nFailed to solve.")
        error_msg = result.get('error', 'Unknown')
        print(f"Error: {error_msg}")
        if 'traceback' in result:
            print("\nTraceback:")
            print(result['traceback'])
        if 'stats' in result:
            print(f"Stats: {result['stats']}")

def cmd_batch(args):
    print(f"Running batch test for {args.difficulty} (limit={args.limit})...")
    results = batch_solve(args.difficulty, limit=args.limit, timeout=args.timeout, max_iterations=args.max_iterations)
    
    solved = sum(1 for r in results if r['success'])
    print(f"\nSummary: {solved}/{len(results)} solved.")

def main():
    parser = argparse.ArgumentParser(description="NYTimes Pips Local Search Solver")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Solve command
    solve_parser = subparsers.add_parser("solve", help="Solve a single puzzle")
    solve_parser.add_argument("difficulty", choices=["easy", "medium", "hard"], help="Puzzle difficulty")
    solve_parser.add_argument("date", help="Puzzle date (YYYY-MM-DD)")
    solve_parser.add_argument("--timeout", type=float, default=30.0, help="Solver timeout in seconds (default: 30 seconds)")
    solve_parser.add_argument("--max-iterations", type=int, default=10000, help="Max iterations (default: 10000)")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run batch verification")
    batch_parser.add_argument("difficulty", choices=["easy", "medium", "hard"], help="Puzzle difficulty")
    batch_parser.add_argument("--limit", type=int, default=5, help="Number of puzzles to solve (default: 5)")
    batch_parser.add_argument("--timeout", type=float, default=30.0, help="Timeout per puzzle (default: 30 seconds)")
    batch_parser.add_argument("--max-iterations", type=int, default=10000, help="Max iterations per puzzle (default: 10000)")
    
    args = parser.parse_args()
    
    if args.command == "solve":
        cmd_solve(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

