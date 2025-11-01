import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.core import (
    Board,
    Domino,
    SumRegion,
    EqualRegion,
    NotEqualRegion,
    GreaterThanRegion,
    LessThanRegion
)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Base directory for board files
BOARDS_DIR = Path(__file__).parent / "boards"

# load inputtecd board json file
def load_board_json(difficulty: str, date: str) -> Optional[Dict]:
    """
    Inputs:
        difficulty: 'easy', 'medium', 'hard'
        date: Date string in format 'YYYY-MM-DD'
    
    Returns:
        Dictionary with board data or None if not found
    """
    board_path = BOARDS_DIR / difficulty / f"{date}.json"
    
    if not board_path.exists():
        return None
    
    with open(board_path, 'r') as f:
        return json.load(f)

# parse domino list from json data into Domino objects
def parse_dominoes(domino_list: List[List[int]]) -> set:
    """
    Inputs:
        domino_list: list of pairs, [left, right]
    
    Returns:
        set of Domino objects
    """
    dominoes = set()
    for left, right in domino_list:
        dominoes.add(Domino(left, right))
    return dominoes

# parse regions from json data into Region objects and determine valid cells
def parse_regions(regions_data: List[Dict], board_rows: int, board_cols: int) -> Tuple[List, set]:
    """
    Inputs:
        regions_data: list of region dictionaries
        board_rows: max row index + 1
        board_cols: max column index + 1
    
    Returns:
        (list of Region objects, set of valid cells)
    """
    regions = []
    valid_cells = set()
    
    for region_data in regions_data:
        indices = region_data.get('indices', [])
        region_type = region_data.get('type', '').lower()
        
        # Convert indices to tuples
        cells = [(idx[0], idx[1]) for idx in indices]
        valid_cells.update(cells)
        
        # Skip empty regions
        if region_type == 'empty' or not cells:
            continue
        
        # Create appropriate region type
        if region_type == 'sum':
            target = region_data.get('target')
            if target is not None:
                regions.append(SumRegion(cells, target=target))
        
        elif region_type == 'equals':
            regions.append(EqualRegion(cells))
        
        elif region_type == 'notequals' or region_type == 'notequal':
            regions.append(NotEqualRegion(cells))
        
        elif region_type == 'greater' or region_type == 'greaterthan':
            threshold = region_data.get('target') or region_data.get('threshold')
            if threshold is not None:
                regions.append(GreaterThanRegion(cells, threshold=threshold))
        
        elif region_type == 'less' or region_type == 'lessthan':
            threshold = region_data.get('target') or region_data.get('threshold')
            if threshold is not None:
                regions.append(LessThanRegion(cells, threshold=threshold))
    
    return regions, valid_cells

# creates Board object from json data
def create_board_from_json(board_data: Dict) -> Board:
    """
    Inputs:
        board_data: dict w/board data
    
    Returns:
        Board object
    """
    # parse dominoes
    domino_list = board_data.get('dominoes', [])
    dominoes = parse_dominoes(domino_list) if domino_list else Domino.create_standard_set()
    
    # parse regions and determine board dimensions
    regions_data = board_data.get('regions', [])
    
    # find board dimensions from region indices
    all_indices = []
    for region in regions_data:
        indices = region.get('indices', [])
        all_indices.extend(indices)
    
    if not all_indices:
        raise ValueError("No regions or indices found in board data")
    
    max_row = max(idx[0] for idx in all_indices) + 1
    max_col = max(idx[1] for idx in all_indices) + 1
    
    regions, valid_cells = parse_regions(regions_data, max_row, max_col)
    
    # create board
    board = Board(
        rows=max_row,
        cols=max_col,
        regions=regions,
        dominoes=dominoes,
        valid_cells=valid_cells
    )
    
    return board

