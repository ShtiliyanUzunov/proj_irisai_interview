from __future__ import annotations

import json
import os
import importlib
from functools import partial
from typing import Any

import kagglehub

from src.jsonl_dataset import JsonLDataset


if __name__ == "__main__":
    path: str = kagglehub.dataset_download("Cornell-University/arxiv/versions/272")
    ds_path: str = os.path.join(path, 'arxiv-metadata-oai-snapshot.json')
    ds: JsonLDataset = JsonLDataset(ds_path)
    
    from src.workers.jsonl_parallel_processor import JsonLParallelProcessor
    from src.workers import tasks
    
    importlib.reload(tasks)
    processor: JsonLParallelProcessor = JsonLParallelProcessor(ds)

    print("Indexing...")
    categories_hierarchy: dict[str, Any] = json.load(open("resources/categories_hierarchy.json", 'r'))
    remapped_index: list[Any] = processor.map(
        partial(tasks.augment_and_remap_categories, categories_hierarchy=categories_hierarchy)
    )

    print("Saving...")
    with open('resources/remapped_index.jsonl', 'w', encoding='utf-8') as f:
        for entry in remapped_index:
            # json.dumps converts the dict to a string
            # we add \n to ensure the next entry starts on a new line
            f.write(json.dumps(entry) + '\n')