"""
Lazy singleton wrapper around the E2E prediction pipeline.

Initializes MultiAdapterParentPredictor, SubcategoryPredictor, and E2EPredictor
on first use. All model / adapter paths are resolved relative to the project root.
"""
import json
import logging
import os
import sys
import threading
from pathlib import Path

from sklearn.preprocessing import MultiLabelBinarizer

logger = logging.getLogger("services.predictor_service")

# Project root: interview_irisai/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Ensure `src/` is on sys.path so the existing modules can be imported
_src_dir = str(PROJECT_ROOT / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


def _create_mlb(target_classes: list) -> MultiLabelBinarizer:
    mlb = MultiLabelBinarizer(classes=target_classes)
    mlb.fit([target_classes])
    return mlb


TARGET_PARENT_CLASSES = [
    "Physics",
    "Mathematics",
    "Computer Science",
    "Quantitative Biology",
    "Statistics",
    "Quantitative Finance",
    "Economics",
    "Electrical Engineering and Systems Science",
]


class PredictorService:
    """Thread-safe lazy singleton that holds the full E2E prediction pipeline."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._predictor = None
        self._initialized = False

    def _initialize(self) -> None:
        """Heavy one-time initialization of all ML models and adapters."""
        from e2e_predictor import E2EPredictor
        from multiadapter_parent_predictor import MultiAdapterParentPredictor
        from subcategory_predictor import SubcategoryPredictor

        resources_dir = PROJECT_ROOT / "resources"
        model_name = os.getenv("MODEL_NAME", "allenai/specter2_base")

        logger.info("Initializing prediction pipeline (model=%s) ...", model_name)

        # --- Parent predictor ---
        mlb_parent = _create_mlb(TARGET_PARENT_CLASSES)
        parent_adapter_configs = [
            {
                "path": str(resources_dir / "parent_categories_adapter"),
                "name": "arxiv_parent_categories_classifier",
            },
            {
                "path": str(resources_dir / "parent_categories_adapter_bucket2"),
                "name": "arxiv_parent_categories_classifier_bucket2",
            },
            {
                "path": str(resources_dir / "parent_categories_adapter_bucket3"),
                "name": "arxiv_parent_categories_classifier_bucket3",
            },
        ]
        parent_predictor = MultiAdapterParentPredictor(
            model_name=model_name,
            adapter_configs=parent_adapter_configs,
            mlb=mlb_parent,
        )

        # --- Subcategory predictor ---
        target_sub_path = resources_dir / "target_sub_classes.json"
        with open(target_sub_path, "r") as f:
            target_sub_categories = json.load(f)

        sub_adapter_configs = []
        for sub_cat_name, classes in target_sub_categories.items():
            sub_adapter_configs.append({
                "category": sub_cat_name,
                "name": f"{sub_cat_name}_categories_adapter",
                "path": str(resources_dir / f"{sub_cat_name}_categories_adapter"),
                "mbl": _create_mlb(classes),
            })

        subcategory_predictor = SubcategoryPredictor(
            model_name=model_name,
            adapter_configs=sub_adapter_configs,
        )

        # --- E2E predictor ---
        self._predictor = E2EPredictor(parent_predictor, subcategory_predictor)
        self._initialized = True
        logger.info("Prediction pipeline ready")

    def eager_load(self) -> None:
        """Force-load all ML models immediately."""
        with self._lock:
            if not self._initialized:
                self._initialize()

    def predict(self, items: list) -> list:
        """
        Run the full E2E prediction pipeline.

        Args:
            items: List of dicts with 'title' and 'abstract' keys.

        Returns:
            List of result dicts with 'parent_categories' and 'labels' keys.
        """
        with self._lock:
            if not self._initialized:
                self._initialize()

        return self._predictor.predict(items)


# Module-level singleton
predictor_service = PredictorService()
