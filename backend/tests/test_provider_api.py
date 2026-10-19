import os
from datetime import datetime, timezone
import httpx
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.providers import weather_payload_to_frame, ProviderError, search_locations


def test_location_provider_filters_india_only():
    def handler(request):
        return httpx.Response(200,json={"results":[
            {"id":1,"name":"Pune","admin1":"Maharashtra","country":"India","country_code":"IN","latitude":18.5,"longitude":73.8,"timezone":"Asia/Kolkata"},
            {"id":2,"name":"Pune","country":"Elsewhere","country_code":"XX","latitude":20,"longitude":40},
        ]})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        matches=search_locations("Pune",client)
    assert len(matches)==1 and matches[0]["latitude"]==18.5


def test_provider_rejects_bad_units_and_gaps():
    idx = pd.date_range("2022-01-01",periods=24*365,freq="h",tz="UTC")
    payload={"hourly":{"time":(idx.astype("int64")//10**9).tolist()},
             "hourly_units":{"shortwave_radiation":"W/m²","direct_normal_irradiance":"W/m²", "diffuse_radiation":"W/m²","temperature_2m":"°C","wind_speed_10m":"km/h"}}
    for name in ["shortwave_radiation","direct_normal_irradiance","diffuse_radiation","temperature_2m","wind_speed_10m"]:
        payload["hourly"][name]=[20.] * len(idx)
    payload["hourly_units"]["shortwave_radiation"]="MJ/m²"
    with pytest.raises(ProviderError, match="unit"):
        weather_payload_to_frame(payload,2022,2022)
    payload["hourly_units"]["shortwave_radiation"]="W/m²"
    # Missing day-boundary weather hours should fail coverage validation.
    with pytest.raises(ProviderError, match="coverage"):
        weather_payload_to_frame(payload,2022,2022)


def test_api_health_and_unverified_tariffs():
    client = TestClient(app)
    assert client.get("/api/v1/health").status_code==200
    tariffs=client.get("/api/v1/tariffs/utilities").json()
    assert tariffs["status"]=="unavailable" and not tariffs["utilities"]
    assert client.get("/api/v1/incentives").json()["verified"]==[]


def test_api_rejects_invalid_payload_without_calling_network():
    client=TestClient(app)
    r=client.post("/api/v1/assessments",json={"location":{"name":"Delhi","latitude":500,"longitude":77}})
    assert r.status_code==422


def test_api_provider_failure_returns_502(monkeypatch):
    from app import main
    def failure(*a,**kw):
        raise ProviderError("weather unavailable")
    monkeypatch.setattr(main,"fetch_weather", failure)
    request={"location":{"name":"Pune India","latitude":18.5,"longitude":73.8},
             "site":{"roof_area_m2":40}, "consumption":{},"tariff":{},"finance":{}}
    r=TestClient(app).post("/api/v1/assessments",json=request)
    assert r.status_code==502
    assert "weather unavailable" in r.json()["detail"]


def test_complete_2022_local_year_weather_is_accepted():
    local_hours = pd.date_range("2022-01-01",periods=365*24,freq="h",tz="Asia/Kolkata")
    # Source timestamps are at each interval end; parser shifts to its beginning.
    ends = (local_hours.tz_convert("UTC")+pd.Timedelta(hours=1)).astype("int64")//10**9
    payload = {"hourly":{"time":ends.tolist()},"hourly_units":{
        "shortwave_radiation":"W/m²", "direct_normal_irradiance":"W/m²",
        "diffuse_radiation":"W/m²", "temperature_2m":"°C", "wind_speed_10m":"km/h"}}
    for name in ["shortwave_radiation","direct_normal_irradiance","diffuse_radiation"]:
        payload["hourly"][name]=[120.]*len(ends)
    payload["hourly"]["temperature_2m"]=[25.]*len(ends)
    payload["hourly"]["wind_speed_10m"]=[8.]*len(ends)
    data=weather_payload_to_frame(payload,2022,2022)
    assert len(data)==8760
    assert data.index[0].tz_convert("Asia/Kolkata").year==2022
    assert data.index[-1].tz_convert("Asia/Kolkata").month==12
