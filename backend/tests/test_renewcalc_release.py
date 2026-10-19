from fastapi.testclient import TestClient
from app.main import app
from app.schemas import AssessmentRequest


def test_service_health_and_no_public_api_docs():
    client = TestClient(app)
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 404


def test_shorter_default_weather_study():
    payload = AssessmentRequest.model_validate({
        "location": {"name": "Pune", "latitude": 18.52, "longitude": 73.86},
        "site": {"roof_area_m2": 60},
        "consumption": {"monthly_kwh": 300},
        "tariff": {"import_rate_inr_kwh": 8},
        "finance": {"installation_cost_inr_kwp": 55000},
    })
    assert (payload.weather_start_year, payload.weather_end_year) == (2023, 2023)
