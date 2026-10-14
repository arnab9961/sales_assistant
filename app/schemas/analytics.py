from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    filter_context: Dict[str, Any]
    total_target: float
    total_achieved: float
    overall_achievement_pct: float
    total_new_sales: float
    total_emi: float
    total_collection: float
    total_executives: int
    executives_at_or_above_100_pct: int
    executives_at_zero: int
    mean_achievement_pct: float
    median_achievement_pct: float
    top_10_concentration_pct: float
    dax_measure_note: str


class ExecutiveRankingItem(BaseModel):
    rank: int
    executive_name: str
    role: str
    target: Optional[float]
    achieved: Optional[float]
    achievement_pct: Optional[float]
    total_collection: Optional[float]


class ProjectRankingItem(BaseModel):
    project_name: str
    sale_value: Optional[float]
    total_collected: Optional[float]
    only_sep_collected: Optional[float]


class RoleAggregationItem(BaseModel):
    role: str
    executive_count: int
    total_target: float
    total_achieved: float
    achievement_pct: float
    total_collection: float


class RankingsResponse(BaseModel):
    top_by_amount: List[ExecutiveRankingItem]
    top_by_achievement_pct: List[ExecutiveRankingItem]
    lowest_project: Optional[ProjectRankingItem]
    by_role_breakdown: List[RoleAggregationItem]


class MetricSummaryStats(BaseModel):
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    sample_size: int


class CorrelationResult(BaseModel):
    variable_x: str
    variable_y: str
    correlation_coefficient: float
    p_value: float
    sample_size: int
    interpretation: str
    causation_warning: str


class ConfidenceIntervalResult(BaseModel):
    metric_name: str
    point_estimate: float
    confidence_level: float
    ci_lower: float
    ci_upper: float
    method: str
    interpretation: str


class MannWhitneyTestResult(BaseModel):
    group1_name: str
    group2_name: str
    group1_median: float
    group2_median: float
    u_statistic: float
    p_value: float
    significant_at_05: bool
    interpretation: str


class StatsResponse(BaseModel):
    transaction_prices: MetricSummaryStats
    discount_percentages: MetricSummaryStats
    target_vs_achieved_correlation: CorrelationResult
    discount_vs_dues_correlation: CorrelationResult
    collection_rate_ci: ConfidenceIntervalResult
    team_leader_vs_exec_test: MannWhitneyTestResult


class DiscountByDivision(BaseModel):
    division: str
    transaction_count: int
    avg_discount_pct: float
    total_discount_amount: float
    avg_dues: float


class DiscountByOfficer(BaseModel):
    officer_name: str
    transaction_count: int
    avg_discount_pct: float
    total_discount_amount: float
    avg_dues: float


class DiscountsResponse(BaseModel):
    overall_avg_discount_pct: float
    overall_total_discount_amount: float
    by_division: List[DiscountByDivision]
    by_sales_officer: List[DiscountByOfficer]
    discount_to_dues_relationship: str
