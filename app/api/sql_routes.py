from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_ro_db
from app.services.sql_service import SQLRunnerService

router = APIRouter(prefix="/api/sql", tags=["SQL Analytics"])
sql_service = SQLRunnerService()


@router.get("", response_model=Dict[str, Any])
def list_whitelisted_queries():
    """List all pre-approved, whitelisted analytical SQL queries."""
    return {"whitelisted_queries": sql_service.get_whitelisted_queries()}


@router.get("/{query_name}")
def run_whitelisted_query(
    query_name: str,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to offset"),
    db: Session = Depends(get_ro_db),
):
    """Execute a specific whitelisted analytical SQL query using read-only database credentials,
    strict parameterization, and pagination.
    """
    return sql_service.execute_query(db, query_name, limit=limit, offset=offset)
