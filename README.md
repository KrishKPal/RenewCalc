# RenewCalc — Solar feasibility calculator

RenewCalc helps people in India explore possible rooftop solar configurations using regional historical weather, roof dimensions, electricity demand and **user-entered** pricing. It compares system capacities and estimates annual production, self-consumption, bill impact and long-term economics.

This is a feasibility calculator, not an installation quote. No official DISCOM tariff, government subsidy or return is implied. The technical calculation engine remains available for developer review in this repository but detailed methodology pages are not exposed on the public website.


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

From `frontend/`, run `npm run lint && npm run build` after installing packages.


## Data and assumptions

- Regional hourly historical weather: Open-Meteo ERA5, supplied on request.
- Solar simulation: pvlib, using configurable roof layout, tilt, azimuth, temperature effects and losses.
- Demand: an assumed hourly profile derived from the user's inputs, **not** a smart-meter measurement.
- Billing: user-supplied flat grid rate and optional assumed export compensation; no verified DISCOM tariffs, subsidies, demand charges or statutory settlement arrangements.
- Finance: 25-year cash flows with user-editable costs and escalation parameters. Results are scenarios, not guarantees.
- Data-provider outages, missing pvlib, missing backend, or unavailable persistent storage return errors; synthetic observations are **never** silently substituted in the live product.
