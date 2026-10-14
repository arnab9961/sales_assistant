def test_dashboard_ui_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text

    assert "AI Sales Operations Assistant" in html
    assert "Sunset Kuakata" in html
    assert "kpiTarget" in html
    assert "targetAchievedChart" in html
    assert "histogramChart" in html
    assert "forecastChart" in html
    assert "leadForm" in html
    assert "submitLeadBtn" in html
    assert "crossCheckTableBody" in html
