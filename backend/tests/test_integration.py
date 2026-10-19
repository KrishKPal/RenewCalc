import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app


def test_create_get_and_pdf_smoke(monkeypatch,tmp_path):
    from app import main, storage
    from app.services import assessment
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "results.db")
    dates=pd.date_range("2023-01-01", "2023-12-31 23:00",freq="h",tz="Asia/Kolkata").tz_convert("UTC")
    hr=dates.tz_convert("Asia/Kolkata").hour.to_numpy()
    ghi=750*np.maximum(0,np.sin(np.pi*(hr-6)/12))
    weather=pd.DataFrame({"shortwave_radiation":ghi},index=dates)
    def fake_weather(*args):
        return weather,{"provider":"Synthetic test fixture","dataset":"fixture","retrieved_at":"2024-01-01T00:00:00+00:00"}
    def fake_pv(weather,lat,lon,site,modules):
        return pd.Series(weather.shortwave_radiation.to_numpy()/1000*site.panel_wp/1000*modules,index=weather.index)
    monkeypatch.setattr(main,"fetch_weather",fake_weather)
    monkeypatch.setattr(assessment,"simulate_pv",fake_pv)
    payload={"location":{"name":"Pune","latitude":18.5,"longitude":73.8},
             "site":{"roof_area_m2":40},"consumption":{"monthly_kwh":350},
             "tariff":{"mode":"no_export","import_rate_inr_kwh":8},
             "finance":{"installation_cost_inr_kwp":42000},
             "weather_start_year":2023,"weather_end_year":2023}
    client=TestClient(app)
    created=client.post("/api/v1/assessments",json=payload)
    assert created.status_code==201,created.text
    result=created.json();id_=result["id"]
    assert result["result"]["annual_generation_kwh"]>0
    assert len(result["result"]["finance"]["cash_flows"])==26
    assert len(result["result"]["monthly"])==12
    assert len(result["result"]["scenarios"]) == 3
    assert client.get(f"/api/v1/assessments/{id_}").status_code==200
    pdf=client.get(f"/api/v1/assessments/{id_}/report")
    assert pdf.status_code==200 and pdf.content.startswith(b"%PDF")
    assert client.get("/api/v1/assessments/not-real").status_code==404
