# RenewCalc — Solar feasibility calculator

RenewCalc helps people in India explore possible rooftop solar configurations using regional historical weather, roof dimensions, electricity demand and **user-entered** pricing. It compares system capacities and estimates annual production, self-consumption, bill impact and long-term economics.

This is a feasibility calculator, not an installation quote. No official DISCOM tariff, government subsidy or return is implied. The technical calculation engine remains available for developer review in this repository but detailed methodology pages are not exposed on the public website.

## What changed in this release

- Rebranded the Next.js site and report as **RenewCalc**; updated site font hierarchy and illustrated interactive globe.
- Replaced search-button-only location entry with 450 ms debounced Indian-city suggestions; stale requests are cancelled. The map is preserved as an alternative.
- Frontend now uses same-origin `/api/v1/` URLs. Next.js proxies requests server-side to FastAPI; this avoids browser-to-`localhost:8000` requests and unnecessary cross-origin browser configuration.
- Default weather period is **2023** (one representative historical year) for a quicker first assessment. Historical results and financial scenarios are still **estimates** rather than measured rooftop production or guaranteed outcomes. Broader weather periods remain available through the API.
- Cleaner status messages for network problems, slow provider responses and invalid inputs.
- Removed public research/documentation pages; GitHub profile and contact email are in the footer. Engineering docs remain in `docs/`.
- Retains `legacy/historical_forecasting/` containing the earlier RenewCast ML research project.

## Requirements

- Python 3.11 or 3.12
- Node.js 22
- Outbound HTTPS access to Open-Meteo for location and historical weather data

## Local development

From the **repository root**, open two terminals:

Terminal 1 — backend:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e './backend[test]'
cd backend
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. The front end proxies `/api/v1/...` requests to the backend from `RENEWCALC_BACKEND_URL`, which defaults to `http://127.0.0.1:8000` locally. Opening http://localhost:8000/api/v1/health should return `status: ok`.

**Important:** The Next.js development server and FastAPI server **must both be running**. An interactive map can load even if FastAPI is stopped; in that case searching and calculating cannot work.

### Docker Compose

```bash
docker compose up --build
```

Docker sets `RENEWCALC_BACKEND_URL=http://backend:8000` for the Next.js server. API requests are proxied across the internal Docker network, while the browser only calls `localhost:3000`.

## Test

```bash
cd backend
python -m pytest -q
```

From `frontend/`, run `npm run lint && npm run build` after installing packages. CI runs both suites.

## Deploy

Deploy Next.js on a server-supported Next.js host and FastAPI on a reachable Python service. Set `RENEWCALC_BACKEND_URL=https://your-real-backend.example` in the **Next.js build and runtime environment**; it is a **server-side** variable, not a `NEXT_PUBLIC_` variable. Rebuild after changing it.

Persist `RENEWCALC_DB_PATH` and `RENEWCALC_CACHE_DIR` outside ephemeral storage, or previously created assessment links may disappear after restarts. Both services must permit the backend to make outbound HTTPS connections to Open-Meteo. See `docs/DEPLOYMENT.md`.

## Data and assumptions

- Regional hourly historical weather: Open-Meteo ERA5, supplied on request.
- Solar simulation: pvlib, using configurable roof layout, tilt, azimuth, temperature effects and losses.
- Demand: an assumed hourly profile derived from the user's inputs, **not** a smart-meter measurement.
- Billing: user-supplied flat grid rate and optional assumed export compensation; no verified DISCOM tariffs, subsidies, demand charges or statutory settlement arrangements.
- Finance: 25-year cash flows with user-editable costs and escalation parameters. Results are scenarios, not guarantees.
- Data-provider outages, missing pvlib, missing backend, or unavailable persistent storage return errors; synthetic observations are **never** silently substituted in the live product.

Privacy: assessment results use unpredictable identifiers and expire after seven days, but those links are bearer URLs. Do not share sensitive details or use this as regulated financial advice.

## Project history

`legacy/historical_forecasting/` preserves the original RenewCast German solar generation ML forecasting application, models, drift monitor and tests. The new site is a feasibility calculation product; it does **not** claim to use a validated site-level machine learning predictor. See `docs/MIGRATION.md`.

Contact: vordelx01@gmail.com · GitHub: https://github.com/KrishKPal
