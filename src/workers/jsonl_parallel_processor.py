from __future__ import annotations

import json
import os
import concurrent.futures
from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.jsonl_dataset import JsonLDataset


class JsonLParallelProcessor:
    def __init__(self, dataset: JsonLDataset) -> None:
        self.file_path: str = dataset.file_path
        self.line_offsets: list[int] = dataset.line_offsets
        self.total_lines: int = len(self.line_offsets)

    def _partition_and_process(
        self,
        start_idx: int,
        end_idx: int,
        task_func: Callable[..., Any],
    ) -> list[Any]:
        """
        The core worker logic: Opens a private file handle, jumps to the 
        assigned offset, and executes the task_func on each paper.
        """
        partition_results: list[Any] = []
        # Each worker process gets its own independent file pointer
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for i in range(start_idx, end_idx):
                f.seek(self.line_offsets[i])
                line = f.readline()
                if line:
                    paper: dict[str, Any] = json.loads(line)
                    # Execute the specific logic passed by the user
                    output: Any = task_func(paper, i)
                    if output is not None:
                        partition_results.append(output)
        return partition_results

    def map(
        self,
        task_func: Callable[..., Any],
        num_workers: int | None = None,
    ) -> list[Any]:
        """
        Slices the dataset and assigns partitions to different CPU cores.
        """
        if num_workers is None:
            num_workers = cpu_count()
            
        chunk_size: int = self.total_lines // num_workers
        ranges: list[tuple[int, int]] = []
        for i in range(num_workers):
            start: int = i * chunk_size
            end: int = self.total_lines if i == num_workers - 1 else (i + 1) * chunk_size
            ranges.append((start, end))
        
        final_collection: list[Any] = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            # We map our renamed worker method to the calculated index ranges
            futures: list[concurrent.futures.Future[list[Any]]] = [
                executor.submit(self._partition_and_process, s, e, task_func) 
                for s, e in ranges
            ]

            for future in futures:
                final_collection.extend(future.result())
                
        return final_collection
