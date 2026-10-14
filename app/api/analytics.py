from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_ro_db
from app.schemas.analytics import (
    DiscountsResponse,
    KPIResponse,
    RankingsResponse,
    StatsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api", tags=["Analytics & Statistics"])


@router.get("/kpis", response_model=KPIResponse)
def get_kpis(
    role: Optional[str] = Query(None, description="Filter by role tag (e.g. 'Team Leader', 'Executive', 'Coordinator')"),
    month: Optional[str] = Query("2026-09", description="Filter by month (e.g. '2026-09')"),
    project: Optional[str] = Query(None, description="Filter by project name"),
    db: Session = Depends(get_ro_db),
):
    """Retrieve dynamic aggregated KPIs behaving as DAX measures across the specified filter context."""
    service = AnalyticsService(db)
    return service.get_kpis(role=role, month=month, project=project)


@router.get("/rankings", response_model=RankingsResponse)
def get_rankings(
    top_n: int = Query(10, ge=1, le=100, description="Number of top executives to return"),
    min_target: float = Query(50000.0, ge=0.0, description="Minimum target threshold for % ranking"),
    db: Session = Depends(get_ro_db),
):
    """Retrieve top executives by volume and achievement %, lowest project, and by-role breakdown."""
    service = AnalyticsService(db)
    return service.get_rankings(top_n=top_n, min_target=min_target)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_ro_db)):
    """Retrieve summary statistics, Pearson correlations with mandatory causation warning,
    Wilson confidence interval, and Mann-Whitney U test between Team Leaders and Executives.
    """
    service = AnalyticsService(db)
    return service.get_stats()


@router.get("/discounts", response_model=DiscountsResponse)
def get_discounts(db: Session = Depends(get_ro_db)):
    """Retrieve discount percentage breakdown across divisions and sales officers, and relationship to dues."""
    service = AnalyticsService(db)
    return service.get_discounts()
