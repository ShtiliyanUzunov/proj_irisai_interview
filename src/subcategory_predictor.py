import torch
import numpy as np
from transformers import AutoTokenizer
from adapters import AutoAdapterModel
from adapters.composition import Parallel

class SubcategoryPredictor:
    def __init__(
        self, 
        model_name: str = "allenai/specter2_base",
        adapter_configs: list = None, # List of dicts: {"path": "...", "name": "...", "category": "..."}
        device: str = None
    ):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.adapter_configs = adapter_configs

        print(f"Initializing Multi-Adapter Pipeline on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoAdapterModel.from_pretrained(model_name)

        # 1. Load all adapters and their respective heads
        for cfg in adapter_configs:
            print(f"  -> Loading {cfg['name']}...")
            self.model.load_adapter(cfg["path"], load_as=cfg["name"])

        self.model.to(self.device)
        self.model.eval()

    def predict(self, items: list, category: str, threshold: float = 0.5):
        """
        Args:
            items: List of dicts, e.g., [{"title": "...", "abstract": "..."}]
            threshold: Sigmoid threshold for multi-label classification.
        """
        supported_categories = [cfg["category"] for cfg in self.adapter_configs]
        if category not in supported_categories:
            raise ValueError(f"Category {category} is not supported. Supported categories are: {supported_categories}")
        
        active_adapter = [cfg for cfg in self.adapter_configs if cfg["category"] == category][0]

        texts = [
            f"{item['title']}{self.tokenizer.sep_token}{item.get('abstract', '')}" 
            for item in items
        ]
    
        inputs = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt"
        ).to(self.device)
    
        with torch.no_grad():
            self.model.set_active_adapters(active_adapter["name"])
            outputs = self.model(**inputs)

        results = []
        for i, logits in enumerate(outputs.logits):
            preds = (torch.sigmoid(logits).cpu().numpy() > threshold).astype(int)
            
            human_labels = active_adapter["mbl"].inverse_transform(np.expand_dims(preds, axis=0))[0]
                
            results.append({
                "logits": logits,
                "labels": list(human_labels),
                "labels_mlb": active_adapter["mbl"].transform([list(human_labels)])
            })
    
        return results