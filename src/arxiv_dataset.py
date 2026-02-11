import torch
import json
from torch.utils.data import Dataset

class ArxivDataset(Dataset):
    def __init__(self, file_path):
        self.file_path = file_path
        self.line_offsets = []
        
        print(f"Indexing dataset at {file_path}... (this may take a minute)")
        with open(file_path, 'rb') as f:
            offset = 0
            for line in f:
                self.line_offsets.append(offset)
                offset += len(line)
        print(f"Indexed {len(self.line_offsets)} entries.")

    def __len__(self):
        return len(self.line_offsets)

    def __getitem__(self, idx):
        # Handle slice or single index
        if torch.is_tensor(idx):
            idx = idx.tolist()

        offset = self.line_offsets[idx]
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            f.seek(offset)
            line = f.readline()
            return json.loads(line)