from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.ml.model_registry import ModelRegistry


@dataclass(frozen=True, slots=True)
class PredictionOutput:
    model_name: str
    predictions: np.ndarray
    feature_names: list[str]


class ModelPredictor:
    """Load registered models and generate predictions."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def predict(self, model_name: str, features: pd.DataFrame) -> PredictionOutput:
        model_entry = self.registry.get_model(model_name)
        model = self.registry.load_trained_model(model_name)
        feature_frame = features.reindex(columns=model_entry.feature_names, fill_value=0)
        predictions = model.predict(feature_frame)
        return PredictionOutput(model_name=model_name, predictions=np.asarray(predictions), feature_names=model_entry.feature_names)
