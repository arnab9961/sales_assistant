def test_list_whitelisted_queries(client):
    resp = client.get("/api/sql")
    assert resp.status_code == 200
    data = resp.json()
    assert "whitelisted_queries" in data
    queries = data["whitelisted_queries"]
    assert "total_sales_by_project" in queries
    assert "monthly_sales_mom" in queries
    assert "top_customers_by_deposit" in queries
    assert "regional_division_performance" in queries


def test_run_total_sales_by_project(client):
    resp = client.get("/api/sql/total_sales_by_project?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_name"] == "total_sales_by_project"
    assert "columns" in data
    assert len(data["data"]) > 0
    first_row = data["data"][0]
    assert "project_name" in first_row
    assert "total_collected_sep" in first_row


def test_run_monthly_sales_mom(client):
    resp = client.get("/api/sql/monthly_sales_mom")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query_name"] == "monthly_sales_mom"
    assert "data" in data
    assert len(data["data"]) > 0


def test_run_top_customers_by_deposit_pagination(client):
    resp = client.get("/api/sql/top_customers_by_deposit?limit=5&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 5
    assert data["data"][0]["total_deposit"] >= data["data"][1]["total_deposit"]


def test_run_regional_division_performance(client):
    resp = client.get("/api/sql/regional_division_performance")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) > 0
    divisions = [r["division"] for r in data["data"]]
    assert "Corporate" in divisions


def test_unwhitelisted_query_rejected(client):
    resp = client.get("/api/sql/drop_all_tables")
    assert resp.status_code == 404
    assert "not found or not permitted" in resp.json()["detail"]

    # Attempting SQL injection in query name
    injection_resp = client.get("/api/sql/SELECT%20*%20FROM%20users")
    assert injection_resp.status_code == 404
