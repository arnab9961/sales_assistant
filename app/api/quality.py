from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_ro_db
from app.schemas.quality import QualityReportResponse
from app.services.quality_service import QualityService

router = APIRouter(prefix="/api", tags=["Data Quality"])


@router.get("/quality", response_model=QualityReportResponse)
def get_data_quality_report(db: Session = Depends(get_ro_db)):
    """Data Quality audit report verifying missing values, duplicates, arithmetic consistency,
    and cross-checks against Excel summary rows.
    """
    service = QualityService(db)
    return service.get_report()
