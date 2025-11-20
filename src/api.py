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
from src.core.loader import (
    load_board_json,
    create_board_from_json,
    BOARDS_DIR
)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

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

