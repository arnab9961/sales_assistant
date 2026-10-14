import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Use SQLite in-memory for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ANONYMIZE_NAMES"] = "true"
os.environ["WEBHOOK_API_KEY"] = "test_webhook_key_secret"

from app.database import Base, get_db, get_ro_db
from app.etl.loader import run_etl
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    # Run ETL on test database if data dir exists
    if os.path.exists("data"):
        run_etl(session, data_dir="data")
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture(scope="session")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ro_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
