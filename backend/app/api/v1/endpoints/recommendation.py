from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import RoleChecker, TokenData, get_current_user_claims
from app.ml.recommendation_engine import BusinessRecommendationService

router = APIRouter()

project_root = Path(__file__).resolve().parents[5]
reports_dir = project_root / "reports"
exports_dir = project_root / "exports"

all_roles = ["admin", "executive", "manager", "analyst"]
write_roles = ["admin", "executive", "manager"]


@router.get("", summary="Get structured business recommendations")
def get_recommendations(
    claims: TokenData = Depends(RoleChecker(all_roles))
) -> list[dict[str, Any]]:
    try:
        service = BusinessRecommendationService(exports_dir=exports_dir, reports_dir=reports_dir)
        recs = service.generate_recommendations()
        return [
            {
                "business_insight": r.business_insight,
                "root_cause": r.root_cause,
                "recommendation": r.recommendation,
                "confidence": r.confidence,
                "expected_impact": r.expected_impact,
                "priority": r.priority,
                "estimated_roi": r.estimated_roi,
                "estimated_time_to_benefit": r.estimated_time_to_benefit
            } for r in recs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", summary="Trigger dynamic recommendations regeneration")
def trigger_generation(
    claims: TokenData = Depends(RoleChecker(write_roles))
) -> dict[str, str]:
    try:
        service = BusinessRecommendationService(exports_dir=exports_dir, reports_dir=reports_dir)
        service.generate_recommendations()
        return {"status": "success", "message": "Recommendations regenerated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
