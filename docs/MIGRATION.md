# From RenewCast to RenewCalc

The previous project was RenewCast, a historical German-solar ML forecasting and model drift research portfolio. The new public product is **RenewCalc**, an India-focused solar feasibility calculator. The original ML research app is kept in `legacy/historical_forecasting/` and is not marketed as the operational modeling engine of RenewCalc.

The new frontend lives in `frontend/` (Next.js) and the new backend in `backend/` (FastAPI, pvlib, custom tariffs and finance). Public methodology, sources and about routes were removed in favor of concise inline explanations, but internal `docs/` remains for maintainers.

The folder names and source package under `legacy/historical_forecasting/` intentionally retain `renewcast` to preserve the earlier research code. Update your GitHub repository name separately only if desired; renaming the product does not automatically rename a GitHub repository.

Use a separate Git branch to integrate this package into an existing repository. It was built from files supplied in this chat, not from a verified current clone of your GitHub main branch.
