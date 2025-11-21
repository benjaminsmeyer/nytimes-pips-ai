"""
Solver performance analysis and comparison tool
Performs analysis of CSP and Local Search solvers.
"""
import os
import time
import json
import tracemalloc
import statistics
import multiprocessing
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats

from src.core.loader import create_board_from_json, BOARDS_DIR
from src.solvers.csp_solver import CSPSolver
from src.solvers.local_search_solver import LocalSearchSolver

class SolverAnalyzer:
    def __init__(self, output_dir="analysis_results"):
        """Initialize with output directory"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Setup plotting style
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.figsize'] = [12, 8]
        
    def run_analysis(self, limit_per_difficulty: int = 100, runs_per_puzzle: int = 100):
        """Run full analysis suite on all puzzles"""        
        results = []
        
        for difficulty in ['easy', 'medium', 'hard']:
            puzzles = self._get_puzzles(difficulty, limit_per_difficulty)
            print(f"\nAnalyzing {len(puzzles)} {difficulty} puzzles...")
            
            for puzzle_path in puzzles:
                puzzle_id = puzzle_path.stem
                print(f"  Processing {puzzle_id}...", end="", flush=True)
                
                # Analyze CSP
                csp_metrics = self._benchmark_solver('csp', puzzle_path, runs=1)
                for m in csp_metrics:
                    m['difficulty'] = difficulty
                    m['puzzle_id'] = puzzle_id
                    results.append(m)
                
                # Analyze Local Search (multiple runs due to randomness)
                ls_metrics = self._benchmark_solver('local_search', puzzle_path, runs=runs_per_puzzle)
                for m in ls_metrics:
                    m['difficulty'] = difficulty
                    m['puzzle_id'] = puzzle_id
                    results.append(m)
                
                print(" Done.")
                
        self.results_df = pd.DataFrame(results)
        return self.results_df

    def _get_puzzles(self, difficulty: str, limit: int) -> List[Path]:
        """Get list of puzzle paths"""
        difficulty_dir = BOARDS_DIR / difficulty
        if not difficulty_dir.exists():
            return []
        return sorted(list(difficulty_dir.glob("*.json")))[:limit]

    def _benchmark_solver(self, solver_type: str, puzzle_path: Path, runs: int) -> List[Dict]:
        """Run benchmark for a specific solver and puzzle"""
        metrics_list = []
        
        with open(puzzle_path, 'r') as f:
            board_data = json.load(f)
            
        # Pre-calculate puzzle complexity features
        board = create_board_from_json(board_data)
        complexity = {
            'num_dominoes': len(board.available_dominoes),
            'num_regions': len(board.regions),
            'grid_size': board.rows * board.cols,
            'constraint_density': len(board.regions) / (board.rows * board.cols) if board.rows * board.cols > 0 else 0
        }
        
        for i in range(runs):
            # Re-create board for each run to ensure fresh state
            board = create_board_from_json(board_data)
            
            if solver_type == 'csp':
                solver = CSPSolver(timeout=10000.0)
            else:
                solver = LocalSearchSolver(timeout=10000.0)
            
            # Memory profiling
            tracemalloc.start()
            start_time = time.time()
            
            solution, stats = solver.solve(board)
            
            duration = time.time() - start_time
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            metrics = {
                'solver': solver_type,
                'run_idx': i,
                'success': solution is not None,
                'time': duration,
                'peak_memory_mb': peak_mem / (1024 * 1024),
                'nodes_explored': stats.get('nodes_explored', 0),
                'backtracks': stats.get('backtracks', 0),
                'iterations': stats.get('iterations', 0),
                'restarts': stats.get('restarts', 0),
                'best_cost': stats.get('best_cost', 0)
            }
            metrics.update(complexity)
            metrics_list.append(metrics)
            
        return metrics_list

    def create_all_plots(self, df: pd.DataFrame):
        """Generate all requested visualizations"""
        print("\nGenerating visualizations...")
        
        # 1. Time Comparison Bar Chart
        self._plot_time_comparison(df)
        
        # 2. Scaling Analysis Line Graph
        self._plot_scaling_analysis(df)
        
        # 3. Success Rate Heatmap
        self._plot_success_heatmap(df)
        
        # 4. Performance Overview Dashboard
        self._plot_dashboard(df)

    def _plot_time_comparison(self, df: pd.DataFrame):
        """Bar chart of solve times with error bars"""
        plt.figure(figsize=(14, 8))
        
        # Aggregate data
        agg_df = df.groupby(['difficulty', 'solver'])['time'].agg(['mean', 'std']).reset_index()
        
        sns.barplot(data=df, x='difficulty', y='time', hue='solver', errorbar='sd', capsize=.1)
        plt.title('Solver Time Comparison by Difficulty')
        plt.ylabel('Time (seconds)')
        plt.xlabel('Difficulty')
        plt.yscale('log')  # Log scale for better visibility of differences
        
        plt.savefig(self.output_dir / 'time_comparison.png')
        plt.close()

    def _plot_scaling_analysis(self, df: pd.DataFrame):
        """Line graph of time vs complexity"""
        plt.figure(figsize=(12, 8))
        
        sns.lmplot(data=df, x='num_dominoes', y='time', hue='solver', logx=True, height=8, aspect=1.5)
        plt.title('Scaling Analysis: Time vs Puzzle Size')
        plt.ylabel('Time (seconds)')
        plt.xlabel('Number of Dominoes')
        plt.yscale('log')
        
        plt.savefig(self.output_dir / 'scaling_analysis.png')
        plt.close()

    def _plot_success_heatmap(self, df: pd.DataFrame):
        """Heatmap of success rates"""
        success_rates = df.groupby(['difficulty', 'solver'])['success'].mean().unstack() * 100
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(success_rates, annot=True, fmt='.1f', cmap='RdYlGn', vmin=0, vmax=100)
        plt.title('Success Rate (%) by Difficulty and Solver')
        
        plt.savefig(self.output_dir / 'success_heatmap.png')
        plt.close()

    def _plot_dashboard(self, df: pd.DataFrame):
        """Create 2x2 dashboard"""
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        
        # Top-left: Average Time
        sns.barplot(data=df, x='difficulty', y='time', hue='solver', ax=axes[0, 0])
        axes[0, 0].set_title('Average Solve Time')
        axes[0, 0].set_yscale('log')
        
        # Top-right: Success Rate
        success_df = df.groupby(['difficulty', 'solver'])['success'].mean().reset_index()
        sns.barplot(data=success_df, x='difficulty', y='success', hue='solver', ax=axes[0, 1])
        axes[0, 1].set_title('Success Rate')
        axes[0, 1].set_ylim(0, 1.1)
        
        # Bottom-left: Memory Usage
        sns.boxplot(data=df, x='difficulty', y='peak_memory_mb', hue='solver', ax=axes[1, 0])
        axes[1, 0].set_title('Peak Memory Usage (MB)')
        
        # Bottom-right: Iterations/Nodes (Normalized)
        # Normalize to compare apples to oranges roughly
        df_norm = df.copy()
        df_norm['effort'] = df_norm.apply(lambda x: x['nodes_explored'] if x['solver'] == 'csp' else x['iterations'], axis=1)
        sns.stripplot(data=df_norm, x='difficulty', y='effort', hue='solver', dodge=True, ax=axes[1, 1])
        axes[1, 1].set_title('Search Effort (Nodes vs Iterations)')
        axes[1, 1].set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'dashboard.png')
        plt.close()

    def generate_report(self, df: pd.DataFrame):
        """Generate HTML report"""
        print("\nGenerating HTML report...")
        
        # Calculate summary stats
        summary = df.groupby(['difficulty', 'solver']).agg({
            'time': ['mean', 'std'],
            'success': 'mean',
            'peak_memory_mb': 'mean'
        }).round(4)
        
        html_content = f"""
        <html>
        <head>
            <title>Solver Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1, h2 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .img-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .img-box {{ flex: 1; min-width: 45%; border: 1px solid #eee; padding: 10px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Solver Performance Analysis Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Summary Statistics</h2>
            {summary.to_html()}
            
            <h2>Visualizations</h2>
            <div class="img-container">
                <div class="img-box">
                    <h3>Performance Dashboard</h3>
                    <img src="dashboard.png" alt="Dashboard">
                </div>
                <div class="img-box">
                    <h3>Time Comparison</h3>
                    <img src="time_comparison.png" alt="Time Comparison">
                </div>
                <div class="img-box">
                    <h3>Scaling Analysis</h3>
                    <img src="scaling_analysis.png" alt="Scaling Analysis">
                </div>
                <div class="img-box">
                    <h3>Success Heatmap</h3>
                    <img src="success_heatmap.png" alt="Success Heatmap">
                </div>
            </div>
            
            <h2>Conclusions</h2>
            <ul>
                <li><b>CSP Solver:</b> Best for deterministic, exact solutions on smaller to medium puzzles.</li>
                <li><b>Local Search Solver:</b> Can be effective for finding solutions in large search spaces, but stochastic nature means variable runtime.</li>
            </ul>
        </body>
        </html>
        """
        
        with open(self.output_dir / 'report.html', 'w') as f:
            f.write(html_content)
            
        # Export CSV
        df.to_csv(self.output_dir / 'raw_data.csv', index=False)
        print(f"Report generated at {self.output_dir / 'report.html'}")

    def print_summary(self, df: pd.DataFrame):
        """Print summary to console"""
        print("\nSummary Statistics")
        
        for difficulty in ['easy', 'medium', 'hard']:
            print(f"\nDifficulty: {difficulty.upper()}")
            d_df = df[df['difficulty'] == difficulty]
            
            for solver in ['csp', 'local_search']:
                s_df = d_df[d_df['solver'] == solver]
                if len(s_df) == 0: continue
                
                avg_time = s_df['time'].mean()
                success_rate = s_df['success'].mean() * 100
                
                print(f"  {solver.ljust(15)}: {success_rate:5.1f}% success, {avg_time:6.3f}s avg time")

if __name__ == "__main__":
    analyzer = SolverAnalyzer()
    
    # Run full analysis
    results = analyzer.run_analysis()
    
    # Generate visualizations
    analyzer.create_all_plots(results)
    
    # Export report
    analyzer.generate_report(results)
    
    # Print summary
    analyzer.print_summary(results)
