#!/usr/bin/env python3
"""
NYTimes Pips AI Solver GUI
Interactive interface for solving Pips puzzles with visualization.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import json
import threading
import time
import random
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Import the solver components
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.board import Board
from src.core.domino import Domino
from src.core.loader import create_board_from_json, BOARDS_DIR
from src.solvers.csp_solver import CSPSolver
from src.solvers.local_search_solver import LocalSearchSolver


class StoppableLocalSearchSolver(LocalSearchSolver):
    """Local search solver that can be stopped via a flag."""

    def __init__(self, stop_flag, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_flag = stop_flag

    def solve(self, board: Board):
        """Override solve to check stop flag."""
        self.start_time = time.time()
        self.stats = {
            'iterations': 0,
            'best_cost': float('inf'),
            'restarts': 0
        }

        while time.time() - self.start_time < self.timeout and not self.stop_flag():
            self.stats['restarts'] += 1

            current_board = board.clone()
            if not self._random_placement(current_board):
                continue

            current_cost = self._calculate_total_cost(current_board)
            best_board = current_board.clone()
            best_cost = current_cost

            if best_cost == 0:
                return self._extract_solution(best_board), self.stats

            temp = self.initial_temp

            while temp > 0.1 and time.time() - self.start_time < self.timeout and not self.stop_flag():
                self.stats['iterations'] += 1

                neighbor_board = self._get_neighbor(current_board)
                neighbor_cost = self._calculate_total_cost(neighbor_board)

                delta = neighbor_cost - current_cost

                if delta < 0 or random.random() < math.exp(-delta / temp):
                    current_board = neighbor_board
                    current_cost = neighbor_cost

                    if current_cost < best_cost:
                        best_cost = current_cost
                        best_board = current_board.clone()
                        self.stats['best_cost'] = best_cost

                        if best_cost == 0:
                            return self._extract_solution(best_board), self.stats

                temp *= self.cooling_rate

        return None, self.stats


class PipsSolverGUI:
    """Main GUI application for Pips solver."""

    def __init__(self, root):
        self.root = root
        self.root.title("NYTimes Pips AI Solver")
        self.root.geometry("1400x900")

        # State
        self.board: Optional[Board] = None
        self.solution: Optional[List] = None
        self.solving_thread: Optional[threading.Thread] = None
        self.is_solving = False
        self.stop_requested = False  # Flag for thread cancellation

        # Colors for regions
        self.region_colors = [
            "#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA",
            "#FFD4BA", "#E0BBE4", "#C7CEEA", "#FFDFD3",
            "#B4F8C8", "#FBE7C6", "#A0E7E5", "#FFAEBC"
        ]

        self.setup_ui()

    def setup_ui(self):
        """Setup the UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Left panel - Controls
        self.setup_control_panel(main_frame)

        # Center panel - Board visualization
        self.setup_board_panel(main_frame)

        # Right panel - Statistics and logs
        self.setup_stats_panel(main_frame)

    def setup_control_panel(self, parent):
        """Setup left control panel."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Puzzle selection
        ttk.Label(control_frame, text="Load Puzzle:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )

        ttk.Label(control_frame, text="Difficulty:").grid(row=1, column=0, sticky=tk.W)
        self.difficulty_var = tk.StringVar(value="easy")
        difficulty_combo = ttk.Combobox(
            control_frame, textvariable=self.difficulty_var,
            values=["easy", "medium", "hard"], state="readonly", width=15
        )
        difficulty_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(control_frame, text="Date:").grid(row=2, column=0, sticky=tk.W)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(control_frame, textvariable=self.date_var, width=15)
        date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Button(control_frame, text="Load Puzzle", command=self.load_puzzle).grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 15)
        )

        # Separator
        ttk.Separator(control_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )

        # Solver selection
        ttk.Label(control_frame, text="Solver Settings:", font=('Arial', 10, 'bold')).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )

        ttk.Label(control_frame, text="Algorithm:").grid(row=6, column=0, sticky=tk.W)
        self.solver_var = tk.StringVar(value="csp")
        solver_combo = ttk.Combobox(
            control_frame, textvariable=self.solver_var,
            values=["csp", "local_search"], state="readonly", width=15
        )
        solver_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(control_frame, text="Timeout (s):").grid(row=7, column=0, sticky=tk.W)
        self.timeout_var = tk.StringVar(value="30")
        timeout_entry = ttk.Entry(control_frame, textvariable=self.timeout_var, width=15)
        timeout_entry.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=2)

        # Solve button
        self.solve_button = ttk.Button(
            control_frame, text="🚀 Solve Puzzle",
            command=self.solve_puzzle, style="Accent.TButton"
        )
        self.solve_button.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))

        # Stop button (initially disabled)
        self.stop_button = ttk.Button(
            control_frame, text="⏹ Stop",
            command=self.stop_solving, state="disabled"
        )
        self.stop_button.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            control_frame, variable=self.progress_var,
            mode='indeterminate', length=200
        )
        self.progress_bar.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            control_frame, textvariable=self.status_var,
            foreground="blue", wraplength=200
        )
        status_label.grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Separator
        ttk.Separator(control_frame, orient='horizontal').grid(
            row=13, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )

        # Clear and Export buttons
        ttk.Button(control_frame, text="Clear Board", command=self.clear_board).grid(
            row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2
        )
        ttk.Button(control_frame, text="Export Solution", command=self.export_solution).grid(
            row=15, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2
        )

    def setup_board_panel(self, parent):
        """Setup center board visualization panel."""
        board_frame = ttk.LabelFrame(parent, text="Puzzle Board", padding="10")
        board_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        board_frame.columnconfigure(0, weight=1)
        board_frame.rowconfigure(0, weight=1)

        # Canvas for board
        canvas_frame = ttk.Frame(board_frame)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.board_canvas = tk.Canvas(
            canvas_frame, bg="white", highlightthickness=1,
            highlightbackground="gray"
        )
        self.board_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.board_canvas.yview)
        v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.board_canvas.xview)
        h_scroll.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.board_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # Info label
        self.board_info_var = tk.StringVar(value="No puzzle loaded")
        ttk.Label(board_frame, textvariable=self.board_info_var, foreground="gray").grid(
            row=1, column=0, pady=5
        )

        # Domino display panel
        domino_display_frame = ttk.LabelFrame(board_frame, text="Available Dominoes", padding="5")
        domino_display_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Canvas for dominoes
        self.domino_canvas = tk.Canvas(
            domino_display_frame, bg="white", height=80,
            highlightthickness=1, highlightbackground="gray"
        )
        self.domino_canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for dominoes
        domino_scroll = ttk.Scrollbar(domino_display_frame, orient="horizontal", command=self.domino_canvas.xview)
        domino_scroll.pack(fill=tk.X)
        self.domino_canvas.configure(xscrollcommand=domino_scroll.set)

    def setup_stats_panel(self, parent):
        """Setup right statistics and log panel."""
        stats_frame = ttk.LabelFrame(parent, text="Statistics & Logs", padding="10")
        stats_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        stats_frame.rowconfigure(1, weight=1)

        # Stats display
        self.stats_text = tk.Text(stats_frame, height=10, width=40, state='disabled', wrap=tk.WORD)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Log output
        ttk.Label(stats_frame, text="Solver Log:", font=('Arial', 9, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=(5, 2)
        )

        self.log_text = ScrolledText(stats_frame, height=30, width=40, state='disabled', wrap=tk.WORD)
        self.log_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure text tags
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("success", foreground="green", font=('Arial', 9, 'bold'))
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")

    def load_puzzle(self):
        """Load a puzzle from the boards directory."""
        difficulty = self.difficulty_var.get()
        date = self.date_var.get()

        self.log_message(f"Loading {difficulty} puzzle for {date}...", "info")

        board_path = BOARDS_DIR / difficulty / f"{date}.json"

        if not board_path.exists():
            messagebox.showerror("Error", f"Puzzle not found: {difficulty}/{date}")
            self.log_message(f"Puzzle not found: {board_path}", "error")
            return

        try:
            with open(board_path, 'r') as f:
                board_data = json.load(f)

            self.board = create_board_from_json(board_data)
            self.solution = None

            self.log_message(f"Puzzle loaded successfully!", "success")
            self.log_message(f"  - Board size: {self.board.rows}x{self.board.cols}")
            self.log_message(f"  - Dominoes: {len(self.board.available_dominoes)}")
            self.log_message(f"  - Regions: {len(self.board.regions)}")

            self.board_info_var.set(
                f"{difficulty.capitalize()} - {date} | "
                f"{self.board.rows}x{self.board.cols} | "
                f"{len(self.board.available_dominoes)} dominoes | "
                f"{len(self.board.regions)} constraints"
            )

            self.visualize_board()
            self.visualize_dominoes()
            self.update_stats()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load puzzle: {str(e)}")
            self.log_message(f"Error loading puzzle: {str(e)}", "error")

    def solve_puzzle(self):
        """Start solving the puzzle in a separate thread."""
        if self.board is None:
            messagebox.showwarning("Warning", "Please load a puzzle first!")
            return

        if self.is_solving:
            messagebox.showwarning("Warning", "Already solving!")
            return

        # Get settings
        solver_type = self.solver_var.get()
        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid timeout value!")
            return

        verbose = False

        # Update UI
        self.is_solving = True
        self.stop_requested = False  # Reset stop flag
        self.solve_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar.start()
        self.status_var.set(f"Solving with {solver_type.upper()}...")

        self.log_message(f"\n{'=' * 50}", "info")
        self.log_message(f"Starting {solver_type.upper()} solver...", "info")
        self.log_message(f"Timeout: {timeout}s", "info")

        # Start solver thread
        self.solving_thread = threading.Thread(
            target=self._solve_thread,
            args=(solver_type, timeout, verbose),
            daemon=True
        )
        self.solving_thread.start()

    def _solve_thread(self, solver_type: str, timeout: float, verbose: bool):
        """Worker thread for solving."""
        try:
            # Clone board to avoid modifying original
            working_board = self.board.clone()

            # Create solver
            if solver_type == "csp":
                solver = CSPSolver(timeout=timeout, verbose=verbose)
            else:
                # Use stoppable version for local search
                solver = StoppableLocalSearchSolver(
                    stop_flag=lambda: self.stop_requested,
                    timeout=timeout,
                    verbose=verbose
                )

            # Solve with periodic stop checks
            start_time = time.time()
            solution, stats = solver.solve(working_board)
            duration = time.time() - start_time

            # Check if stopped
            if self.stop_requested:
                self.root.after(0, self._solve_stopped)
                return

            # Update UI from main thread
            self.root.after(0, self._solve_complete, solution, stats, duration)

        except Exception as e:
            self.root.after(0, self._solve_error, str(e))

    def _solve_complete(self, solution, stats, duration):
        """Called when solving completes."""
        self.is_solving = False
        self.solve_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()

        if solution:
            self.solution = solution
            self.log_message(f"\n✓ Solution found in {duration:.3f}s!", "success")
            self.status_var.set("✓ Solved!")

            # Apply solution to board for visualization
            for pos1, pos2, domino in solution:
                self.board.place_domino(domino, pos1, pos2)

            self.visualize_board()

        else:
            self.log_message(f"\n✗ No solution found within timeout", "error")
            self.status_var.set("Failed to solve")

        # Log statistics
        self.log_message("\nStatistics:", "info")
        for key, value in stats.items():
            self.log_message(f"  {key}: {value}")

        self.update_stats(stats, duration if solution else None)

    def _solve_stopped(self):
        """Called when solving is stopped by user."""
        self.is_solving = False
        self.solve_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        self.status_var.set("Stopped by user")
        self.log_message("\n⏹ Solving stopped by user", "warning")

    def _solve_error(self, error_msg):
        """Called when solving encounters an error."""
        self.is_solving = False
        self.solve_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        self.status_var.set("Error occurred")

        self.log_message(f"\nError during solving: {error_msg}", "error")
        messagebox.showerror("Solving Error", f"An error occurred:\n{error_msg}")

    def stop_solving(self):
        """Stop the current solving process."""
        self.stop_requested = True
        self.is_solving = False
        self.status_var.set("Stopping...")
        self.log_message("Stop requested - waiting for solver to terminate...", "warning")
        # The solver thread will check stop_requested and terminate

    def visualize_dominoes(self):
        """Draw available dominoes in the domino panel."""
        if self.board is None:
            self.domino_canvas.delete("all")
            return

        self.domino_canvas.delete("all")

        # Constants
        domino_width = 35
        domino_height = 70
        spacing = 5
        padding = 10

        # Sort dominoes for consistent display
        available = sorted(list(self.board.available_dominoes),
                           key=lambda d: (d.left, d.right))
        placed = sorted([d for _, _, d in (self.solution or [])],
                        key=lambda d: (d.left, d.right))

        total_dominoes = len(available) + len(placed)
        canvas_width = total_dominoes * (domino_width + spacing) + 2 * padding

        self.domino_canvas.config(scrollregion=(0, 0, canvas_width, domino_height + 2 * padding))

        x = padding

        # Draw placed dominoes (grayed out)
        for domino in placed:
            self._draw_single_domino(x, padding, domino_width, domino_height,
                                     domino, available=False)
            x += domino_width + spacing

        # Draw available dominoes
        for domino in available:
            self._draw_single_domino(x, padding, domino_width, domino_height,
                                     domino, available=True)
            x += domino_width + spacing

    def _draw_single_domino(self, x: int, y: int, width: int, height: int,
                            domino: Domino, available: bool = True):
        """Draw a single domino tile."""
        # Background color
        bg_color = "white" if available else "#D3D3D3"
        outline_color = "black" if available else "gray"
        pip_color = "black" if available else "darkgray"

        # Draw domino outline
        self.domino_canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=bg_color, outline=outline_color, width=2
        )

        # Draw center dividing line
        mid_y = y + height // 2
        self.domino_canvas.create_line(
            x, mid_y, x + width, mid_y,
            fill=outline_color, width=1
        )

        # Draw pips on top half (left value)
        half_height = height // 2
        self._draw_domino_half_pips(x, y, width, half_height, domino.left, pip_color)

        # Draw pips on bottom half (right value)
        self._draw_domino_half_pips(x, y + half_height, width, half_height,
                                    domino.right, pip_color)

    def _draw_domino_half_pips(self, x: int, y: int, width: int, height: int,
                               value: int, color: str):
        """Draw pips for one half of a domino."""
        pip_radius = 3
        cx = x + width // 2
        cy = y + height // 2
        offset_x = width // 4
        offset_y = height // 4

        # Pip positions for values 0-6 (relative to center)
        positions = {
            0: [],
            1: [(0, 0)],
            2: [(-offset_x, -offset_y), (offset_x, offset_y)],
            3: [(-offset_x, -offset_y), (0, 0), (offset_x, offset_y)],
            4: [(-offset_x, -offset_y), (offset_x, -offset_y),
                (-offset_x, offset_y), (offset_x, offset_y)],
            5: [(-offset_x, -offset_y), (offset_x, -offset_y), (0, 0),
                (-offset_x, offset_y), (offset_x, offset_y)],
            6: [(-offset_x, -offset_y), (offset_x, -offset_y),
                (-offset_x, 0), (offset_x, 0),
                (-offset_x, offset_y), (offset_x, offset_y)]
        }

        for dx, dy in positions.get(value, []):
            px = cx + dx
            py = cy + dy
            self.domino_canvas.create_oval(
                px - pip_radius, py - pip_radius,
                px + pip_radius, py + pip_radius,
                fill=color, outline=color
            )

    def visualize_board(self):
        """Draw the board on the canvas."""
        if self.board is None:
            return

        self.board_canvas.delete("all")

        # Constants
        cell_size = 60
        padding = 20

        # Calculate canvas size
        canvas_width = self.board.cols * cell_size + 2 * padding
        canvas_height = self.board.rows * cell_size + 2 * padding

        self.board_canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        # Draw region backgrounds first
        region_map = {}
        for idx, region in enumerate(self.board.regions):
            color = self.region_colors[idx % len(self.region_colors)]
            for row, col in region.cells:
                region_map[(row, col)] = (color, region)

        # Draw cells
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                cell = (row, col)
                if cell not in self.board._valid_cells:
                    continue

                x1 = padding + col * cell_size
                y1 = padding + row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                # Background color for region
                bg_color = "white"
                if cell in region_map:
                    bg_color = region_map[cell][0]

                # Draw cell rectangle
                self.board_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=bg_color, outline="gray", width=1
                )

                # Draw pip value if cell is filled
                if not self.board.is_cell_empty(row, col):
                    value = self.board.get_cell_value(row, col)

                    # Draw pips as dots
                    self._draw_pips(x1, y1, cell_size, value)

                    # Draw domino border
                    _, domino_id = self.board._grid[cell]
                    if domino_id:
                        # Find the other half of this domino
                        pos1, pos2 = self.board._placed_dominoes[domino_id]
                        other = pos2 if cell == pos1 else pos1

                        # Draw connecting line
                        cx1 = x1 + cell_size // 2
                        cy1 = y1 + cell_size // 2
                        cx2 = padding + other[1] * cell_size + cell_size // 2
                        cy2 = padding + other[0] * cell_size + cell_size // 2

                        self.board_canvas.create_line(
                            cx1, cy1, cx2, cy2,
                            fill="black", width=3
                        )

        # Draw region constraints as text
        for idx, region in enumerate(self.board.regions):
            if not region.cells:
                continue

            # Get center of region
            avg_row = sum(c[0] for c in region.cells) / len(region.cells)
            avg_col = sum(c[1] for c in region.cells) / len(region.cells)

            x = padding + avg_col * cell_size + cell_size // 2
            y = padding + avg_row * cell_size - 10

            # Get constraint text
            constraint_text = self._get_constraint_text(region)

            self.board_canvas.create_text(
                x, y, text=constraint_text,
                font=('Arial', 10, 'bold'),
                fill="darkblue"
            )

        # Update domino display
        self.visualize_dominoes()

    def _draw_pips(self, x, y, size, value):
        """Draw domino pips (dots) in a cell."""
        pip_radius = 4
        offset = size // 4
        center = size // 2

        # Pip positions for values 0-6
        positions = {
            0: [],
            1: [(center, center)],
            2: [(offset, offset), (size - offset, size - offset)],
            3: [(offset, offset), (center, center), (size - offset, size - offset)],
            4: [(offset, offset), (size - offset, offset),
                (offset, size - offset), (size - offset, size - offset)],
            5: [(offset, offset), (size - offset, offset), (center, center),
                (offset, size - offset), (size - offset, size - offset)],
            6: [(offset, offset), (offset, center), (offset, size - offset),
                (size - offset, offset), (size - offset, center), (size - offset, size - offset)]
        }

        for px, py in positions.get(value, []):
            self.board_canvas.create_oval(
                x + px - pip_radius, y + py - pip_radius,
                x + px + pip_radius, y + py + pip_radius,
                fill="black"
            )

    def _get_constraint_text(self, region) -> str:
        """Get display text for a constraint region."""
        from src.core.region import SumRegion, EqualRegion, NotEqualRegion, GreaterThanRegion, LessThanRegion

        if isinstance(region, SumRegion):
            return f"Σ={region.target}"
        elif isinstance(region, EqualRegion):
            return "="
        elif isinstance(region, NotEqualRegion):
            return "≠"
        elif isinstance(region, GreaterThanRegion):
            return f">{region.threshold}"
        elif isinstance(region, LessThanRegion):
            return f"<{region.threshold}"
        return "?"

    def update_stats(self, solver_stats=None, duration=None):
        """Update statistics display."""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        if self.board:
            self.stats_text.insert(tk.END, "=== Puzzle Info ===\n", "bold")
            self.stats_text.insert(tk.END, f"Board: {self.board.rows}x{self.board.cols}\n")
            self.stats_text.insert(tk.END, f"Total cells: {len(self.board._valid_cells)}\n")
            self.stats_text.insert(tk.END,
                                   f"Dominoes: {len(self.board.available_dominoes) + len(self.board._placed_dominoes)}\n")
            self.stats_text.insert(tk.END, f"Regions: {len(self.board.regions)}\n")
            self.stats_text.insert(tk.END,
                                   f"Filled: {len(self.board._placed_dominoes)}/{len(self.board.available_dominoes) + len(self.board._placed_dominoes)}\n")
            self.stats_text.insert(tk.END, f"\nComplete: {'Yes' if self.board.is_complete() else 'No'}\n")
            self.stats_text.insert(tk.END, f"Valid: {'Yes' if self.board.is_valid_state() else 'No'}\n")

        if solver_stats:
            self.stats_text.insert(tk.END, "\n=== Solver Stats ===\n", "bold")
            if duration:
                self.stats_text.insert(tk.END, f"Time: {duration:.3f}s\n")
            for key, value in solver_stats.items():
                self.stats_text.insert(tk.END, f"{key}: {value}\n")

        self.stats_text.config(state='disabled')

    def log_message(self, message: str, tag: str = ""):
        """Add message to log."""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def clear_board(self):
        """Clear the board and reset."""
        self.board = None
        self.solution = None
        self.board_canvas.delete("all")
        self.domino_canvas.delete("all")
        self.board_info_var.set("No puzzle loaded")
        self.status_var.set("Ready")
        self.update_stats()
        self.log_message("Board cleared", "info")

    def export_solution(self):
        """Export the solution to a JSON file."""
        if not self.solution:
            messagebox.showwarning("Warning", "No solution to export!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                export_data = {
                    "puzzle": {
                        "difficulty": self.difficulty_var.get(),
                        "date": self.date_var.get(),
                        "board_size": f"{self.board.rows}x{self.board.cols}"
                    },
                    "solution": [
                        {
                            "domino": f"[{d.left}|{d.right}]",
                            "position1": list(p1),
                            "position2": list(p2)
                        }
                        for p1, p2, d in self.solution
                    ]
                }

                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)

                self.log_message(f"Solution exported to {file_path}", "success")
                messagebox.showinfo("Success", "Solution exported successfully!")

            except Exception as e:
                self.log_message(f"Export failed: {str(e)}", "error")
                messagebox.showerror("Error", f"Failed to export:\n{str(e)}")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = PipsSolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()