from fastapi import APIRouter
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/api", tags=["Forecasting"])


@router.get("/forecast", response_model=ForecastResponse)
def get_revenue_forecast():
    """Retrieve 3-month revenue collection forecast with backtest evaluations,
    holdout MAE/RMSE comparisons, prediction intervals, and honest low-confidence warnings.
    """
    service = ForecastService()
    return service.generate_forecast()
