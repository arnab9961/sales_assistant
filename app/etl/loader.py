import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
from sqlalchemy.orm import Session

from app.config import settings
from app.etl.anonymizer import anonymizer
from app.etl.normalizer import (
    clean_date,
    clean_int,
    clean_number,
    extract_role_and_name,
    normalize_column_name,
)
from app.models.sales import (
    DataQualityIssue,
    DivisionMonthly,
    ExecutiveSep,
    ProjectSep,
    ProjectStatusSep,
    SalesJuly,
)

logger = logging.getLogger("sales_ops.etl")


def find_file(directory: Path, patterns: List[str]) -> Optional[Path]:
    """Find a file in directory matching any of the pattern strings (case-insensitive & fuzzy)."""
    if not directory.exists():
        return None

    # Check direct match
    for f in directory.iterdir():
        if f.is_file():
            fname_clean = f.name.lower().replace("_", " ").replace("-", " ")
            for pat in patterns:
                pat_clean = pat.lower().replace("_", " ").replace("-", " ")
                if pat_clean in fname_clean or fname_clean in pat_clean:
                    return f

    return None


class DataLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.quality_issues: List[Dict[str, Any]] = []

    def log_issue(
        self,
        table_name: str,
        issue_type: str,
        severity: str,
        description: str,
        row_id: Optional[str] = None,
        details: Optional[str] = None,
    ):
        issue = {
            "table_name": table_name,
            "issue_type": issue_type,
            "severity": severity,
            "row_identifier": row_id,
            "description": description,
            "details": details,
        }
        self.quality_issues.append(issue)
        logger.info(f"[{severity.upper()}] {table_name}: {description}")

    def load_executives_sep(self, wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
        """Load executive collection sheet for September."""
        # Target sheet is '30.9.26'
        sheet_name = "30.9.26"
        if sheet_name not in wb.sheetnames:
            # Fallback to first sheet
            sheet_name = wb.sheetnames[0]

        ws = wb[sheet_name]
        records: List[Dict[str, Any]] = []

        # Header is on row 2
        header_row = 2
        headers = []
        for c in range(1, ws.max_column + 1):
            val = ws.cell(header_row, c).value
            headers.append(normalize_column_name(val))

        seen_names = set()
        total_row_values = {}

        for r in range(header_row + 1, ws.max_row + 1):
            row_raw = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
            if not any(v is not None for v in row_raw):
                continue

            row_dict = {headers[i]: row_raw[i] for i in range(len(headers)) if i < len(row_raw)}
            team_str = str(row_dict.get("team") or "").strip()

            # Check for Total row
            if "total" in team_str.lower() or team_str == "":
                # Check if this is the summary Total row
                sl = str(row_dict.get("sl_no") or "").strip().lower()
                if "total" in team_str.lower() or "total" in sl or any(
                    "total" in str(v).lower() for v in row_raw[:3] if v
                ):
                    total_row_values = {
                        "target": clean_number(row_dict.get("target")),
                        "achieved": clean_number(row_dict.get("achieved_sep")),
                        "dues": clean_number(row_dict.get("dues")),
                        "new_sales": clean_number(row_dict.get("new_sales")),
                        "emi": clean_number(row_dict.get("emi")),
                        "total_collection": clean_number(row_dict.get("total_collection")),
                    }
                    continue

            name_clean, role = extract_role_and_name(team_str)
            anonymized_name = anonymizer.anonymize_executive(name_clean, role)

            # Check duplicates
            if name_clean in seen_names:
                self.log_issue(
                    "executives_sep",
                    "duplicate",
                    "warning",
                    f"Duplicate executive name detected: {name_clean}",
                    row_id=f"Row-{r}",
                )
            seen_names.add(name_clean)

            sl_no = clean_int(row_dict.get("sl_no"))
            client_target = clean_int(row_dict.get("clients_target"))
            share_target = clean_int(row_dict.get("share"))
            target_amt = clean_number(row_dict.get("target"))
            achieved_amt = clean_number(row_dict.get("achieved_sep"))
            dues_amt = clean_number(row_dict.get("dues"))
            token_cnt = clean_int(row_dict.get("token"))
            sold_share_cnt = clean_int(row_dict.get("sold_share"))
            new_sales = clean_number(row_dict.get("new_sales"))
            emi = clean_number(row_dict.get("emi"))
            total_coll = clean_number(row_dict.get("total_collection"))

            # Missing value checks
            if target_amt is None:
                self.log_issue(
                    "executives_sep",
                    "missing_value",
                    "warning",
                    f"Executive {anonymized_name} has no management target specified",
                    row_id=f"Row-{r}",
                )
            elif target_amt == 0:
                self.log_issue(
                    "executives_sep",
                    "zero_target",
                    "info",
                    f"Executive {anonymized_name} has target of 0",
                    row_id=f"Row-{r}",
                )

            # Arithmetic checks: Dues == Target - Achieved
            if target_amt is not None and achieved_amt is not None and dues_amt is not None:
                expected_dues = target_amt - achieved_amt
                if abs(expected_dues - dues_amt) > 1.0:
                    self.log_issue(
                        "executives_sep",
                        "arithmetic_error",
                        "warning",
                        f"Dues mismatch for {anonymized_name}: reported={dues_amt}, calculated={expected_dues}",
                        row_id=f"Row-{r}",
                        details=f"Target={target_amt}, Achieved={achieved_amt}, Diff={expected_dues - dues_amt}",
                    )

            # Arithmetic checks: Total Collection == New Sales + EMI
            ns = new_sales or 0.0
            em = emi or 0.0
            if total_coll is not None and (new_sales is not None or emi is not None):
                expected_coll = ns + em
                if abs(expected_coll - total_coll) > 1.0:
                    self.log_issue(
                        "executives_sep",
                        "arithmetic_error",
                        "warning",
                        f"Total collection mismatch for {anonymized_name}: reported={total_coll}, expected={expected_coll}",
                        row_id=f"Row-{r}",
                    )

            achieve_pct = None
            if target_amt and target_amt > 0 and achieved_amt is not None:
                achieve_pct = (achieved_amt / target_amt) * 100.0

            records.append(
                {
                    "sl_no": sl_no,
                    "name_raw": team_str,
                    "name": anonymized_name,
                    "role": role,
                    "client_target": client_target,
                    "share_target": share_target,
                    "target_amount": target_amt,
                    "achieved_amount": achieved_amt,
                    "dues_amount": dues_amt,
                    "token_count": token_cnt,
                    "sold_share_count": sold_share_cnt,
                    "new_sales": new_sales,
                    "emi": emi,
                    "total_collection": total_coll,
                    "achievement_pct": achieve_pct,
                    "month": "2026-09",
                }
            )

        # Cross check totals against sheet Total row
        calc_target = sum(r["target_amount"] or 0 for r in records)
        calc_achieved = sum(r["achieved_amount"] or 0 for r in records)
        calc_dues = sum(r["dues_amount"] or 0 for r in records)
        calc_new_sales = sum(r["new_sales"] or 0 for r in records)
        calc_emi = sum(r["emi"] or 0 for r in records)
        calc_total_coll = sum(r["total_collection"] or 0 for r in records)

        if total_row_values:
            sheet_target = total_row_values.get("target")
            sheet_achieved = total_row_values.get("achieved")
            sheet_dues = total_row_values.get("dues")

            if sheet_target and abs(calc_target - sheet_target) > 1.0:
                self.log_issue(
                    "executives_sep",
                    "cross_check_discrepancy",
                    "critical",
                    f"Sum of executive targets ({calc_target:,.2f}) does not match sheet Total ({sheet_target:,.2f})",
                )
            if sheet_achieved and abs(calc_achieved - sheet_achieved) > 1.0:
                self.log_issue(
                    "executives_sep",
                    "cross_check_discrepancy",
                    "critical",
                    f"Sum of achieved ({calc_achieved:,.2f}) does not match sheet Total ({sheet_achieved:,.2f})",
                )
            if sheet_dues and abs(calc_dues - sheet_dues) > 1.0:
                diff = sheet_dues - calc_dues
                self.log_issue(
                    "executives_sep",
                    "cross_check_discrepancy",
                    "warning",
                    f"Sum of dues ({calc_dues:,.2f}) differs from sheet Total row ({sheet_dues:,.2f}) by {diff:,.2f} BDT",
                    details="Excel sheet total has 38,251,500 while sum of rows is 38,251,000 (arithmetic gap of 500 BDT in spreadsheet)",
                )

        return records

    def load_projects_sep(
        self, wb: openpyxl.Workbook
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse stacked tables in Project Wise Collection (Sep-26).
        Returns: (project_records, status_records)
        """
        sheet_name = "Sep-26"
        if sheet_name not in wb.sheetnames:
            sheet_name = wb.sheetnames[0]

        ws = wb[sheet_name]
        project_records: List[Dict[str, Any]] = []
        status_records: List[Dict[str, Any]] = []

        current_table = None
        current_headers = []

        for r in range(1, ws.max_row + 1):
            row_vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
            row_str = " ".join([str(v) for v in row_vals if v is not None]).strip()

            if not row_str:
                continue

            # Detect Table Headers by title text
            if "total sold share & collection" in row_str.lower() and "sep" in row_str.lower():
                current_table = "month_totals"
                current_headers = []
                continue
            elif "only kuakata" in row_str.lower():
                current_table = "only_kuakata"
                current_headers = []
                continue
            elif "only dfi" in row_str.lower():
                current_table = "only_dfi"
                current_headers = []
                continue
            elif "only hospital" in row_str.lower():
                current_table = "only_hospital"
                current_headers = []
                continue
            elif "project wise sale value & collection" in row_str.lower():
                current_table = "summary_non_overlapping"
                current_headers = []
                continue
            elif "status wise" in row_str.lower():
                current_table = "status_separation"
                current_headers = []
                continue

            # Detect Column Headers Row
            first_val = str(row_vals[0] or row_vals[1] or "").strip().lower()
            if "sl.no" in first_val or "sl. no" in first_val or "project name" in row_str.lower():
                current_headers = [str(v).strip().lower() if v is not None else "" for v in row_vals]
                continue

            if not current_table or not current_headers:
                continue

            # Skip Total summary rows inside each table
            if any("total" in str(v).lower() for v in row_vals[:3] if v is not None):
                continue

            col_map = {current_headers[i]: row_vals[i] for i in range(len(current_headers)) if i < len(row_vals)}

            p_name = None
            for key in ("project name", "seperation", "separation"):
                if key in col_map and col_map[key] is not None:
                    p_name = str(col_map[key]).strip()
                    break

            if not p_name:
                continue

            if current_table == "status_separation":
                status_records.append(
                    {
                        "status_name": p_name,
                        "clients_qty": clean_int(col_map.get("clients qty")),
                        "share_qty": clean_int(col_map.get("share qty")),
                        "sale_value": clean_number(col_map.get("sale value")),
                        "collected_amount": clean_number(col_map.get("collected amount")),
                        "dues": clean_number(col_map.get("dues")),
                        "month": "2026-09",
                    }
                )
            else:
                sl_no = clean_int(col_map.get("sl.no") or col_map.get("sl. no"))
                clients_qty = clean_int(col_map.get("clients qty"))
                share_qty = clean_int(col_map.get("share qty"))
                sale_value = clean_number(col_map.get("sale value"))
                total_coll = clean_number(
                    col_map.get("total collected amount") or col_map.get("collected amount")
                )
                only_sep_coll = clean_number(col_map.get("only sep-26 collected"))
                avg_sv = clean_number(col_map.get("avg s.v"))
                avg_coll = clean_number(col_map.get("avg collection"))

                project_records.append(
                    {
                        "sl_no": sl_no,
                        "project_name": p_name,
                        "clients_qty": clients_qty,
                        "share_qty": share_qty,
                        "sale_value": sale_value,
                        "total_collected_amount": total_coll,
                        "only_sep_collected": only_sep_coll,
                        "avg_sale_value": avg_sv,
                        "avg_collection": avg_coll,
                        "table_source": current_table,
                        "month": "2026-09",
                    }
                )

        return project_records, status_records

    def load_discount_sales(self, wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
        """Load July sold share discount data."""
        ws = wb["Sheet1"] if "Sheet1" in wb.sheetnames else wb.sheetnames[0]
        records: List[Dict[str, Any]] = []

        # Row 4 is column headers (Row 3 was a summary total)
        header_row = 4
        headers = []
        for c in range(1, ws.max_column + 1):
            val = ws.cell(header_row, c).value
            headers.append(normalize_column_name(val))

        seen_ids = set()

        for r in range(header_row + 1, ws.max_row + 1):
            row_raw = [ws.cell(r, c).value for c in range(1, len(headers) + 1)]
            if not any(v is not None for v in row_raw):
                continue

            row_dict = {headers[i]: row_raw[i] for i in range(len(headers)) if i < len(row_raw)}

            c_id = str(row_dict.get("client_id") or "").strip()
            if not c_id or "total" in c_id.lower():
                continue

            client_raw = str(row_dict.get("client_name") or "").strip()
            do_raw = str(row_dict.get("sales_officer") or "").strip()

            anonymized_client = anonymizer.anonymize_client(client_raw)
            anonymized_do = anonymizer.anonymize_do(do_raw)

            sale_dt = clean_date(row_dict.get("date"))
            orig_price = clean_number(row_dict.get("original_price"))
            disc_amt = clean_number(row_dict.get("discount_amount"))
            disc_pct = clean_number(row_dict.get("discount_pct"))
            sales_price = clean_number(row_dict.get("sales_price"))
            total_deposit = clean_number(row_dict.get("total_deposit"))
            dues = clean_number(row_dict.get("dues"))
            aug_dep = clean_number(row_dict.get("august_deposited"))
            status = str(row_dict.get("booking_status") or "").strip() or "Unknown"

            # Check duplicate client IDs
            if c_id in seen_ids:
                self.log_issue(
                    "sales_july",
                    "duplicate",
                    "info",
                    f"Duplicate Client ID {c_id} in transactions (multiple unit purchases)",
                    row_id=f"Row-{r}",
                )
            seen_ids.add(c_id)

            # Arithmetic checks on discount: Original - Discount == Sales Price
            if orig_price is not None and disc_amt is not None and sales_price is not None:
                calc_sp = orig_price - disc_amt
                if abs(calc_sp - sales_price) > 1.0:
                    self.log_issue(
                        "sales_july",
                        "arithmetic_error",
                        "warning",
                        f"Sales price mismatch for Client ID {c_id}: reported={sales_price}, calculated={calc_sp}",
                        row_id=f"Row-{r}",
                    )

            # Arithmetic checks on dues: Sales Price - Total Deposit == Dues
            if sales_price is not None and total_deposit is not None and dues is not None:
                calc_dues = sales_price - total_deposit
                if abs(calc_dues - dues) > 1.0:
                    self.log_issue(
                        "sales_july",
                        "arithmetic_error",
                        "warning",
                        f"Dues mismatch for Client ID {c_id}: reported={dues}, calculated={calc_dues}",
                        row_id=f"Row-{r}",
                    )

            records.append(
                {
                    "sl_no": clean_int(row_dict.get("sl_no")),
                    "sale_date": sale_dt,
                    "client_id": c_id,
                    "client_name_raw": client_raw,
                    "client_name": anonymized_client,
                    "sales_officer_raw": do_raw,
                    "sales_officer": anonymized_do,
                    "division": str(row_dict.get("division") or "").strip() or "Unknown",
                    "unit_types": str(row_dict.get("unit_types") or "").strip(),
                    "original_price": orig_price,
                    "discount_amount": disc_amt,
                    "discount_pct": disc_pct,
                    "sales_price": sales_price,
                    "total_deposit": total_deposit,
                    "dues": dues,
                    "august_deposited": aug_dep,
                    "booking_status": status,
                    "last_deposited_date": str(row_dict.get("last_deposited_date") or "").strip(),
                }
            )

        return records

    def load_division_monthly(
        self, wb: openpyxl.Workbook, month_label: str
    ) -> List[Dict[str, Any]]:
        """Load division monthly summary from Sheet3."""
        sheet_name = "Sheet3"
        if sheet_name not in wb.sheetnames:
            return []

        ws = wb[sheet_name]
        records: List[Dict[str, Any]] = []

        # Read New Token/Booking table (rows 5 to 10)
        # Division, Expected New Clients, Expected New Share, Exp Amount, Inv. Clients, Inv. Share, Collected, %
        divisions = ["Corporate", "SED", "CST", "Directorial", "Founder"]

        for r in range(5, 30):
            d_name = str(ws.cell(r, 1).value or "").strip()
            if d_name in divisions:
                exp_c = clean_int(ws.cell(r, 2).value)
                exp_s = clean_int(ws.cell(r, 3).value)
                exp_amt = clean_number(ws.cell(r, 4).value)
                inv_c = clean_int(ws.cell(r, 5).value)
                inv_s = clean_int(ws.cell(r, 6).value)
                coll_amt = clean_number(ws.cell(r, 7).value)
                pct = clean_number(ws.cell(r, 8).value)

                records.append(
                    {
                        "month": month_label,
                        "division": d_name,
                        "category": "token_booking",
                        "expected_clients": exp_c,
                        "expected_shares": exp_s,
                        "expected_amount": exp_amt,
                        "invested_clients": inv_c,
                        "invested_shares": inv_s,
                        "collected_amount": coll_amt,
                        "achievement_pct": pct,
                    }
                )

        return records

    def run_all(self, db: Session):
        """Execute full ETL load into PostgreSQL / database."""
        logger.info(f"Starting ETL load from directory: {self.data_dir.resolve()}")

        # 1. Load Executive Sep
        f_exec = find_file(self.data_dir, ["Estimated_Budget_-September_26", "Estimated Budget -September 26"])
        if f_exec:
            wb = openpyxl.load_workbook(f_exec, data_only=True)
            exec_records = self.load_executives_sep(wb)
            db.query(ExecutiveSep).delete()
            for r in exec_records:
                db.add(ExecutiveSep(**r))
            db.commit()
            logger.info(f"Loaded {len(exec_records)} executive records for September")
        else:
            self.log_issue("executives_sep", "missing_file", "critical", "September Executive file not found")

        # 2. Load Project Wise Collection
        f_proj = find_file(self.data_dir, ["Project_Wise_Collection__Only_Sep_", "Project Wise Collection.(Only Sep)"])
        if f_proj:
            wb = openpyxl.load_workbook(f_proj, data_only=True)
            p_records, s_records = self.load_projects_sep(wb)
            db.query(ProjectSep).delete()
            for r in p_records:
                db.add(ProjectSep(**r))
            db.query(ProjectStatusSep).delete()
            for r in s_records:
                db.add(ProjectStatusSep(**r))
            db.commit()
            logger.info(f"Loaded {len(p_records)} project records and {len(s_records)} status records")
        else:
            self.log_issue("projects_sep", "missing_file", "critical", "Project Wise Collection file not found")

        # 3. Load Discount Price (Sales July)
        f_disc = find_file(self.data_dir, ["Discount_Price", "Discount Price"])
        if f_disc:
            wb = openpyxl.load_workbook(f_disc, data_only=True)
            d_records = self.load_discount_sales(wb)
            db.query(SalesJuly).delete()
            for r in d_records:
                db.add(SalesJuly(**r))
            db.commit()
            logger.info(f"Loaded {len(d_records)} sales records for July (Discount_Price)")
        else:
            self.log_issue("sales_july", "missing_file", "critical", "Discount Price file not found")

        # 4. Load Division Monthly (Sep & Aug)
        f_div_sep = find_file(self.data_dir, ["All_Division_Estimate_budget__Sep-26", "All Division Estimate budget  Sep-26"])
        f_div_aug = find_file(self.data_dir, ["All_Division_Estimate_budget__Aug-26", "All Division Estimate budget  Aug-26"])
        db.query(DivisionMonthly).delete()

        div_count = 0
        if f_div_sep:
            wb = openpyxl.load_workbook(f_div_sep, data_only=True)
            div_sep = self.load_division_monthly(wb, "2026-09")
            for r in div_sep:
                db.add(DivisionMonthly(**r))
            div_count += len(div_sep)

        if f_div_aug:
            wb = openpyxl.load_workbook(f_div_aug, data_only=True)
            div_aug = self.load_division_monthly(wb, "2026-08")
            for r in div_aug:
                db.add(DivisionMonthly(**r))
            div_count += len(div_aug)
        db.commit()
        logger.info(f"Loaded {div_count} division monthly records")

        # 5. Inter-table cross checks
        # Check if project summary total matches executive total collection
        exec_total_coll = sum(r["total_collection"] or 0 for r in exec_records) if f_exec else 0
        proj_summary_coll = 0
        if f_proj:
            for r in p_records:
                if r["table_source"] == "summary_non_overlapping":
                    proj_summary_coll += (r["only_sep_collected"] or 0)

        if exec_total_coll and proj_summary_coll:
            diff = abs(exec_total_coll - proj_summary_coll)
            if diff > 10.0:
                self.log_issue(
                    "cross_table_check",
                    "inter_table_mismatch",
                    "info",
                    f"Executive Sep Total Collection ({exec_total_coll:,.2f}) differs from Project Summary Only-Sep ({proj_summary_coll:,.2f}) by {diff:,.2f} BDT",
                    details="Executive sheet captures Corporate division sales team; project summary aggregates all collections across divisions/branches.",
                )

        # 6. Save data quality issues to DB
        db.query(DataQualityIssue).delete()
        for issue in self.quality_issues:
            db.add(DataQualityIssue(**issue))
        db.commit()
        logger.info(f"Logged {len(self.quality_issues)} data quality audit issues")


def run_etl(db: Session, data_dir: str = "data") -> DataLoader:
    loader = DataLoader(data_dir=data_dir)
    loader.run_all(db)
    return loader
