from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnMissingStat(BaseModel):
    column_name: str
    missing_count: int
    total_count: int
    missing_pct: float


class TableQualitySummary(BaseModel):
    table_name: str
    total_rows: int
    missing_stats: List[ColumnMissingStat]
    duplicate_count: int
    zero_or_null_targets: int


class ArithmeticCheckResult(BaseModel):
    rule: str
    passed: bool
    failed_rows_count: int
    discrepancy_details: List[str]


class CrossCheckResult(BaseModel):
    sheet_or_table: str
    metric: str
    computed_sum: float
    sheet_total_row: float
    discrepancy: float
    matches: bool
    notes: Optional[str] = None


class QualityReportResponse(BaseModel):
    overall_status: str  # "PASS" | "WARNING" | "FAIL"
    missing_value_policy: str
    tables: List[TableQualitySummary]
    arithmetic_checks: List[ArithmeticCheckResult]
    sheet_cross_checks: List[CrossCheckResult]
    inter_table_comparisons: List[Dict[str, Any]]
    total_logged_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[Dict[str, Any]]
