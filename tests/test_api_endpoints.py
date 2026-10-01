"""
Test: Core API endpoints work correctly.
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["ARTEFACTS_DIR"] = os.path.join(os.path.dirname(__file__), "..", "artefacts")
os.environ["DATABASE_URL"] = "sqlite://"

from tests.conftest import *  # noqa


class TestIncidentAPI:
    def test_create_incident(self, client, sample_incident_payload):
        """POST /incidents creates a new incident."""
        response = client.post("/incidents", json=sample_incident_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["incident_id"] == "INC-TEST-001"
        assert data["status"] == "open"
        assert data["affected_service"] == "order-service"

    def test_get_incident(self, client, sample_incident_payload):
        """GET /incidents/{id} retrieves an existing incident."""
        client.post("/incidents", json=sample_incident_payload)
        response = client.get("/incidents/INC-TEST-001")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == "INC-TEST-001"

    def test_get_incident_not_found(self, client):
        """GET /incidents/{id} returns 404 for non-existent incident."""
        response = client.get("/incidents/INC-NONEXISTENT")
        assert response.status_code == 404

    def test_create_duplicate_incident(self, client, sample_incident_payload):
        """Creating an incident with duplicate ID returns 409."""
        client.post("/incidents", json=sample_incident_payload)
        response = client.post("/incidents", json=sample_incident_payload)
        assert response.status_code == 409

    def test_get_evidence_no_investigation(self, client, sample_incident_payload):
        """GET /incidents/{id}/evidence returns empty state if not investigated."""
        client.post("/incidents", json=sample_incident_payload)
        response = client.get("/incidents/INC-TEST-001/evidence")
        assert response.status_code == 200
        data = response.json()
        assert data["evidence_items"] == []

    def test_get_report_before_investigation(self, client, sample_incident_payload):
        """GET /incidents/{id}/report returns 404 if investigation not run."""
        client.post("/incidents", json=sample_incident_payload)
        response = client.get("/incidents/INC-TEST-001/report")
        assert response.status_code == 404

    def test_health_endpoint(self, client):
        """GET /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
