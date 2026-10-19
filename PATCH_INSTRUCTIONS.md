# RenewCalc UI / API reliability patch

This patch was generated against the **RenewCast 2.0 Implementation ZIP from this conversation**, not a live clone of your current GitHub branch.

## Apply on a new branch

1. Back up your project and commit local changes.
2. At repository root, extract `RenewCalc_Update_Patch.zip` (it contains paths like `frontend/app/assess/page.tsx`).
3. Remove the retired public routes:

```bash
rm -rf frontend/app/methodology frontend/app/sources frontend/app/about
```

4. Start the backend and frontend (two separate terminals; commands in README).
5. Keep `frontend/.env.local` with `RENEWCALC_BACKEND_URL=http://127.0.0.1:8000` (or deployed FastAPI URL). **Delete the old `NEXT_PUBLIC_API_BASE_URL` line**.
6. Visit `http://localhost:3000/api/v1/health` to verify Next.js is forwarding successfully. Then test autocomplete and assessment.

The patch retains the old German forecasting experiment under `legacy/historical_forecasting/`. It does not delete engineering `docs/` in the repository; it removes developer-facing documentation pages from the website.

## Changed files

- Frontend: `next.config.ts`, `lib/api.ts`, `app/assess/page.tsx`, `app/results/[id]/page.tsx`, `app/page.tsx`, `app/layout.tsx`, `app/globals.css`, `app/icon.svg`, `components/Nav.tsx`, `components/Footer.tsx`, `components/GlobeScene.tsx`, `package.json`, `.env.example`, `Dockerfile`.
- Backend: `app/main.py`, `app/schemas.py`, `app/services/providers.py`, `app/services/assessment.py`, `app/storage.py`, `app/report.py`, `pyproject.toml`, `tests/test_renewcalc_release.py`.
- Repo config & docs: `docker-compose.yml`, `.env.example`, `README.md`, `docs/DEPLOYMENT.md`, `docs/MIGRATION.md`, `docs/ARCHITECTURE.md`, `docs/DATA_SOURCES.md`, `docs/TARIFFS.md`, `scripts/refresh_weather.py`.

## Important checks

The frontend must be served by Next.js (not a static export). FastAPI must be running and able to access `https://geocoding-api.open-meteo.com` and `https://archive-api.open-meteo.com`. In a public deployment, set `RENEWCALC_BACKEND_URL` to an actual accessible backend URL; `localhost` is not valid unless Next.js and FastAPI run together in the same host namespace.

Running the assessment requires `pvlib`. A backend missing pvlib now responds with a useful `503` instead of an unexplained network error, but the real PV computation still needs a Python environment with installed dependencies and external network access. Public-hosting proxy timeouts may still require persistent hosting or an asynchronous-job design for slow provider calls.
