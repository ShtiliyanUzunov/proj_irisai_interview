import torch
import json
import os
from torch.utils.data import Dataset

class ArxivDataset(Dataset):
    def __init__(self, file_path):
        self.file_path = file_path
        self.line_offsets = []
        self.f = None  # Placeholder for the file handle
        
        print(f"Indexing dataset at {file_path}... (this may take a minute)")
        # We use 'rb' for indexing to get exact byte offsets easily
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.line_offsets.append(offset)
                offset += len(line)
        print(f"Indexed {len(self.line_offsets)} entries.")

    def __len__(self):
        return len(self.line_offsets)

    def _get_handle(self):
        """Ensures each process has its own file handle."""
        if self.f is None:
            self.f = open(self.file_path, 'r', encoding='utf-8')
        return self.f

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        # Get the handle (opens file if not already open)
        handle = self._get_handle()
        
        offset = self.line_offsets[idx]
        handle.seek(offset)
        line = handle.readline()
        
        return json.loads(line)

    def __del__(self):
        """Close handle when object is deleted."""
        if self.f is not None:
            self.f.close()