class E2EPredictor:
    def __init__(self, parent_predictor, subcategory_predictor):
        """
        Args:
            parent_predictor: An instance of MultiAdapterInferencePipeline
            subcategory_predictor: An instance of SubCategoryPredictor
        """
        self.parent_predictor = parent_predictor
        self.subcategory_predictor = subcategory_predictor

    def predict(self, items: list, parent_threshold: float = 0.5, sub_threshold: float = 0.5):
        """
        Runs a tiered prediction: 
        1. Identifies parent categories.
        2. For each identified parent, runs the corresponding sub-category adapter.
        """
        final_results = []

        # 1. Get Parent Predictions for the batch
        # We pass the whole list to the parent predictor for efficiency
        parent_outputs = self.parent_predictor.predict(items, threshold=parent_threshold)

        for i, item in enumerate(items):
            detected_parents = parent_outputs[i]['labels']
            all_subcategories = []

            # 2. For each parent detected, run the specific sub-category adapter
            for parent in detected_parents:
                # Note: We pass [item] as a list to match your predictor's signature
                sub_out = self.subcategory_predictor.predict(
                    [item], 
                    category=parent, 
                    threshold=sub_threshold
                )
                
                # If an adapter existed and returned results, collect the labels
                if sub_out:
                    all_subcategories.extend(sub_out[0]["labels"])

            # 3. Consolidate results for this specific item
            final_results.append({
                "parent_categories": detected_parents,
                "labels": list(set(all_subcategories))
            })

        return final_results