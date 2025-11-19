#!/usr/bin/env python3
"""
Main entry point for the NYTimes Pips AI Solver.

Usage:
    python main.py solve <difficulty> <date> [--timeout T]
    python main.py batch <difficulty> [--limit N] [--timeout T]
"""
import argparse
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.solvers.solver_runner import solve_puzzle, batch_solve

def cmd_solve(args):
    print(f"Solving {args.difficulty} puzzle for {args.date}...")
    result = solve_puzzle(args.difficulty, args.date, timeout=args.timeout)
    
    if result['success']:
        print("\nSolution found!")
        print(f"Time: {result['time_taken']:.4f}s")
        print(f"Stats: {result['stats']}")
        print("\nMoves:")
        for move in result['solution']:
            print(f"  Place {move['domino']} at {move['pos1']}-{move['pos2']}")
    else:
        print("\nFailed to solve.")
        print(f"Error: {result.get('error', 'Unknown')}")
        if 'stats' in result:
            print(f"Stats: {result['stats']}")

def cmd_batch(args):
    print(f"Running batch test for {args.difficulty} (limit={args.limit})...")
    results = batch_solve(args.difficulty, limit=args.limit, timeout=args.timeout)
    
    solved = sum(1 for r in results if r['success'])
    print(f"\nSummary: {solved}/{len(results)} solved.")

def main():
    parser = argparse.ArgumentParser(description="NYTimes Pips AI Solver")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Solve command
    solve_parser = subparsers.add_parser("solve", help="Solve a single puzzle")
    solve_parser.add_argument("difficulty", choices=["easy", "medium", "hard"], help="Puzzle difficulty")
    solve_parser.add_argument("date", help="Puzzle date (YYYY-MM-DD)")
    solve_parser.add_argument("--timeout", type=float, default=10000.0, help="Solver timeout in seconds (default: 10000 seconds)")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run batch verification")
    batch_parser.add_argument("difficulty", choices=["easy", "medium", "hard"], help="Puzzle difficulty")
    batch_parser.add_argument("--limit", type=int, default=5, help="Number of puzzles to solve (default: 5)")
    batch_parser.add_argument("--timeout", type=float, default=10000.0, help="Timeout per puzzle (default: 10000 seconds)")
    
    args = parser.parse_args()
    
    if args.command == "solve":
        cmd_solve(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
