"""Public feasibility API. No silent synthetic provider fallbacks."""
import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import AssessmentRequest, LocationCandidate
from app.services.providers import ProviderError, fetch_weather, search_locations
from app.services.assessment import analyze
from app.services.solar import maximum_modules
from app.storage import find_result, save_result
from app.report import create_pdf

expose_docs = os.getenv("RENEWCALC_EXPOSE_API_DOCS", "false").lower() in {"1", "true", "yes"}
app = FastAPI(title="RenewCalc API", version="0.2.0",
              docs_url="/docs" if expose_docs else None,
              redoc_url=None,
              openapi_url="/openapi.json" if expose_docs else None)
allowed_origins = [x.strip() for x in os.getenv("RENEWCALC_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/v1/locations/search", response_model=list[LocationCandidate])
def locations_search(q: str = Query(min_length=2, max_length=80)):
    try:
        return search_locations(q)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v1/weather/summary")
def weather_summary(latitude: float, longitude: float, start_year: int = 2022, end_year: int = 2024):
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise HTTPException(422, "Coordinates outside valid geographic range")
    if not 2010 <= start_year <= end_year <= 2024 or end_year - start_year > 4:
        raise HTTPException(422, "Invalid historical weather years")
    try:
        frame, source = fetch_weather(latitude, longitude, start_year, end_year)
    except ProviderError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"source": source, "hour_count": len(frame),
            "start": frame.index[0].isoformat(), "end": frame.index[-1].isoformat(),
            "mean_ghi_w_m2": round(float(frame["shortwave_radiation"].mean()), 2)}


@app.get("/api/v1/tariffs/utilities")
def tariff_utilities():
    return {"utilities": [], "status": "unavailable",
            "message": "No reviewed official Indian DISCOM tariffs are bundled. Use a user-supplied flat-rate scenario."}


@app.get("/api/v1/tariffs/lookup")
def tariff_lookup(state: str = "", utility: str = ""):
    return {"status": "unavailable", "state": state, "utility": utility,
            "message": "Official tariffs require documented manual verification; no verified record available."}


@app.get("/api/v1/incentives")
def incentives():
    return {"verified": [], "status": "unavailable",
            "message": "Subsidies are not included until eligibility and current rules can be verified."}


@app.post("/api/v1/assessments", status_code=201)
def create_assessment(payload: AssessmentRequest):
    if maximum_modules(payload.site) == 0:
        raise HTTPException(422, "Roof area cannot fit one module under the specified layout")
    try:
        weather, source = fetch_weather(payload.location.latitude, payload.location.longitude,
                                        payload.weather_start_year, payload.weather_end_year)
        result = analyze(payload, weather, source)
    except ProviderError as exc:
        raise HTTPException(502, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    try:
        result_id = save_result(result)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, f"Persistent assessment storage unavailable: {exc}") from exc
    return {"id": result_id, "result": result}


@app.get("/api/v1/assessments/{assessment_id}")
def get_assessment(assessment_id: str):
    result = find_result(assessment_id)
    if result is None:
        raise HTTPException(404, "Assessment unavailable, expired or not found")
    return {"id": assessment_id, "result": result}


@app.get("/api/v1/assessments/{assessment_id}/report")
def assessment_report(assessment_id: str):
    result = find_result(assessment_id)
    if result is None:
        raise HTTPException(404, "Assessment unavailable, expired or not found")
    return Response(create_pdf(result), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="renewcalc-{assessment_id[:8]}.pdf"'})