# formats board so AI can read it
def format_for_ai(board_data: Dict, board: Board) -> Dict:
    """
    Inputs:
        board_data: original JSON board data
        board: Board object with core logic
    
    Returns:
        dict formatted for AI consumption
    """
    # Format regions for AI
    formatted_regions = []
    for region in board.regions:
        region_info = {
            "cells": region.cells,
            "type": region.__class__.__name__,
            "name": region.name
        }
        
        if isinstance(region, SumRegion):
            region_info["constraint"] = f"sum == {region.target}"
            region_info["target"] = region.target
        elif isinstance(region, EqualRegion):
            region_info["constraint"] = "all cells must have same value"
        elif isinstance(region, NotEqualRegion):
            region_info["constraint"] = "all cells must have different values"
        elif isinstance(region, GreaterThanRegion):
            region_info["constraint"] = f"sum > {region.threshold}"
            region_info["threshold"] = region.threshold
        elif isinstance(region, LessThanRegion):
            region_info["constraint"] = f"sum < {region.threshold}"
            region_info["threshold"] = region.threshold
        
        formatted_regions.append(region_info)
    
    # format dominoes
    formatted_dominoes = []
    for domino in sorted(board.available_dominoes, key=lambda d: (d.left, d.right)):
        formatted_dominoes.append({
            "id": domino.id,
            "pips": [domino.left, domino.right],
            "is_double": domino.is_double(),
            "total_pips": domino.total_pips()
        })
    
    # get current board state
    board_state = []
    for row in range(board.rows):
        row_data = []
        for col in range(board.cols):
            cell = (row, col)
            if cell in board._valid_cells:
                value = board.get_cell_value(row, col)
                row_data.append({
                    "row": row,
                    "col": col,
                    "value": value if value != -1 else None,
                    "is_empty": board.is_cell_empty(row, col)
                })
            else:
                row_data.append({
                    "row": row,
                    "col": col,
                    "value": None,
                    "is_empty": False,
                    "invalid": True
                })
        board_state.append(row_data)
    
    # get available pip counts
    pip_counts = board.get_available_pip_counts()
    
    return {
        "puzzle_id": board_data.get('id'),
        "constructor": board_data.get('constructors', ''),
        "difficulty": None,  # set by API endpoint
        "date": None,  # set by API endpoint
        "board": {
            "rows": board.rows,
            "cols": board.cols,
            "valid_cells": list(board._valid_cells),
            "state": board_state
        },
        "dominoes": {
            "total": len(board.available_dominoes),
            "available": formatted_dominoes,
            "pip_counts": pip_counts
        },
        "constraints": {
            "total_regions": len(board.regions),
            "regions": formatted_regions
        },
        "game_state": {
            "is_complete": board.is_complete(),
            "is_valid": board.is_valid_state(),
            "cells_remaining": sum(1 for cell in board._valid_cells if board.is_cell_empty(*cell)),
            "dominoes_remaining": len(board.available_dominoes)
        }
    }

# get puzzle formatted for AI
@app.route('/api/puzzle/<difficulty>/<date>', methods=['GET'])
def get_puzzle(difficulty: str, date: str):
    """
    Inputs:
        difficulty: One of 'easy', 'medium', 'hard'
        date: Date string in format 'YYYY-MM-DD'
    
    Returns:
        JSON response with formatted puzzle data
    """
    if difficulty not in ['easy', 'medium', 'hard']:
        return jsonify({"error": "Invalid difficulty. Must be 'easy', 'medium', or 'hard'"}), 400
    
    # Load board data
    board_data = load_board_json(difficulty, date)
    
    if board_data is None:
        return jsonify({"error": f"Puzzle not found for {difficulty}/{date}"}), 404
    
    try:
        # Create board object
        board = create_board_from_json(board_data)
        
        # Format for AI
        ai_format = format_for_ai(board_data, board)
        ai_format["difficulty"] = difficulty
        ai_format["date"] = date
        
        return jsonify(ai_format)
    
    except Exception as e:
        return jsonify({"error": f"Error processing puzzle: {str(e)}"}), 500

# lists all available puzzles
@app.route('/api/puzzles', methods=['GET'])
def list_puzzles():
    """
    Query parameters:
        difficulty: Filter by difficulty (optional)
    
    Returns:
        JSON response with list of available puzzles
    """
    difficulty_filter = request.args.get('difficulty')
    
    puzzles = []
    
    for difficulty in ['easy', 'medium', 'hard']:
        if difficulty_filter and difficulty != difficulty_filter:
            continue
        
        difficulty_dir = BOARDS_DIR / difficulty
        if not difficulty_dir.exists():
            continue
        
        for board_file in difficulty_dir.glob("*.json"):
            date = board_file.stem
            try:
                with open(board_file, 'r') as f:
                    board_data = json.load(f)
                
                # Skip empty/invalid puzzles
                if not board_data.get('regions'):
                    continue
                
                puzzles.append({
                    "difficulty": difficulty,
                    "date": date,
                    "puzzle_id": board_data.get('id'),
                    "constructor": board_data.get('constructors', '')
                })
            except Exception as e:
                continue
    
    return jsonify({
        "total": len(puzzles),
        "puzzles": sorted(puzzles, key=lambda x: (x['date'], x['difficulty']))
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

