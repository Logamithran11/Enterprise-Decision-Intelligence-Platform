from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

import joblib


@dataclass(frozen=True, slots=True)
class RegisteredModel:
    name: str
    model_path: str
    metrics: dict[str, float]
    feature_names: list[str]
    trained_at: str
    model_type: str
    description: str


class ModelRegistry:
    """Persist and retrieve trained ML models with metadata."""

    def __init__(self, registry_dir: Path) -> None:
        self.registry_dir = registry_dir
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.registry_dir / "model_registry.json"

    def _load_registry(self) -> list[dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _save_registry(self, entries: list[dict[str, Any]]) -> None:
        self.registry_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def register_model(
        self,
        name: str,
        model: Any,
        metrics: dict[str, float],
        feature_names: list[str],
        model_type: str,
        description: str,
    ) -> RegisteredModel:
        model_path = self.registry_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        entry = RegisteredModel(
            name=name,
            model_path=str(model_path),
            metrics=metrics,
            feature_names=feature_names,
            trained_at=datetime.now(timezone.utc).isoformat(),
            model_type=model_type,
            description=description,
        )
        registry = self._load_registry()
        registry = [existing for existing in registry if existing.get("name") != name]
        registry.append(asdict(entry))
        self._save_registry(registry)
        return entry

    def list_models(self) -> list[RegisteredModel]:
        return [RegisteredModel(**entry) for entry in self._load_registry()]

    def get_model(self, name: str) -> RegisteredModel:
        for entry in self._load_registry():
            if entry.get("name") == name:
                return RegisteredModel(**entry)
        raise KeyError(f"Model {name!r} not found in registry")

    def load_trained_model(self, name: str) -> Any:
        model_entry = self.get_model(name)
        return joblib.load(model_entry.model_path)
