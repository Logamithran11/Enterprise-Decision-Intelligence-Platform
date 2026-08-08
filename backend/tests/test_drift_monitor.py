from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from app.ml.drift_monitor import DriftMonitor


def test_drift_monitor_validates_and_detects(tmp_path: Path) -> None:
    features_dir = tmp_path / "features"
    features_dir.mkdir()
    reports_dir = tmp_path / "reports"

    # Create mock reference features
    ref_df = pd.DataFrame({
        "value": [10.0, 11.0, 12.0, 10.5, 9.5] * 4,
        "segment": ["Enterprise", "SMB"] * 10
    })
    ref_df.to_csv(features_dir / "customer_features.csv", index=False)

    # Create mock feature_schema.json
    schema = {
        "customer_features": [
            {"column": "value", "dtype": "float64"},
            {"column": "segment", "dtype": "object"}
        ]
    }
    (features_dir / "feature_schema.json").write_text(json.dumps(schema), encoding="utf-8")

    monitor = DriftMonitor(features_dir=features_dir, reports_dir=reports_dir)

    # Test case 1: Data matching reference (No Drift)
    inc_df = pd.DataFrame({
        "value": [10.2, 10.8, 11.5, 10.0, 9.8] * 2,
        "segment": ["Enterprise", "SMB"] * 5
    })
    res = monitor.check_drift("customer_features", inc_df)
    assert res["schema_valid"]
    assert not res["drift_detected"]

    # Test case 2: Schema violation (Missing column)
    invalid_schema_df = pd.DataFrame({
        "segment": ["Enterprise", "SMB"] * 5
    })
    res_invalid = monitor.check_drift("customer_features", invalid_schema_df)
    assert not res_invalid["schema_valid"]

    # Test case 3: Data with statistical drift (drift values far out of reference range)
    drifted_df = pd.DataFrame({
        "value": [80.0, 85.0, 90.0, 88.0, 82.0] * 2,
        "segment": ["Enterprise", "SMB"] * 5
    })
    res_drift = monitor.check_drift("customer_features", drifted_df)
    assert res_drift["drift_detected"]
