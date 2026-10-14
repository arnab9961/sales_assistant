def test_forecast_endpoint(client):
    resp = client.get("/api/forecast")
    assert resp.status_code == 200
    data = resp.json()

    # Honest low confidence check
    assert data["confidence_status"] == "LOW_CONFIDENCE"
    assert data["sample_size"] == 9
    assert "fewer than ~12" in data["confidence_reason"] or "only 9" in data["confidence_reason"]

    # History checks
    history = data["historical_series"]
    assert len(history) == 9
    months = [h["month"] for h in history]
    assert months == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
    ]
    # Check that differenced cumulative snapshots are documented
    differenced = [h for h in history if h["is_differenced"]]
    assert len(differenced) >= 4

    # Baselines and evaluations
    evals = data["model_evaluations"]
    assert len(evals) == 3
    model_names = [m["model_name"] for m in evals]
    assert any("Naive" in n for n in model_names)
    assert any("Moving Average" in n for n in model_names)
    assert any("Simple Exponential Smoothing" in n for n in model_names)

    for ev in evals:
        assert ev["mae"] > 0
        assert ev["rmse"] > 0

    assert data["best_model"] in model_names

    # 3-Month forecast
    forecast_points = data["forecast_next_3_months"]
    assert len(forecast_points) == 3
    assert [p["month"] for p in forecast_points] == ["2026-10", "2026-11", "2026-12"]

    for p in forecast_points:
        assert p["forecast_amount"] > 0
        assert p["lower_bound_95"] <= p["forecast_amount"] <= p["upper_bound_95"]
