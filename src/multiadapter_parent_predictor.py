import torch
import numpy as np
from transformers import AutoTokenizer
from adapters import AutoAdapterModel
from adapters.composition import Parallel

class MultiAdapterParentPredictor:
    def __init__(
        self, 
        model_name: str = "allenai/specter2_base",
        adapter_configs: list = None, # List of dicts: {"path": "...", "name": "..."}
        mlb = None, 
        device: str = None
    ):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.mlb = mlb
        self.adapter_names = [cfg["name"] for cfg in adapter_configs]

        print(f"Initializing Multi-Adapter Pipeline on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoAdapterModel.from_pretrained(model_name)

        # 1. Load all adapters and their respective heads
        for cfg in adapter_configs:
            print(f"  -> Loading {cfg['name']}...")
            self.model.load_adapter(cfg["path"], load_as=cfg["name"])
        
        # 2. Set them to run in Parallel
        # This tells the model: "In every layer, pass the input through all these adapters"
        self.model.set_active_adapters(Parallel(*self.adapter_names))
        
        self.model.to(self.device)
        self.model.eval()

    def predict(self, items: list, threshold: float = 0.5, weights: list = None):
        """
        Args:
            items: List of dicts, e.g., [{"title": "...", "abstract": "..."}]
            threshold: Sigmoid threshold for multi-label classification.
            weights: Optional list of floats to weight adapter outputs.
        """
        # 1. Replicate Collator text construction
        # We use the same formatting: Title + [SEP] + Abstract
        texts = [
            f"{item['title']}{self.tokenizer.sep_token}{item.get('abstract', '')}" 
            for item in items
        ]
    
        # 2. Tokenization
        inputs = self.tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt"
        ).to(self.device)
        
        # Handle default weighting
        if weights is None:
            weights = [1.0 / len(self.adapter_names)] * len(self.adapter_names)
    
        # 3. Model Inference
        with torch.no_grad():
            # Passing inputs through the Parallel adapter setup
            outputs = self.model(**inputs)
            if len(self.adapter_names) == 1:
                outputs = [outputs]
            
            # if not isinstance(outputs, (list, tuple)):
            #     outputs = [outputs]
            
            # In Parallel mode, outputs is a list of AdapterOutput objects
            # We extract logits from each specific adapter head
            logits = []
            for output in outputs:
                logits.append(torch.sigmoid(output.logits).cpu().numpy())
            
            # 4. Weighted Aggregation
            # We ensemble the probabilities from all 3+ adapters
            final_probs = np.zeros_like(logits[0])
            for p, w in zip(logits, weights):
                final_probs += (p * w)
    
        # 5. Mapping back to Labels
        results = []
        for i, prob_dist in enumerate(final_probs):
            preds = (prob_dist > threshold).astype(int)
            
            # Use inverse_transform to get the original class names
            human_labels = []
            if self.mlb:
                human_labels = self.mlb.inverse_transform(np.expand_dims(preds, axis=0))[0]
                
            results.append({
                "logits": logits,
                "probabilities": prob_dist.tolist(),
                "labels": list(human_labels),
                "labels_mlb": self.mlb.transform([list(human_labels)])
            })
    
        return results