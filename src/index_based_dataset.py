from torch.utils.data import Dataset, DataLoader

class IndexBasedDataset(Dataset):
    """
    The indices in the dataset are engineered based on the specific task. 
    They are precomputed, and stored in the /resources folder.
    The indices ensure the classes distribution match the training task requirements.
    For details on how the indices are constructed - check data_selection.ipynb
    """
    
    def __init__(self, master_dataset, augmented_datset, indices):
        self.master_dataset = master_dataset
        self.augmented_datset = augmented_datset
        self.indices = indices

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        master_idx = self.indices[idx]
        return {
            "master_idx": master_idx,
            "title": self.master_dataset[master_idx]["title"],
            "abstract": self.master_dataset[master_idx]["abstract"],
            "raw_categories": self.master_dataset[master_idx]["categories"],
            "parent_categories": self.augmented_datset[master_idx][2],
            "remapped_categories": self.augmented_datset[master_idx][3]
        }