"""Weighted fusion of independent risk components. PLAN §18."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from veripay_common.enums import RiskBand


class RiskComponent(BaseModel):
    component: str = Field(min_length=1)
    score: float = Field(ge=0, le=100)
    weight: float = Field(gt=0, le=1)
    available: bool = True
    reason_code: str | None = None


class FusionRequest(BaseModel):
    transaction_id: str = Field(min_length=1)
    components: list[RiskComponent] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_weights(self) -> FusionRequest:
        if sum(component.weight for component in self.components) <= 0:
            raise ValueError("At least one positive component weight is required")
        return self


class FusionResponse(BaseModel):
    transaction_id: str
    unified_score: int = Field(ge=0, le=100)
    band: RiskBand
    components: list[RiskComponent]


def fuse_risk(request: FusionRequest) -> FusionResponse:
    """Redistribute unavailable weights across available components."""
    available = [component for component in request.components if component.available]
    if not available:
        score = 100
    else:
        total_weight = sum(component.weight for component in available)
        weighted_score = sum(component.score * component.weight for component in available)
        score = round(weighted_score / total_weight)
    band = RiskBand.APPROVE if score < 40 else RiskBand.VERIFY if score < 70 else RiskBand.BLOCK
    return FusionResponse(
        transaction_id=request.transaction_id,
        unified_score=score,
        band=band,
        components=request.components,
    )
