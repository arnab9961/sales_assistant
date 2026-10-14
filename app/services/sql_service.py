import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger("sales_ops.sql")

WHITELISTED_QUERIES = {
    "total_sales_by_project": {
        "file": "total_sales_by_project.sql",
        "title": "Total Sales by Project",
        "description": "Aggregates revenue, sold shares, and client counts across resort projects",
    },
    "monthly_sales_mom": {
        "file": "monthly_sales_mom.sql",
        "title": "Monthly Sales with MoM Growth",
        "description": "Calculates monthly collection trends and MoM growth rate using SQL window functions (LAG)",
    },
    "top_customers_by_deposit": {
        "file": "top_customers_by_deposit.sql",
        "title": "Top Customers by Cumulative Deposit",
        "description": "Retrieves top depositing investors and their outstanding dues",
    },
    "regional_division_performance": {
        "file": "regional_division_performance.sql",
        "title": "Regional Division Performance",
        "description": "Cross-division breakdown of booking volume, discounts, and dues exposure",
    },
}


class SQLRunnerService:
    def __init__(self, sql_dir: str = "sql"):
        self.sql_dir = Path(sql_dir)

    def get_whitelisted_queries(self) -> Dict[str, Any]:
        return {
            name: {
                "name": name,
                "title": meta["title"],
                "description": meta["description"],
            }
            for name, meta in WHITELISTED_QUERIES.items()
        }

    def execute_query(
        self,
        db: Session,
        query_name: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        if query_name not in WHITELISTED_QUERIES:
            valid_names = list(WHITELISTED_QUERIES.keys())
            raise HTTPException(
                status_code=404,
                detail=f"Query '{query_name}' not found or not permitted. Whitelisted queries: {valid_names}",
            )

        meta = WHITELISTED_QUERIES[query_name]
        query_file = self.sql_dir / meta["file"]
        if not query_file.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Query definition file '{meta['file']}' is missing on server",
            )

        sql_content = query_file.read_text(encoding="utf-8")

        # Clean comments from query if running on SQLite or PostgreSQL
        # Ensure parameterized bounds
        safe_limit = max(1, min(limit, 200))
        safe_offset = max(0, offset)

        try:
            # Execute with parameterized bindings
            stmt = text(sql_content).bindparams(
                limit_val=safe_limit,
                offset_val=safe_offset,
            )
            result = db.execute(stmt)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

            # Format numbers for clean JSON serialization
            formatted_rows = []
            for row in rows:
                formatted_row = {}
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        formatted_row[k] = v.isoformat()
                    elif isinstance(v, float):
                        formatted_row[k] = round(v, 2)
                    else:
                        formatted_row[k] = v
                formatted_rows.append(formatted_row)

            return {
                "query_name": query_name,
                "title": meta["title"],
                "description": meta["description"],
                "columns": columns,
                "row_count": len(formatted_rows),
                "limit": safe_limit,
                "offset": safe_offset,
                "data": formatted_rows,
            }
        except Exception as e:
            logger.error(f"Error executing whitelisted query '{query_name}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Database execution error: {str(e)}",
            )
