from typing import List, Optional
from pydantic import BaseModel, Field


class HistoricalPoint(BaseModel):
    month: str  # e.g. "2026-01"
    amount: float
    source_sheet: str
    is_differenced: bool
    notes: Optional[str] = None


class ForecastPoint(BaseModel):
    month: str  # e.g. "2026-10"
    forecast_amount: float
    lower_bound_95: float
    upper_bound_95: float


class ModelEvaluation(BaseModel):
    model_name: str
    mae: float
    rmse: float
    description: str


class ForecastResponse(BaseModel):
    confidence_status: str  # "LOW_CONFIDENCE"
    confidence_reason: str
    sample_size: int
    historical_series: List[HistoricalPoint]
    model_evaluations: List[ModelEvaluation]
    best_model: str
    forecast_next_3_months: List[ForecastPoint]
    methodology_documentation: str
