def test_kpis_endpoint_and_filters(client):
    # Unfiltered KPIs
    resp = client.get("/api/kpis")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_target"] == 46500000.0
    assert data["total_achieved"] == 8249000.0
    assert data["total_collection"] == 10203250.0
    assert data["total_executives"] == 64
    assert data["top_10_concentration_pct"] > 0
    assert "DAX Measure vs Calculated Column" in data["dax_measure_note"]

    # Filtered by role = "Team Leader"
    tl_resp = client.get("/api/kpis?role=Team%20Leader")
    assert tl_resp.status_code == 200
    tl_data = tl_resp.json()
    assert tl_data["filter_context"]["role"] == "Team Leader"
    assert tl_data["total_executives"] < data["total_executives"]
    assert tl_data["total_target"] < data["total_target"]


def test_rankings_endpoint(client):
    resp = client.get("/api/rankings?top_n=5&min_target=50000")
    assert resp.status_code == 200
    data = resp.json()

    # Top by amount
    assert len(data["top_by_amount"]) == 5
    top1 = data["top_by_amount"][0]
    assert top1["rank"] == 1
    assert top1["achieved"] >= data["top_by_amount"][1]["achieved"]

    # Top by achievement %
    assert len(data["top_by_achievement_pct"]) == 5
    for item in data["top_by_achievement_pct"]:
        assert item["target"] >= 50000

    # Lowest project
    assert data["lowest_project"] is not None
    assert "project_name" in data["lowest_project"]

    # By role breakdown
    assert len(data["by_role_breakdown"]) >= 2
    roles = [r["role"] for r in data["by_role_breakdown"]]
    assert "Team Leader" in roles
    assert "Executive" in roles


def test_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Summary stats
    assert data["transaction_prices"]["sample_size"] == 115
    assert data["transaction_prices"]["mean"] > 0
    assert data["discount_percentages"]["mean"] > 0

    # Pearson correlations with mandatory causation warning
    assert "correlation_coefficient" in data["target_vs_achieved_correlation"]
    assert "CORRELATION DOES NOT PROVE CAUSATION" in data["target_vs_achieved_correlation"]["causation_warning"]
    assert "CORRELATION DOES NOT PROVE CAUSATION" in data["discount_vs_dues_correlation"]["causation_warning"]

    # Confidence interval
    ci = data["collection_rate_ci"]
    assert ci["confidence_level"] == 95.0
    assert 0 <= ci["ci_lower"] <= ci["ci_upper"] <= 100

    # Mann-Whitney U test
    mw = data["team_leader_vs_exec_test"]
    assert mw["group1_name"] == "Team Leader"
    assert mw["group2_name"] == "Executive"
    assert "u_statistic" in mw
    assert "p_value" in mw


def test_discounts_endpoint(client):
    resp = client.get("/api/discounts")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_avg_discount_pct"] > 0
    assert data["overall_total_discount_amount"] > 0
    assert len(data["by_division"]) > 0
    assert len(data["by_sales_officer"]) > 0
    assert "discount_to_dues_relationship" in data
