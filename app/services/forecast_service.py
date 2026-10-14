import math
from typing import List, Tuple
import numpy as np

from app.schemas.forecast import (
    ForecastPoint,
    ForecastResponse,
    HistoricalPoint,
    ModelEvaluation,
)


def get_historical_monthly_data() -> List[HistoricalPoint]:
    """Extract verifiable historical monthly collection data points from Project Wise Collection.(Only Sep).xlsx."""
    return [
        HistoricalPoint(
            month="2026-01",
            amount=5560000.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Sheet 'Only Jan 26', Row 11 Total",
            is_differenced=False,
            notes="Direct monthly standalone collection reported for January 2026",
        ),
        HistoricalPoint(
            month="2026-02",
            amount=4685000.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Sheet 'Only Feb 26', Row 11 Total",
            is_differenced=False,
            notes="Direct monthly standalone collection reported for February 2026",
        ),
        HistoricalPoint(
            month="2026-03",
            amount=11646000.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Sheet '01.04.26' / 'Sheet2', Row 12 Total",
            is_differenced=False,
            notes="Direct standalone collection for March 2026",
        ),
        HistoricalPoint(
            month="2026-04",
            amount=9277700.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Differenced cumulative snapshot (09.05.26 minus 25.03.26)",
            is_differenced=True,
            notes="Differenced cumulative collection (116,323,375 - 97,767,975 = 18,555,400) apportioned evenly across April and early May",
        ),
        HistoricalPoint(
            month="2026-05",
            amount=9277700.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Differenced cumulative snapshot (09.05.26 minus 25.03.26)",
            is_differenced=True,
            notes="Differenced cumulative collection apportioned across April and May",
        ),
        HistoricalPoint(
            month="2026-06",
            amount=12329736.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Differenced cumulative snapshot (21.07.26 minus 09.05.26)",
            is_differenced=True,
            notes="Differenced cumulative collection (140,982,848 - 116,323,375 = 24,659,473) apportioned evenly across June and July",
        ),
        HistoricalPoint(
            month="2026-07",
            amount=12329737.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Differenced cumulative snapshot (21.07.26 minus 09.05.26)",
            is_differenced=True,
            notes="Differenced cumulative collection apportioned across June and July; cross-validated with Discount Price July sales (9.35M deposit + 2.53M Aug)",
        ),
        HistoricalPoint(
            month="2026-08",
            amount=16551090.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Sheet 'Aug-26 (4)', Row 12 'Only Aug-26 Collected'",
            is_differenced=False,
            notes="Direct standalone collection recorded for August 2026",
        ),
        HistoricalPoint(
            month="2026-09",
            amount=11495750.0,
            source_sheet="Project Wise Collection.(Only Sep).xlsx -> Sheet 'Sep-26', Row 13 'Only Sep-26 Collected'",
            is_differenced=False,
            notes="Direct standalone collection recorded for September 2026",
        ),
    ]


