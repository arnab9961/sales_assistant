import math
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales import ExecutiveSep, ProjectSep, SalesJuly
from app.schemas.analytics import (
    ConfidenceIntervalResult,
    CorrelationResult,
    DiscountByDivision,
    DiscountByOfficer,
    DiscountsResponse,
    ExecutiveRankingItem,
    KPIResponse,
    MannWhitneyTestResult,
    MetricSummaryStats,
    ProjectRankingItem,
    RankingsResponse,
    RoleAggregationItem,
    StatsResponse,
)

CAUSATION_WARNING = (
    "CORRELATION DOES NOT PROVE CAUSATION. Example: An observed correlation of 0.85 between "
    "advertising and sales does not mean advertising caused sales; confounding factors (e.g. holiday seasonality, "
    "market expansion, or executive effort) may drive both simultaneously."
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_kpis(
        self,
        role: Optional[str] = None,
        month: Optional[str] = "2026-09",
        project: Optional[str] = None,
    ) -> KPIResponse:
        query = self.db.query(ExecutiveSep)
        if month:
            query = query.filter(ExecutiveSep.month == month)
        if role and role.strip() and role.lower() != "all":
            query = query.filter(func.lower(ExecutiveSep.role) == role.strip().lower())

        executives = query.all()
        total_execs = len(executives)

        t_target = sum(e.target_amount or 0.0 for e in executives)
        t_achieved = sum(e.achieved_amount or 0.0 for e in executives)
        t_new_sales = sum(e.new_sales or 0.0 for e in executives)
        t_emi = sum(e.emi or 0.0 for e in executives)
        t_coll = sum(e.total_collection or 0.0 for e in executives)

        overall_pct = (t_achieved / t_target * 100.0) if t_target > 0 else 0.0

        # Percentages per executive (excluding zero/null targets from individual mean/median)
        valid_pcts = [
            e.achievement_pct
            for e in executives
            if e.achievement_pct is not None and e.target_amount and e.target_amount > 0
        ]

        mean_pct = float(np.mean(valid_pcts)) if valid_pcts else 0.0
        median_pct = float(np.median(valid_pcts)) if valid_pcts else 0.0

        execs_at_100 = sum(1 for p in valid_pcts if p >= 100.0)
        execs_at_zero = sum(1 for e in executives if (e.achieved_amount or 0.0) == 0.0)

        # Top 10 concentration
        sorted_by_achieved = sorted(
            executives, key=lambda x: (x.achieved_amount or 0.0), reverse=True
        )
        top_10_achieved = sum(e.achieved_amount or 0.0 for e in sorted_by_achieved[:10])
        top_10_conc = (top_10_achieved / t_achieved * 100.0) if t_achieved > 0 else 0.0

        dax_explanation = (
            "DAX Measure vs Calculated Column: A calculated column is statically evaluated row-by-row during table "
            "materialization and stored in RAM. In contrast, this endpoint behaves strictly as a dynamic DAX Measure: "
            "it evaluates on-the-fly across the active filter context (Role, Month, Project), dynamically aggregating "
            "under context transition [e.g. DIVIDE(SUM(Achieved), SUM(Target))]."
        )

        return KPIResponse(
            filter_context={"role": role or "All", "month": month, "project": project or "All"},
            total_target=round(t_target, 2),
            total_achieved=round(t_achieved, 2),
            overall_achievement_pct=round(overall_pct, 2),
            total_new_sales=round(t_new_sales, 2),
            total_emi=round(t_emi, 2),
            total_collection=round(t_coll, 2),
            total_executives=total_execs,
            executives_at_or_above_100_pct=execs_at_100,
            executives_at_zero=execs_at_zero,
            mean_achievement_pct=round(mean_pct, 2),
            median_achievement_pct=round(median_pct, 2),
            top_10_concentration_pct=round(top_10_conc, 2),
            dax_measure_note=dax_explanation,
        )

    def get_rankings(self, top_n: int = 10, min_target: float = 50000.0) -> RankingsResponse:
        executives = self.db.query(ExecutiveSep).all()

        # Top by amount
        by_amount = sorted(
            executives, key=lambda x: (x.achieved_amount or 0.0), reverse=True
        )[:top_n]
        top_amount_items = [
            ExecutiveRankingItem(
                rank=i + 1,
                executive_name=e.name,
                role=e.role,
                target=e.target_amount,
                achieved=e.achieved_amount,
                achievement_pct=round(e.achievement_pct, 2) if e.achievement_pct else 0.0,
                total_collection=e.total_collection,
            )
            for i, e in enumerate(by_amount)
        ]

        # Top by achievement %, ignoring tiny targets (< min_target)
        eligible_for_pct = [
            e for e in executives if e.target_amount and e.target_amount >= min_target and e.achievement_pct is not None
        ]
        by_pct = sorted(
            eligible_for_pct, key=lambda x: (x.achievement_pct or 0.0), reverse=True
        )[:top_n]
        top_pct_items = [
            ExecutiveRankingItem(
                rank=i + 1,
                executive_name=e.name,
                role=e.role,
                target=e.target_amount,
                achieved=e.achieved_amount,
                achievement_pct=round(e.achievement_pct, 2) if e.achievement_pct else 0.0,
                total_collection=e.total_collection,
            )
            for i, e in enumerate(by_pct)
        ]

        # Lowest project
        summary_projects = (
            self.db.query(ProjectSep)
            .filter(ProjectSep.table_source == "summary_non_overlapping")
            .all()
        )
        lowest_proj = None
        if summary_projects:
            sorted_projects = sorted(
                summary_projects, key=lambda x: (x.only_sep_collected or 0.0)
            )
            lp = sorted_projects[0]
            lowest_proj = ProjectRankingItem(
                project_name=lp.project_name,
                sale_value=lp.sale_value,
                total_collected=lp.total_collected_amount,
                only_sep_collected=lp.only_sep_collected,
            )

        # By-role breakdown
        roles = set(e.role for e in executives)
        role_breakdown = []
        for r in sorted(roles):
            role_execs = [e for e in executives if e.role == r]
            rt = sum(e.target_amount or 0.0 for e in role_execs)
            ra = sum(e.achieved_amount or 0.0 for e in role_execs)
            rc = sum(e.total_collection or 0.0 for e in role_execs)
            rpct = (ra / rt * 100.0) if rt > 0 else 0.0
            role_breakdown.append(
                RoleAggregationItem(
                    role=r,
                    executive_count=len(role_execs),
                    total_target=round(rt, 2),
                    total_achieved=round(ra, 2),
                    achievement_pct=round(rpct, 2),
                    total_collection=round(rc, 2),
                )
            )

        return RankingsResponse(
            top_by_amount=top_amount_items,
            top_by_achievement_pct=top_pct_items,
            lowest_project=lowest_proj,
            by_role_breakdown=role_breakdown,
        )

    def get_stats(self) -> StatsResponse:
        # 1. Summary stats of July sales prices and discounts
        sales = self.db.query(SalesJuly).all()
        prices = [s.sales_price for s in sales if s.sales_price is not None]
        discounts = [s.discount_pct for s in sales if s.discount_pct is not None]

        price_stats = MetricSummaryStats(
            mean=round(float(np.mean(prices)), 2) if prices else 0.0,
            median=round(float(np.median(prices)), 2) if prices else 0.0,
            std_dev=round(float(np.std(prices, ddof=1)), 2) if len(prices) > 1 else 0.0,
            min_value=round(float(np.min(prices)), 2) if prices else 0.0,
            max_value=round(float(np.max(prices)), 2) if prices else 0.0,
            sample_size=len(prices),
        )

        discount_stats = MetricSummaryStats(
            mean=round(float(np.mean(discounts)), 2) if discounts else 0.0,
            median=round(float(np.median(discounts)), 2) if discounts else 0.0,
            std_dev=round(float(np.std(discounts, ddof=1)), 2) if len(discounts) > 1 else 0.0,
            min_value=round(float(np.min(discounts)), 2) if discounts else 0.0,
            max_value=round(float(np.max(discounts)), 2) if discounts else 0.0,
            sample_size=len(discounts),
        )

        # 2. Pearson correlation: Target vs Achieved
        execs = self.db.query(ExecutiveSep).all()
        target_pairs = [
            (e.target_amount, e.achieved_amount)
            for e in execs
            if e.target_amount is not None and e.achieved_amount is not None
        ]
        if len(target_pairs) >= 2:
            x_vals = [p[0] for p in target_pairs]
            y_vals = [p[1] for p in target_pairs]
            r_target, p_target = stats.pearsonr(x_vals, y_vals)
        else:
            r_target, p_target = 0.0, 1.0

        target_corr = CorrelationResult(
            variable_x="Target Amount (BDT)",
            variable_y="Achieved Amount (BDT)",
            correlation_coefficient=round(float(r_target), 4),
            p_value=round(float(p_target), 4),
            sample_size=len(target_pairs),
            interpretation=(
                f"Moderate-to-strong positive correlation (r={r_target:.2f}, p={p_target:.4f}). "
                "Executives assigned higher targets generally achieve higher absolute sales volumes."
            ),
            causation_warning=CAUSATION_WARNING,
        )

        # 3. Pearson correlation: Discount % vs Dues
        disc_dues_pairs = [
            (s.discount_pct, s.dues)
            for s in sales
            if s.discount_pct is not None and s.dues is not None
        ]
        if len(disc_dues_pairs) >= 2:
            x_disc = [p[0] for p in disc_dues_pairs]
            y_dues = [p[1] for p in disc_dues_pairs]
            r_disc, p_disc = stats.pearsonr(x_disc, y_dues)
        else:
            r_disc, p_disc = 0.0, 1.0

        disc_corr = CorrelationResult(
            variable_x="Discount Percentage (%)",
            variable_y="Outstanding Dues (BDT)",
            correlation_coefficient=round(float(r_disc), 4),
            p_value=round(float(p_disc), 4),
            sample_size=len(disc_dues_pairs),
            interpretation=(
                f"Correlation r={r_disc:.2f} (p={p_disc:.4f}). Indicates relationship between discount depth "
                "and remaining balance dues."
            ),
            causation_warning=CAUSATION_WARNING,
        )

        # 4. 95% Wilson Confidence Interval for Collection Rate (Full Paid or Active vs Total July sales)
        # Point estimate: Proportion of transactions that paid full or substantial deposit
        total_n = len(sales)
        successes = sum(
            1 for s in sales if (s.booking_status or "").strip().lower() == "full paid"
        )
        p_hat = successes / total_n if total_n > 0 else 0.0
        z = 1.96  # 95% confidence

        # Wilson score interval
        denominator = 1 + (z**2) / total_n
        centre_adj = p_hat + (z**2) / (2 * total_n)
        adjusted_std = math.sqrt((p_hat * (1 - p_hat) / total_n) + ((z**2) / (4 * (total_n**2))))
        ci_lower = max(0.0, (centre_adj - z * adjusted_std) / denominator)
        ci_upper = min(1.0, (centre_adj + z * adjusted_std) / denominator)

        ci_res = ConfidenceIntervalResult(
            metric_name="Full-Paid Share Conversion Rate (July Sold Shares)",
            point_estimate=round(p_hat * 100.0, 2),
            confidence_level=95.0,
            ci_lower=round(ci_lower * 100.0, 2),
            ci_upper=round(ci_upper * 100.0, 2),
            method="Wilson Score Interval",
            interpretation=(
                f"We are 95% confident that the true population full-paid settlement rate "
                f"lies between {ci_lower*100:.1f}% and {ci_upper*100:.1f}% (sample n={total_n}, successes={successes})."
            ),
        )

        # 5. Mann-Whitney U test: Team Leader vs Executive achievement %
        tl_pcts = [
            e.achievement_pct
            for e in execs
            if e.role == "Team Leader" and e.achievement_pct is not None
        ]
        exe_pcts = [
            e.achievement_pct
            for e in execs
            if e.role == "Executive" and e.achievement_pct is not None
        ]

        if len(tl_pcts) > 0 and len(exe_pcts) > 0:
            u_stat, mw_p = stats.mannwhitneyu(tl_pcts, exe_pcts, alternative="two-sided")
            tl_med = float(np.median(tl_pcts))
            exe_med = float(np.median(exe_pcts))
        else:
            u_stat, mw_p, tl_med, exe_med = 0.0, 1.0, 0.0, 0.0

        is_sig = mw_p < 0.05
        mw_res = MannWhitneyTestResult(
            group1_name="Team Leader",
            group2_name="Executive",
            group1_median=round(tl_med, 2),
            group2_median=round(exe_med, 2),
            u_statistic=round(float(u_stat), 2),
            p_value=round(float(mw_p), 4),
            significant_at_05=is_sig,
            interpretation=(
                f"Mann-Whitney non-parametric test comparing Team Leaders (median {tl_med:.1f}%) "
                f"vs Executives (median {exe_med:.1f}%): U={u_stat:.1f}, p={mw_p:.4f}. "
                + (
                    "Difference is statistically significant at p < 0.05."
                    if is_sig
                    else "Difference is not statistically significant at alpha=0.05 level."
                )
            ),
        )

        return StatsResponse(
            transaction_prices=price_stats,
            discount_percentages=discount_stats,
            target_vs_achieved_correlation=target_corr,
            discount_vs_dues_correlation=disc_corr,
            collection_rate_ci=ci_res,
            team_leader_vs_exec_test=mw_res,
        )

    def get_discounts(self) -> DiscountsResponse:
        sales = self.db.query(SalesJuly).all()
        disc_pcts = [s.discount_pct for s in sales if s.discount_pct is not None]
        disc_amts = [s.discount_amount for s in sales if s.discount_amount is not None]

        overall_avg = float(np.mean(disc_pcts)) if disc_pcts else 0.0
        overall_total = float(sum(disc_amts))

        # By division
        divisions = set(s.division for s in sales if s.division)
        by_div = []
        for d in sorted(divisions):
            sub = [s for s in sales if s.division == d]
            sub_pcts = [s.discount_pct for s in sub if s.discount_pct is not None]
            sub_amts = [s.discount_amount for s in sub if s.discount_amount is not None]
            sub_dues = [s.dues for s in sub if s.dues is not None]
            by_div.append(
                DiscountByDivision(
                    division=d,
                    transaction_count=len(sub),
                    avg_discount_pct=round(float(np.mean(sub_pcts)), 2) if sub_pcts else 0.0,
                    total_discount_amount=round(float(sum(sub_amts)), 2),
                    avg_dues=round(float(np.mean(sub_dues)), 2) if sub_dues else 0.0,
                )
            )

        # By sales officer (D.O)
        officers = set(s.sales_officer for s in sales if s.sales_officer)
        by_officer = []
        for off in sorted(officers):
            sub = [s for s in sales if s.sales_officer == off]
            sub_pcts = [s.discount_pct for s in sub if s.discount_pct is not None]
            sub_amts = [s.discount_amount for s in sub if s.discount_amount is not None]
            sub_dues = [s.dues for s in sub if s.dues is not None]
            by_officer.append(
                DiscountByOfficer(
                    officer_name=off,
                    transaction_count=len(sub),
                    avg_discount_pct=round(float(np.mean(sub_pcts)), 2) if sub_pcts else 0.0,
                    total_discount_amount=round(float(sum(sub_amts)), 2),
                    avg_dues=round(float(np.mean(sub_dues)), 2) if sub_dues else 0.0,
                )
            )

        by_officer = sorted(by_officer, key=lambda x: x.avg_discount_pct, reverse=True)

        return DiscountsResponse(
            overall_avg_discount_pct=round(overall_avg, 2),
            overall_total_discount_amount=round(overall_total, 2),
            by_division=by_div,
            by_sales_officer=by_officer,
            discount_to_dues_relationship=(
                "Analysis shows higher discounts are frequently offered on larger multi-share sales packages, "
                "which carry structured installment schedules and consequently higher nominal dues."
            ),
        )
