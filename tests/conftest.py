import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from unittest.mock import patch, MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set artefacts dir for tests
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["LLM_MODEL"] = "gpt-4o"

from app.main import app
from app.db import get_session
from app.models.incident import Incident, InvestigationStateDB, RecommendedActionDB


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a FastAPI test client with DB override."""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_incident_payload():
    return {
        "incident_id": "INC-TEST-001",
        "title": "Order Service 503 Failures",
        "affected_service": "order-service",
        "severity": "SEV-2",
        "start_time": "2025-07-14T02:15:00Z",
        "detection_time": "2025-07-14T02:22:00Z",
        "customer_impact": "18% of checkout requests failing",
        "reporter_notes": "DB timeouts spiking, batch job running, recent deployment.",
        "initial_symptoms": [
            "HTTP 503 responses elevated",
            "DB timeout errors",
            "Batch job running during incident window",
        ],
        "tags": ["order-service", "503", "database"],
    }
