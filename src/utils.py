from __future__ import annotations

from typing import Any


def remap_to_modern_standard(category: str) -> str:
    """
    Translates legacy, decommissioned, or hyphenated arXiv categories 
    into the modern 'Group.Subject' standard.
    """
    # 1. Direct "Classic" to Modern Mapping
    # These are tags that were completely renamed or moved.
    classic_map = {
        # Computer Science
        "cmp-lg": "cs.CL",
        # Mathematics
        "alg-geom": "math.AG",
        "dg-ga": "math.DG",
        "funct-an": "math.FA",
        "q-alg": "math.QA",
        "spectral-theory": "math.SP",
        # Physics / Nonlinear Sciences
        "adap-org": "nlin.AO",
        "chao-dyn": "nlin.CD",
        "patt-sol": "nlin.PS",
        "solv-int": "nlin.SI",
        "comp-gas": "nlin.CG",
        "supr-con": "cond-mat.supr-con",
        "acc-phys": "physics.acc-ph",
        "chem-ph": "physics.chem-ph",
        "plasm-ph": "physics.plasm-ph",
        "atom-ph": "physics.atom-ph",
        "bayes-an": "physics.data-an",
    }

    if category in classic_map:
        return classic_map[category]

    # 2. Modernizing hyphenated Physics archives
    # If it's a legacy archive like 'hep-th' or 'quant-ph', we treat 
    # the archive as the group and the specific tag as the subject.
    legacy_physics = [
        "hep-th", "hep-ph", "hep-ex", "hep-lat", 
        "gr-qc", "quant-ph", "nucl-th", "nucl-ex", "math-ph"
    ]
    
    if category in legacy_physics:
        # These are effectively their own Group and Subject
        return category

    # 3. Handling prefixes that became Groups (astro-ph, cond-mat)
    # If a tag is JUST 'cond-mat' (legacy), we leave it or map to a general sub.
    # If it's already 'cond-mat.mtrl-sci', it's already modern.
    return category

def get_parent_category(category_tag: str, categories_hierarchy: dict[str, Any]) -> str | None:
    """
    Looks up a category tag in the categories_hierarchy structure 
    and returns its top-level Super-Group (e.g., 'Physics' or 'Computer Science').
    """
    for group_name, group_info in categories_hierarchy.items():
        # Iterate through the subgroups (e.g., 'cs', 'math', 'astro-ph')
        for subgroup_name, subgroup_info in group_info['subgroups'].items():
            # Check if the tag exists in this subgroup's tag list
            if category_tag in subgroup_info['tags']:
                return group_name
                
    return None