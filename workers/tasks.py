def filter_latest_only(paper):
    """
    Returns the paper ID and the version number of the current entry.
    We will use this to deduplicate in the main process.
    """
    # versions looks like: [{"version": "v1", "created": "..."}, {"version": "v2", "created": "..."}]
    current_version = int(paper['versions'][-1]['version'].replace('v', ''))
    return {
        'id': paper['id'],
        'version': current_version,
        'full_entry': paper
    }

def version(paper):
    if "version" in paper:
        return paper['version']
    return None

def get_all_categories(paper):
    if "categories" in paper:
        return paper["categories"]
    return None

def filter_by_category(paper, category=None, exact=False):
    """
    Returns the paper if it matches the category criteria.
    
    Args:
        paper (dict): The paper object.
        category (str): The tag to look for (e.g., 'cs' or 'cs.LG').
        exact (bool): If True, matches the full string. 
                     If False, matches by prefix.
    """
    if not category:
        return paper
        
    tags = paper.get('categories', '').split()
    
    if exact:
        # Check if the tag exists exactly as written
        if any(tag == category for tag in tags):
            return paper
    else:
        # Check if any tag starts with the prefix
        if any(tag.startswith(category) for tag in tags):
            return paper
            
    return None