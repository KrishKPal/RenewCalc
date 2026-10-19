"""Provider adapters. Live failures remain failures; no fabricated weather fallback."""
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARIABLES = [
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation",
    "temperature_2m", "wind_speed_10m",
]
CACHE_ROOT = Path(os.getenv("RENEWCALC_CACHE_DIR", str(Path(__file__).resolve().parents[2] / ".cache" / "renewcalc")))


class ProviderError(RuntimeError):
    pass


def get_json(url: str, params: dict, client: httpx.Client | None = None) -> dict:
    # Requests never silently fall back to invented irradiance data.
    try:
        if client is not None:
            response = client.get(url, params=params, timeout=35)
        else:
            timeout = httpx.Timeout(35, connect=8)
            with httpx.Client(timeout=timeout, follow_redirects=False) as session:
                response = session.get(url, params=params)
        response.raise_for_status()
        result = response.json()
    except httpx.TimeoutException as exc:
        raise ProviderError("The data provider did not respond in time. Please retry shortly.") from exc
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code == 429:
            message = "The weather or location service is busy. Please try again shortly."
        else:
            message = f"The data provider returned HTTP {code}. Please retry later."
        raise ProviderError(message) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise ProviderError(f"Could not retrieve provider data ({type(exc).__name__}). Check network access and try again.") from exc
    if not isinstance(result, dict):
        raise ProviderError("The data provider returned an unexpected response.")
    if result.get("error"):
        raise ProviderError(f"The data provider rejected this request: {result.get('reason', 'unknown reason')}")
    return result


def search_locations(query: str, client: httpx.Client | None = None) -> list[dict]:
    if len(query.strip()) < 2 or len(query) > 80:
        raise ValueError("Search query must contain 2–80 characters")
    payload = get_json(GEOCODE_URL, {"name": query, "count": 10, "language": "en", "format": "json", "countryCode": "IN"}, client)
    results = []
    for item in payload.get("results", []):
        if item.get("country_code") != "IN":
            continue
        results.append({key: item.get(key) for key in (
            "id", "name", "admin1", "country", "country_code", "latitude", "longitude", "timezone"
        )})
    return results


def weather_payload_to_frame(payload: dict, start_year: int, end_year: int) -> pd.DataFrame:
    hourly = payload.get("hourly")
    units = payload.get("hourly_units", {})
    if not isinstance(hourly, dict) or any(key not in hourly for key in ["time", *WEATHER_VARIABLES]):
        raise ProviderError("Historical weather response is missing hourly fields")
    for key in ("shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation"):
        if units.get(key) != "W/m²":
            raise ProviderError(f"Unexpected {key} unit: {units.get(key)}")
    if units.get("temperature_2m") != "°C" or units.get("wind_speed_10m") != "km/h":
        raise ProviderError("Unexpected weather temperature or wind units")
    values = hourly["time"]
    if not isinstance(values, list) or not values:
        raise ProviderError("No hourly observations returned")
    timestamps = pd.to_datetime(values, unit="s", utc=True)
    # Open-Meteo radiation values are averages over the preceding hour.
    # Label each interval by its beginning for billing and solar position.
    timestamps = timestamps - pd.Timedelta(hours=1)
    try:
        frame = pd.DataFrame({name: pd.to_numeric(hourly[name], errors="raise") for name in WEATHER_VARIABLES}, index=timestamps)
    except (ValueError, TypeError) as exc:
        raise ProviderError("Weather payload contains nonnumeric values") from exc
    if frame.isna().any().any() or not np.isfinite(frame.to_numpy()).all():
        raise ProviderError("Weather observations contain missing or infinite values")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ProviderError("Weather timestamps are duplicated or unordered")
    if not (frame.index.to_series().diff().dropna() == pd.Timedelta(hours=1)).all():
        raise ProviderError("Historical weather has missing hourly intervals")
    if len(frame) < 24 * 300:
        raise ProviderError("Historical weather contains fewer than 300 days")
    for col in WEATHER_VARIABLES[:3]:
        if (frame[col] < -1).any() or (frame[col] > 1450).any():
            raise ProviderError(f"Implausible irradiance in {col}")
        frame[col] = frame[col].clip(lower=0)
    if not frame.index[0].year <= start_year <= end_year <= frame.index[-1].year:
        raise ProviderError("Weather date coverage does not include requested years")
    local_year = frame.index.tz_convert("Asia/Kolkata").year
    frame = frame[(local_year >= start_year) & (local_year <= end_year)]
    # January/December boundary requests include one extra day on each side.
    expected = sum(8784 if pd.Timestamp(y, 12, 31).is_leap_year else 8760 for y in range(start_year, end_year + 1))
    if len(frame) != expected:
        raise ProviderError(f"Weather coverage incomplete: expected {expected} hours, got {len(frame)}")
    return frame


def fetch_weather(latitude: float, longitude: float, start_year: int, end_year: int,
                  client: httpx.Client | None = None) -> tuple[pd.DataFrame, dict]:
    params = {
        "latitude": latitude, "longitude": longitude, "start_date": f"{start_year-1}-12-31",
        "end_date": f"{end_year+1}-01-01", "hourly": ",".join(WEATHER_VARIABLES),
        "timezone": "GMT", "timeformat": "unixtime", "models": "era5",
    }
    cache_key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    cache_file = CACHE_ROOT / f"weather-{cache_key}.json"
    ttl_seconds = 30 * 24 * 3600
    if cache_file.exists() and time.time() - cache_file.stat().st_mtime < ttl_seconds:
        try:
            payload = json.loads(cache_file.read_text())
            data = weather_payload_to_frame(payload, start_year, end_year)
            return data, {"provider": "Open-Meteo", "dataset": "ERA5", "url": ARCHIVE_URL,
                          "cache": "hit", "retrieved_at": datetime.fromtimestamp(cache_file.stat().st_mtime, timezone.utc).isoformat(),
                          "reference_years": [start_year, end_year]}
        except (ValueError, ProviderError, OSError):
            pass
    payload = get_json(ARCHIVE_URL, params, client)
    data = weather_payload_to_frame(payload, start_year, end_year)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        temp = cache_file.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, separators=(",", ":")))
        temp.replace(cache_file)
    except OSError:
        pass  # A read-only deployment can calculate without a disk cache.
    return data, {"provider": "Open-Meteo", "dataset": "ERA5", "url": ARCHIVE_URL,
                  "cache": "miss", "retrieved_at": datetime.now(timezone.utc).isoformat(),
                  "reference_years": [start_year, end_year]}
