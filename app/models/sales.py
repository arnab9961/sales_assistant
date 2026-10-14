from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Date, Boolean
from app.database import Base


class ExecutiveSep(Base):
    __tablename__ = "executives_sep"

    id = Column(Integer, primary_key=True, index=True)
    sl_no = Column(Integer, nullable=True)
    name_raw = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    client_target = Column(Integer, nullable=True)
    share_target = Column(Integer, nullable=True)
    target_amount = Column(Float, nullable=True, index=True)
    achieved_amount = Column(Float, nullable=True, index=True)
    dues_amount = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    sold_share_count = Column(Integer, nullable=True)
    new_sales = Column(Float, nullable=True)
    emi = Column(Float, nullable=True)
    total_collection = Column(Float, nullable=True)
    achievement_pct = Column(Float, nullable=True, index=True)
    month = Column(String(20), default="2026-09", index=True)


class ProjectSep(Base):
    __tablename__ = "projects_sep"

    id = Column(Integer, primary_key=True, index=True)
    sl_no = Column(Integer, nullable=True)
    project_name = Column(String(100), nullable=False, index=True)
    clients_qty = Column(Integer, nullable=True)
    share_qty = Column(Integer, nullable=True)
    sale_value = Column(Float, nullable=True)
    total_collected_amount = Column(Float, nullable=True)
    only_sep_collected = Column(Float, nullable=True)
    avg_sale_value = Column(Float, nullable=True)
    avg_collection = Column(Float, nullable=True)
    table_source = Column(String(50), nullable=False, index=True)
    month = Column(String(20), default="2026-09")


class ProjectStatusSep(Base):
    __tablename__ = "project_status_sep"

    id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), nullable=False, index=True)
    clients_qty = Column(Integer, nullable=True)
    share_qty = Column(Integer, nullable=True)
    sale_value = Column(Float, nullable=True)
    collected_amount = Column(Float, nullable=True)
    dues = Column(Float, nullable=True)
    month = Column(String(20), default="2026-09")


class SalesJuly(Base):
    __tablename__ = "sales_july"

    id = Column(Integer, primary_key=True, index=True)
    sl_no = Column(Integer, nullable=True)
    sale_date = Column(Date, nullable=True, index=True)
    client_id = Column(String(50), nullable=True, index=True)
    client_name_raw = Column(String(255), nullable=True)
    client_name = Column(String(255), nullable=True)
    sales_officer_raw = Column(String(255), nullable=True)
    sales_officer = Column(String(255), nullable=True, index=True)
    division = Column(String(100), nullable=True, index=True)
    unit_types = Column(String(50), nullable=True)
    original_price = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    discount_pct = Column(Float, nullable=True)
    sales_price = Column(Float, nullable=True)
    total_deposit = Column(Float, nullable=True)
    dues = Column(Float, nullable=True)
    august_deposited = Column(Float, nullable=True)
    booking_status = Column(String(50), nullable=True, index=True)
    last_deposited_date = Column(String(50), nullable=True)


class DivisionMonthly(Base):
    __tablename__ = "division_monthly"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(20), nullable=False, index=True)
    division = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # new_token_booking, emi, total
    expected_clients = Column(Integer, nullable=True)
    expected_shares = Column(Integer, nullable=True)
    expected_amount = Column(Float, nullable=True)
    invested_clients = Column(Integer, nullable=True)
    invested_shares = Column(Integer, nullable=True)
    collected_amount = Column(Float, nullable=True)
    achievement_pct = Column(Float, nullable=True)


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    issue_type = Column(String(50), nullable=False, index=True)  # missing_value, duplicate, arithmetic_error, cross_check, etc.
    severity = Column(String(20), nullable=False, index=True)  # info, warning, critical
    row_identifier = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
