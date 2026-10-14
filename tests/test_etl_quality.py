from datetime import date
from app.etl.normalizer import (
    normalize_column_name,
    clean_number,
    clean_int,
    clean_date,
    extract_role_and_name,
)
from app.etl.anonymizer import anonymizer
from app.etl.customer_handler import clean_customer_record
from app.models.sales import ExecutiveSep, ProjectSep, ProjectStatusSep, SalesJuly


def test_column_normalization():
    assert normalize_column_name("Sahre") == "share"
    assert normalize_column_name("Achived") == "achieved"
    assert normalize_column_name("Prevoius") == "previous"
    assert normalize_column_name("Divison") == "division"
    assert normalize_column_name("Orginal Price") == "original_price"
    assert normalize_column_name("Total Deposit up to -26") == "total_deposit"
    assert normalize_column_name("Bking/ EMI") == "booking_status"
    assert normalize_column_name("Lat 5 days") == "last_5_days"
    assert normalize_column_name("Sepaerion") == "separation"


def test_number_cleaner_missing_value_policy():
    # Strict policy: missing is None, never silently 0!
    assert clean_number(None) is None
    assert clean_number("") is None
    assert clean_number("-") is None
    assert clean_number("nan") is None
    assert clean_number("N/A") is None

    # Normal numbers
    assert clean_number("1,500,000") == 1500000.0
    assert clean_number(250000) == 250000.0
    assert clean_number("0") == 0.0
    assert clean_number(0) == 0.0


def test_date_cleaner():
    assert clean_date(None) is None
    assert clean_date("") is None
    assert clean_date("2026-07-02 00:00:00") == date(2026, 7, 2)
    assert clean_date("10.08.26") == date(2026, 8, 10)
    assert clean_date("10/08/2026") == date(2026, 8, 10)


def test_role_extraction():
    name, role = extract_role_and_name("Mehajabin Adita (TL)")
    assert name == "Mehajabin Adita"
    assert role == "Team Leader"

    name, role = extract_role_and_name("Nahid Hasan Emon(C.O)")
    assert name == "Nahid Hasan Emon"
    assert role == "Coordinator"

    name, role = extract_role_and_name("Gazi Mahfuz Kashem(G.L)")
    assert name == "Gazi Mahfuz Kashem"
    assert role == "Group Leader"

    name, role = extract_role_and_name("Sowaib Ahmed")
    assert name == "Sowaib Ahmed"
    assert role == "Executive"


def test_anonymizer_stability():
    anonymizer.reset()
    anon1 = anonymizer.anonymize_executive("Md. Anwarul Islam", "Executive")
    anon2 = anonymizer.anonymize_executive("Md. Anwarul Islam", "Executive")
    assert anon1 == anon2
    assert anon1.startswith("Exec-")

    client1 = anonymizer.anonymize_client("John Doe")
    client2 = anonymizer.anonymize_client("John Doe")
    assert client1 == client2
    assert client1.startswith("Client-")


def test_generic_customer_handler_policy():
    # Valid record
    rec = {
        "name": " Rahim Ahmed ",
        "age": 35,
        "phone": "+8801712345678",
        "registration_date": "2026-01-15",
        "initial_deposit": "50,000",
    }
    cleaned, flags = clean_customer_record(rec)
    assert cleaned["name"] == "Rahim Ahmed"
    assert cleaned["age"] == 35
    assert cleaned["phone"] == "01712345678"
    assert cleaned["registration_date"] == date(2026, 1, 15)
    assert cleaned["initial_deposit"] == 50000.0
    assert len(flags) == 0

    # Incomplete / missing values record
    bad_rec = {
        "name": None,
        "age": "invalid",
        "phone": "123",  # < 10 digits
        "registration_date": "-",
        "initial_deposit": None,  # MUST NOT become 0!
    }
    cleaned_bad, flags_bad = clean_customer_record(bad_rec)
    assert cleaned_bad["name"] == "Unknown"
    assert cleaned_bad["age"] is None
    assert cleaned_bad["phone"] is None
    assert cleaned_bad["registration_date"] is None
    assert cleaned_bad["initial_deposit"] is None  # Preserved as None!
    assert len(flags_bad) == 5


def test_loaded_data_counts_and_cross_checks(db):
    execs = db.query(ExecutiveSep).all()
    assert len(execs) == 64, f"Expected 64 executives in Sep sheet, found {len(execs)}"

    # Check sum of targets = 46,500,000
    total_target = sum(e.target_amount or 0 for e in execs)
    assert total_target == 46500000.0

    # Check sum of achieved = 8,249,000
    total_achieved = sum(e.achieved_amount or 0 for e in execs)
    assert total_achieved == 8249000.0

    # Check projects
    projects = db.query(ProjectSep).all()
    assert len(projects) > 0

    # Check project status separation (Full paid, EMI, Token, Hold, Cancel)
    statuses = db.query(ProjectStatusSep).all()
    assert len(statuses) == 5

    # Check sales July (Discount Price)
    sales = db.query(SalesJuly).all()
    assert len(sales) == 115, f"Expected 115 July sales records, found {len(sales)}"


def test_quality_api_endpoint(client):
    response = client.get("/api/quality")
    assert response.status_code == 200
    data = response.json()

    assert "overall_status" in data
    assert "missing_value_policy" in data
    assert "NEVER silently replace missing sales/money with 0" in data["missing_value_policy"]
    assert len(data["tables"]) >= 3
    assert len(data["arithmetic_checks"]) >= 2
    assert len(data["sheet_cross_checks"]) >= 4

    # Verify that the 500 BDT aggregate dues discrepancy was caught and documented
    dues_cross_check = next(
        (c for c in data["sheet_cross_checks"] if "Aggregate Dues" in c["metric"]), None
    )
    assert dues_cross_check is not None
    assert dues_cross_check["matches"] is False
    assert dues_cross_check["discrepancy"] == 500.0
