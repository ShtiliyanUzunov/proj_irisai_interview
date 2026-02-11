from src.utils import get_parent_category
from src.utils import remap_to_modern_standard

def get_all_ids(paper, idx):
    return paper.get("id")

def get_all_categories(paper, idx):
    return paper.get("categories")

def filter_by_category(paper, idx, fields=[], category=None, exact=False):
    """
    Returns specific fields of the paper if it matches the category criteria.
    
    Args:
        paper (dict): The paper object.
        fields (list): List of strings representing the keys to return.
        category (str): The tag to look for (e.g., 'cs' or 'cs.LG').
        exact (bool): If True, matches the full string. 
                      If False, matches by prefix.
    """
    # Define a helper to extract only requested fields
    def get_selected_fields(p):
        return {f: p.get(f) for f in fields}

    if not category:
        return get_selected_fields(paper)
        
    tags = paper.get('categories', '').split()
    
    # Check for a match
    match_found = False
    if exact:
        match_found = any(tag == category for tag in tags)
    else:
        match_found = any(tag.startswith(category) for tag in tags)
            
    return get_selected_fields(paper) if match_found else None

def augment_and_remap_categories(paper, idx, categories_hierarchy=None):
    """
    Returns a tuple with information for the paper:
    (idx, raw_categories, parent_category, remapped_categories)

    Output:
        idx (int): being the idx(row) in the dataset.
        raw_categories (list): the categories unchanged
        parent_categories (list): list of parent categories, taken from the categories_hierarchy.json
        remapped_categories (list): the categories remapped to the modern namings
    """
    raw_categories = paper.get("categories")
    parent_categories = set()
    remapped_categories = []

    for c in raw_categories:
        parent_categories.add(get_parent_category(c, categories_hierarchy))
        remapped_categories.append(remap_to_modern_standard(c))
    
    return (idx, raw_categories, list(parent_categories), remapped_categories)