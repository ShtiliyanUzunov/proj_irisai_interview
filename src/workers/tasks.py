from __future__ import annotations

from typing import Any

from src.utils import get_parent_category
from src.utils import remap_to_modern_standard


def get_all_ids(paper: dict[str, Any], idx: int) -> str | None:
    return paper.get("id")


def get_all_categories(paper: dict[str, Any], idx: int) -> str | None:
    return paper.get("categories")


def filter_by_category(
    paper: dict[str, Any],
    idx: int,
    fields: list[str] = [],
    category: str | None = None,
    exact: bool = False,
) -> dict[str, Any] | None:
    """
    Returns specific fields of the paper if it matches the category criteria.
    
    Args:
        paper: The paper object.
        fields: List of strings representing the keys to return.
        category: The tag to look for (e.g., 'cs' or 'cs.LG').
        exact: If True, matches the full string. 
               If False, matches by prefix.
    """
    # Define a helper to extract only requested fields
    def get_selected_fields(p: dict[str, Any]) -> dict[str, Any]:
        return {f: p.get(f) for f in fields}

    if not category:
        return get_selected_fields(paper)
        
    tags = paper.get('categories', '').split()
    
    # Check for a match
    match_found: bool = False
    if exact:
        match_found = any(tag == category for tag in tags)
    else:
        match_found = any(tag.startswith(category) for tag in tags)
            
    return get_selected_fields(paper) if match_found else None


def augment_and_remap_categories(
    paper: dict[str, Any],
    idx: int,
    categories_hierarchy: dict[str, Any] | None = None,
) -> tuple[int, str, list[str], list[str]]:
    """
    Returns a tuple with information for the paper:
    (idx, raw_categories, parent_category, remapped_categories)

    Output:
        idx: being the idx(row) in the dataset.
        raw_categories: the categories unchanged
        parent_categories: list of parent categories, taken from the categories_hierarchy.json
        remapped_categories: the categories remapped to the modern namings
    """
    raw_categories: str = paper.get("categories")
    parent_categories: set[str | None] = set()
    remapped_categories: list[str] = []

    for c in raw_categories.split():
        parent_categories.add(get_parent_category(c, categories_hierarchy))
        remapped_categories.append(remap_to_modern_standard(c))
    
    return (idx, raw_categories, list(parent_categories), remapped_categories)