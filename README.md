# NYTimes Pips Solver
## Overview
This project provides a framework to analyze and solve the NYTimes Pips puzzle using 2 different AI techniques, Constraint Satisfaction Problem (CSP) and Local Search. It includes tools for fetching daily puzzles, organizing them by difficulty, and running solvers through terminal or GUI interfaces. The project is designed for studying algorithmic performance, automating puzzle solving, and exploring AI strategies.

## Features
- **Puzzle Fetching and Organization**
  - Downloads daily NYTimes Pips puzzles via their API.
  - Saves raw puzzle JSONs in boards/raw/.
  - Splits puzzle JSONs into difficulty levels: easy, medium, and hard.
  - Automates fetching over a range of dates using fetch_pips_levels.py.

- **Solver Framework**
  - CSP-based solver for exact solutions.
  - Local search algorithms for heuristic-based solving.
  - Terminal-based interfaces (terminal_main_solver.py and terminal_main_local_search.py) for running the solvers.
  - Modular design allows adding new solver strategies easily.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/benjaminsmeyer/nytimes-pips-ai.git
cd https://github.com/benjaminsmeyer/nytimes-pips-ai.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Fetch puzzles:

```bash
python src/fetch_pips_levels.py
```

This will create folders under `boards/` and populate them with JSON puzzle files.


## Team Contributions
Benjamin Meyer developed the core game logic and environment setup. Catherina Haast built the puzzle dataset through web scraping. Aarushi Thejaswi created the API connecting the dataset to game logic. Shuyan Ke designed the GUI visualization. Benjamin and Shuyan implemented the CSP solver, while Catherina and Aarushi developed the Local Search solver. All members collaborated on analyzing and comparing both solving approaches through performance plots.
