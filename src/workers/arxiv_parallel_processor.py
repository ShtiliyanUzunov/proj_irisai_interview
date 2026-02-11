import json
import os
import concurrent.futures
from multiprocessing import cpu_count

class ArxivParallelProcessor:
    def __init__(self, dataset):
        self.file_path = dataset.file_path
        self.line_offsets = dataset.line_offsets
        self.total_lines = len(self.line_offsets)

    def _partition_and_process(self, start_idx, end_idx, task_func):
        """
        The core worker logic: Opens a private file handle, jumps to the 
        assigned offset, and executes the task_func on each paper.
        """
        partition_results = []
        # Each worker process gets its own independent file pointer
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for i in range(start_idx, end_idx):
                f.seek(self.line_offsets[i])
                line = f.readline()
                if line:
                    paper = json.loads(line)
                    # Execute the specific logic passed by the user
                    output = task_func(paper, i)
                    if output is not None:
                        partition_results.append(output)
        return partition_results

    def map(self, task_func, num_workers=None):
        """
        Slices the dataset and assigns partitions to different CPU cores.
        Results are 
        """
        if num_workers is None:
            num_workers = cpu_count()
            
        chunk_size = self.total_lines // num_workers
        ranges = []
        for i in range(num_workers):
            start = i * chunk_size
            end = self.total_lines if i == num_workers - 1 else (i + 1) * chunk_size
            ranges.append((start, end))
        
        final_collection = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            # We map our renamed worker method to the calculated index ranges
            futures = [
                executor.submit(self._partition_and_process, s, e, task_func) 
                for s, e in ranges
            ]

            for future in futures:
                final_collection.extend(future.result())
                
        return final_collection
