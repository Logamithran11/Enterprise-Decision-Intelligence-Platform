from __future__ import annotations

import json
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score

from app.ml.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class CustomerSegmentationPaths:
    features_dir: Path
    trained_models_dir: Path
    reports_dir: Path
    exports_dir: Path

    def ensure(self) -> None:
        self.features_dir.mkdir(parents=True, exist_ok=True)
        self.trained_models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class SegmentationArtifact:
    model_name: str
    path: str
    silhouette: float
    davies_bouldin: float
    description: str


class CustomerSegmentationService:
    """Segment customers into behavioral clusters using K-Means and PCA."""

    def __init__(self, paths: CustomerSegmentationPaths) -> None:
        self.paths = paths
        self.paths.ensure()
        self.registry = ModelRegistry(self.paths.trained_models_dir)

    def load_customer_features(self) -> pd.DataFrame:
        features_path = self.paths.features_dir / "customer_features.csv"
        if not features_path.exists():
            raise FileNotFoundError(f"Missing customer features dataset: {features_path}")
        return pd.read_csv(features_path)

    def prepare_segmentation_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        # Use standard scaled features for clustering
        cols_to_use = [
            "annual_revenue_standard_scaled",
            "total_revenue_standard_scaled",
            "average_order_value_standard_scaled",
            "customer_activity_score_standard_scaled"
        ]
        
        # Verify columns exist, fallback to their unscaled versions (scaled on the fly) if not
        fallback_cols = ["annual_revenue", "total_revenue", "average_order_value", "customer_activity_score"]
        available_cols = []
        
        for col in cols_to_use:
            if col in df.columns:
                available_cols.append(col)
                
        if len(available_cols) < 2:
            # Scale on the fly
            X = df[[c for c in fallback_cols if c in df.columns]].copy()
            for c in X.columns:
                mean = X[c].mean()
                std = X[c].std()
                X[f"{c}_standard_scaled"] = (X[c] - mean) / max(std, 1e-5)
            available_cols = [f"{c}_standard_scaled" for c in X.columns]
            df = pd.concat([df, X[available_cols]], axis=1)
            
        X = df[available_cols].fillna(0)
        return X, available_cols

    def _determine_persona(self, centroid: pd.Series) -> str:
        # Centroid values are scaled. High or Low relative to 0.0
        rev = centroid.get("annual_revenue_standard_scaled", 0.0)
        activity = centroid.get("customer_activity_score_standard_scaled", 0.0)
        val = centroid.get("total_revenue_standard_scaled", 0.0)

        if rev > 0.5 and activity > 0.5:
            return "Enterprise Champions"
        elif val > 0.2 and activity < -0.3:
            return "At-Risk High-Value"
        elif rev < -0.2 and activity > 0.4:
            return "Active Growth SMB"
        else:
            return "Stable Mid-Market"

    def train_and_register(self, n_clusters: int = 4) -> tuple[SegmentationArtifact, pd.DataFrame]:
        df = self.load_customer_features()
        X, feature_cols = self.prepare_segmentation_data(df)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        silhouette = float(silhouette_score(X, labels))
        davies_bouldin = float(davies_bouldin_score(X, labels))

        # Assign personas dynamically based on centroids
        centroids = pd.DataFrame(kmeans.cluster_centers_, columns=feature_cols)
        cluster_personas = {}
        for cluster_id in range(n_clusters):
            centroid = centroids.iloc[cluster_id]
            persona = self._determine_persona(centroid)
            # Ensure unique personas if duplicates arise by appending cluster index
            if persona in cluster_personas.values():
                persona = f"{persona} (Group {cluster_id + 1})"
            cluster_personas[cluster_id] = persona

        # Map to customer dataset
        df["cluster_id"] = labels
        df["persona"] = df["cluster_id"].map(cluster_personas)

        # PCA for 2D visualization
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X)
        df["pca_x"] = X_pca[:, 0]
        df["pca_y"] = X_pca[:, 1]

        # Register K-Means model
        registered = self.registry.register_model(
            name="customer_segmentation_model",
            model=kmeans,
            metrics={"silhouette": silhouette, "davies_bouldin": davies_bouldin},
            feature_names=feature_cols,
            model_type="kmeans_clustering",
            description="Clustering model categorizing customers based on scale and activity."
        )

        artifact = SegmentationArtifact(
            model_name=registered.name,
            path=registered.model_path,
            silhouette=silhouette,
            davies_bouldin=davies_bouldin,
            description=registered.description
        )

        # Save cluster personas config report
        persona_report = {
            str(k): {
                "persona_name": v,
                "centroid": centroids.iloc[k].to_dict()
            } for k, v in cluster_personas.items()
        }
        (self.paths.reports_dir / "customer_persona_definitions.json").write_text(json.dumps(persona_report, indent=2), encoding="utf-8")

        # Save segments data
        export_df = df[["customer_id", "cluster_id", "persona", "pca_x", "pca_y", "annual_revenue", "customer_activity_score"]].copy()
        export_df.to_csv(self.paths.exports_dir / "customer_segments.csv", index=False)

        # Plot PCA clusters
        self._generate_pca_plot(df, n_clusters, cluster_personas)

        return artifact, export_df

    def _generate_pca_plot(self, df: pd.DataFrame, n_clusters: int, personas: dict[int, str]) -> None:
        figure, ax = plt.subplots(figsize=(10, 8))
        
        for cluster_id in range(n_clusters):
            cluster_data = df[df["cluster_id"] == cluster_id]
            ax.scatter(
                cluster_data["pca_x"],
                cluster_data["pca_y"],
                label=personas[cluster_id],
                alpha=0.8,
                edgecolors="none"
            )
            
        ax.set_title("Customer Segmentation PCA Visualization")
        ax.set_xlabel("PCA Dimension 1")
        ax.set_ylabel("PCA Dimension 2")
        ax.legend(title="Customer Personas", bbox_to_anchor=(1.05, 1), loc="upper left")
        figure.tight_layout()
        
        figure.savefig(self.paths.exports_dir / "customer_segments_pca_plot.png", dpi=180, bbox_inches="tight")
        plt.close(figure)
