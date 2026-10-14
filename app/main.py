import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import Base, engine, test_connection, SessionLocal
from app.etl.loader import run_etl
from app.middleware import RequestIdAndLoggingMiddleware
from app.models.sales import ExecutiveSep
from app.api.quality import router as quality_router
from app.api.analytics import router as analytics_router
from app.api.forecast import router as forecast_router
from app.api.sql_routes import router as sql_router
from app.api.leads import router as leads_router
from app.api.webhooks import router as webhooks_router
from app.api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sales_ops.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Sales Operations Assistant application...")

    # Create tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    # Check if data should be auto-loaded
    data_path = Path(settings.DATA_DIR)
    if data_path.exists():
        try:
            with SessionLocal() as db:
                exec_count = db.query(ExecutiveSep).count()
                if exec_count == 0:
                    logger.info("Database is empty. Automatically executing ETL from data directory...")
                    run_etl(db, data_dir=settings.DATA_DIR)
                    logger.info("ETL completed successfully on startup.")
                else:
                    logger.info(f"Database already populated ({exec_count} executives found). Skipping startup ETL.")
        except Exception as e:
            logger.error(f"Error during startup ETL: {e}")

    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI Sales Operations Assistant for Sunset Kuakata Hotel & Resort share-sales operations.",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestIdAndLoggingMiddleware)

# Static files & templates
static_path = Path("app/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(quality_router)
app.include_router(analytics_router)
app.include_router(forecast_router)
app.include_router(sql_router)
app.include_router(leads_router)
app.include_router(webhooks_router)
app.include_router(chat_router)


@app.get("/health", tags=["System"])
def health():
    """Health check endpoint indicating container is alive."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/ready", tags=["System"])
def ready():
    """Readiness check verifying database connectivity."""
    db_ok = test_connection()
    if not db_ok:
        return JSONResponse(status_code=503, content={"status": "not_ready", "database": "disconnected"})
    return {"status": "ready", "database": "connected"}


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard(request: Request):
    """Serve the single-page responsive sales operations dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "anonymize_names": settings.ANONYMIZE_NAMES,
        },
    )
