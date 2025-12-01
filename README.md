# NYTimes Pips AI Solver

## Overview

The **NYTimes Pips AI Solver** is a Python project designed to solve the "Pips" puzzle from the New York Times. It employs advanced Artificial Intelligence techniques, specifically **Constraint Satisfaction Problems (CSP)** and **Local Search (Simulated Annealing)**, to find valid domino placements that satisfy all board constraints.

The project features a comprehensive **GUI** for interactive solving and visualization, **Command Line Interfaces (CLI)** for batch processing and quick solves, and a **Flask API** to serve puzzle data.

## Features

-   **AI Solvers**:
    -   **CSP Solver**: Uses backtracking with forward checking and heuristics (MRV, Degree) to guarantee a solution if one exists.
    -   **Local Search**: Implements Simulated Annealing to probabilistically find solutions, useful for larger or more complex state spaces.
-   **Interactive GUI**: A Tkinter graphical interface to load puzzles, visualize the board, watch the AI solve in real-time, and view statistics.
-   **CLI Tools**: Dedicated command-line scripts for running both CSP and Local Search solvers on single puzzles or in batch mode.
-   **REST API**: A Flask application that provides puzzle data and board states in a JSON format suitable for external AI agents or front-end applications.

## Directory Structure

```
.
├── src/
│   ├── api.py                  # Flask API for serving puzzle data
│   ├── core/                   # Core game logic (Board, Domino, Regions)
│   ├── solvers/                # AI implementations (CSP, Local Search)
│   ├── boards/                 # Database of puzzles (JSON format)
│   └── pips_solver_gui.py      # Main GUI Application
├── terminal_main_solver.py     # CLI entry point for CSP and Local Search Solver
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Getting Started

### Prerequisites

-   Python 3.8+
-   pip (Python package installer)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/benjaminsmeyer/nytimes-pips-ai.git
    cd nytimes-pips-ai
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download puzzle data**:
    ```bash
    python src/fetch_pips_levels.py
    ```

This will create folders under `boards/` and populate them with JSON puzzle files.

## Usage

### 1. Graphical User Interface (GUI)

The GUI is the best way to visualize the solving process.

```bash
python src/pips_solver_gui.py
```
-   **Load Puzzle**: Select difficulty (easy, medium, hard) and date.
-   **Solve**: Choose between "CSP" or "Local Search" and click "Solve Puzzle".
-   **Visualize**: Watch the dominoes being placed in real-time.

### 2. Command Line Interface (CLI)

#### CSP Solver
Run the exact solver based on Constraint Satisfaction.

-   **Solve a single puzzle**:
    ```bash
    python terminal_main_solver.py solve <difficulty> <date>
    # Example: python terminal_main_solver.py solve easy 2023-10-01
    ```

-   **Batch verification**:
    ```bash
    python terminal_main_solver.py batch <difficulty> --limit 5
    ```

#### Local Search Solver
Run the probabilistic solver based on Simulated Annealing.

-   **Solve a single puzzle**:
    ```bash
    python terminal_main_solver.py solve <difficulty> <date> --solver local_search
    ```

-   **Batch verification**:
    ```bash
    python terminal_main_solver.py batch <difficulty> --solver local_search
    ```

### 3. API

Start the Flask server to access puzzle data programmatically.

```bash
python src/api.py
```
-   **Get Puzzle**: `GET /api/puzzle/<difficulty>/<date>`
-   **List Puzzles**: `GET /api/puzzles?difficulty=<difficulty>`

## Solvers Detail

### Constraint Satisfaction Problem (CSP)
The CSP solver models the puzzle as a set of variables (board cells) and constraints (region sums, unique dominoes). It uses:
-   **Backtracking**: Systematically explores valid placements.
-   **Forward Checking**: Prunes the search space by ensuring current moves don't make future moves impossible.
-   **Heuristics**: Minimum Remaining Values (MRV) and Degree Heuristic to choose the most constrained variables first.

### Local Search (Simulated Annealing)
The Local Search solver starts with a random (potentially invalid) full board and iteratively improves it.
-   **Cost Function**: Calculates a "energy" score based on violated constraints (e.g., region sums incorrect, duplicate dominoes).
-   **Simulated Annealing**: Accepts worse moves with a probability that decreases over time (temperature), allowing it to escape local optima.

## Team Contributions
Benjamin Meyer developed the core game logic and environment setup. Catherina Haast built the puzzle dataset through web scraping. Aarushi Thejaswi created the API connecting the dataset to game logic. Shuyan Ke designed the GUI visualization. Benjamin and Shuyan implemented the CSP solver, while Catherina and Aarushi developed the Local Search solver. All members collaborated on analyzing and comparing both solving approaches through performance plots.