class ForecastService:
    def __init__(self):
        self.history = get_historical_monthly_data()

    def _naive_forecast(self, train: List[float], steps: int) -> List[float]:
        last_val = train[-1]
        return [last_val] * steps

    def _ma3_forecast(self, train: List[float], steps: int) -> List[float]:
        # 3-period moving average
        history = list(train)
        preds = []
        for _ in range(steps):
            window = history[-3:] if len(history) >= 3 else history
            nxt = float(np.mean(window))
            preds.append(nxt)
            history.append(nxt)
        return preds

    def _ses_forecast(self, train: List[float], steps: int, alpha: float = 0.4) -> List[float]:
        # Simple Exponential Smoothing
        smoothed = [train[0]]
        for t in range(1, len(train)):
            st = alpha * train[t] + (1 - alpha) * smoothed[-1]
            smoothed.append(st)
        last_level = smoothed[-1]
        return [last_level] * steps

    def _evaluate(self, actual: List[float], predicted: List[float]) -> Tuple[float, float]:
        errors = [a - p for a, p in zip(actual, predicted)]
        mae = float(np.mean([abs(e) for e in errors]))
        rmse = float(np.sqrt(np.mean([e**2 for e in errors])))
        return mae, rmse

    def generate_forecast(self) -> ForecastResponse:
        data = self.history
        values = [p.amount for p in data]
        n = len(values)

        # Holdout validation on last 2 months: Aug (idx 7) and Sep (idx 8)
        train_idx = 7
        train = values[:train_idx]
        holdout = values[train_idx:]
        holdout_steps = len(holdout)

        # 1. Naive Model
        naive_preds = self._naive_forecast(train, holdout_steps)
        naive_mae, naive_rmse = self._evaluate(holdout, naive_preds)

        # 2. Moving Average (MA-3)
        ma_preds = self._ma3_forecast(train, holdout_steps)
        ma_mae, ma_rmse = self._evaluate(holdout, ma_preds)

        # 3. Simple Exponential Smoothing (SES, alpha=0.4)
        ses_preds = self._ses_forecast(train, holdout_steps, alpha=0.4)
        ses_mae, ses_rmse = self._evaluate(holdout, ses_preds)

        model_evals = [
            ModelEvaluation(
                model_name="Naive Baseline (Last Value)",
                mae=round(naive_mae, 2),
                rmse=round(naive_rmse, 2),
                description="Carries forward the last observed monthly revenue point directly (Y_t+1 = Y_t).",
            ),
            ModelEvaluation(
                model_name="3-Month Moving Average (MA-3)",
                mae=round(ma_mae, 2),
                rmse=round(ma_rmse, 2),
                description="Unweighted average of the preceding 3 months to dampen short-term monthly volatility.",
            ),
            ModelEvaluation(
                model_name="Simple Exponential Smoothing (SES, alpha=0.4)",
                mae=round(ses_mae, 2),
                rmse=round(ses_rmse, 2),
                description="Exponentially decayed weighting favoring recent collection velocity.",
            ),
        ]

        # Select best model (lowest RMSE)
        best_eval = min(model_evals, key=lambda m: m.rmse)
        best_name = best_eval.model_name

        # Forecast next 3 months using best model trained on full dataset
        forecast_steps = 3
        forecast_months = ["2026-10", "2026-11", "2026-12"]

        if "Naive" in best_name:
            full_preds = self._naive_forecast(values, forecast_steps)
        elif "Moving Average" in best_name:
            full_preds = self._ma3_forecast(values, forecast_steps)
        else:
            full_preds = self._ses_forecast(values, forecast_steps, alpha=0.4)

        # Prediction intervals (95% CI): pred +- 1.96 * RMSE * sqrt(h)
        base_rmse = best_eval.rmse
        forecast_points = []
        for h, (m, pred) in enumerate(zip(forecast_months, full_preds), start=1):
            margin = 1.96 * base_rmse * math.sqrt(h)
            lower = max(0.0, pred - margin)
            upper = pred + margin
            forecast_points.append(
                ForecastPoint(
                    month=m,
                    forecast_amount=round(pred, 2),
                    lower_bound_95=round(lower, 2),
                    upper_bound_95=round(upper, 2),
                )
            )

        confidence_explanation = (
            f"LOW CONFIDENCE WARNING: Dataset provides only {n} monthly points (Jan 2026 - Sep 2026). "
            "Statistical rule of thumb requires at least 12-24 observations to fit seasonality (SARIMA/Prophet) "
            "or detect long-term macro trends. This projection represents an operational baseline. "
            "Do not oversell accuracy or make irreversible capital commitments without observing full annual cycles."
        )

        methodology_doc = (
            "Forecasting Methodology:\n"
            "1. True Historical Extraction: Standalone monthly collection records extracted directly from sheets "
            "'Only Jan 26', 'Only Feb 26', 'Sheet2' (March), 'Aug-26 (4)', and 'Sep-26'. Intermediate periods "
            "(April-May and June-July) derived by differencing cumulative 'Up to' snapshots (09.05.26 and 21.07.26).\n"
            "2. Holdout Backtesting: Evaluated on an out-of-sample holdout (August & September 2026) across three "
            "parsimonious models (Naive, MA-3, SES). Selected model with lowest RMSE on unseen data.\n"
            "3. Prediction Intervals: 95% uncertainty bands computed scaling with horizon step (sqrt(h)) "
            "accounting for compounding multi-step variance."
        )

        return ForecastResponse(
            confidence_status="LOW_CONFIDENCE",
            confidence_reason=confidence_explanation,
            sample_size=n,
            historical_series=data,
            model_evaluations=model_evals,
            best_model=best_name,
            forecast_next_3_months=forecast_points,
            methodology_documentation=methodology_doc,
        )
