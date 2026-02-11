from __future__ import annotations

import io
import json
import os

import torch
from torch.utils.data import Dataset

from typing import Any


class JsonLDataset(Dataset):
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.line_offsets: list[int] = []
        self.f: io.TextIOWrapper | None = None  # Placeholder for the file handle
        
        print(f"Indexing dataset at {file_path}... (this may take a minute)")
        # We use 'rb' for indexing to get exact byte offsets easily
        with open(file_path, 'rb') as f:
            offset: int = 0
            for line in f:
                self.line_offsets.append(offset)
                offset += len(line)
        print(f"Indexed {len(self.line_offsets)} entries.")

    def __len__(self) -> int:
        return len(self.line_offsets)

    def _get_handle(self) -> io.TextIOWrapper:
        if self.f is None:
            self.f = open(self.file_path, 'r', encoding='utf-8')
        return self.f

    def __getitem__(self, idx: int | list[int]) -> dict[str, Any]:
        if torch.is_tensor(idx):
            idx = idx.tolist()

        # Get the handle (opens file if not already open)
        handle: io.TextIOWrapper = self._get_handle()
        
        offset: int = self.line_offsets[idx]
        handle.seek(offset)
        line: str = handle.readline()
        
        return json.loads(line)

    def __del__(self) -> None:
        """Close handle when object is deleted."""
        if self.f is not None:
            self.f.close()