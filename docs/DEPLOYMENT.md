# RenewCalc deployment notes

## Architecture

Browser -> Next.js `/api/v1/...` -> Next.js rewrite -> FastAPI `/api/v1/...` -> Open-Meteo / pvlib / SQLite.

The browser never accesses a private `localhost:8000` URL. The rewrite target is controlled by `RENEWCALC_BACKEND_URL` on the Next.js **server**. Never point it at `localhost` on public hosting unless FastAPI actually runs in that same host/network namespace.

## Development

From project root, start backend with `cd backend && uvicorn app.main:app --reload --port 8000`, and frontend with `cd frontend && npm run dev`. Set `RENEWCALC_BACKEND_URL=http://127.0.0.1:8000` in `frontend/.env.local` (copy from `frontend/.env.example`). Restart the Next.js server if the URL changes.

## Production

- Backend needs Python 3.11/3.12, installed pvlib and outbound HTTPS access to Open-Meteo.
- Configure backend persistent volumes: `RENEWCALC_DB_PATH` and `RENEWCALC_CACHE_DIR`.
- Deploy Next.js with the **server-side** `RENEWCALC_BACKEND_URL` pointing to the deployed FastAPI HTTPS URL (or internal service hostname when appropriate). Run a new build.
- Only enable external CORS with `RENEWCALC_CORS_ORIGINS` if directly exposing the FastAPI endpoint to browsers; same-origin proxy does not need frontend cross-origin traffic.
- Next.js rewrites work with a running Next.js server; `next export` and purely static hosting are unsupported.
- On serverless frontend hosting, large weather simulations may outlast function/proxy timeouts. Use a long-running Next.js service or a persistent backend/async job design before expanding workloads.
- SQLite assessment IDs are not durable across ephemeral instance restarts. Persist storage or move to a managed database.
- Open-Meteo free hosted data has licensing and usage constraints; confirm commercial-use permission before monetizing.
- Do not store secrets or identifiable consumer bills in source control. Verify provider attribution.

## Acceptance checks

1. `http://localhost:8000/api/v1/health` responds `ok`.
2. `http://localhost:3000/api/v1/health` responds via the proxy.
3. Typing `Pune` in the city field returns suggestions when Open-Meteo is reachable, or a helpful error otherwise.
4. Picking a map location still fills coordinates.
5. One real assessment produces a result, then a PDF, with no fabricated data.
6. Disconnect the backend and verify a useful error instead of an unexplained `Failed to fetch`.
7. Test a deployed app from another machine to confirm there is no localhost API dependency.
