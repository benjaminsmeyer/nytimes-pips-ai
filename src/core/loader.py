import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from src.core.board import Board
from src.core.domino import Domino
from src.core.region import (
    Region,
    SumRegion,
    EqualRegion,
    NotEqualRegion,
    GreaterThanRegion,
    LessThanRegion
)

# Base directory for board files
# src/core/loader.py -> src/core -> src -> src/boards
BOARDS_DIR = Path(__file__).parent.parent / "boards"

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
def parse_dominoes(domino_list: List[List[int]]) -> Set[Domino]:
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
def parse_regions(regions_data: List[Dict], board_rows: int, board_cols: int) -> Tuple[List[Region], Set[Tuple[int, int]]]:
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
