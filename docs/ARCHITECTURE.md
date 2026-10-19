# Architecture

```text
React / Next.js (browser)
    │ GET locations / POST assessments / GET results / GET PDF
    ▼
FastAPI backend (validated Pydantic contracts)
    ├─ Open-Meteo geocoding adapter
    ├─ Open-Meteo ERA5 historical weather adapter → local keyed cache
    ├─ pvlib solar geometry, irradiance, DC and AC simulation
    ├─ Hourly assumed load → energy balance → simplified billing
    ├─ Feasible capacity comparison → unlevered financial model
    ├─ ReportLab PDF built from persisted results
    └─ SQLite result storage (7-day retention, unguessable UUID identifiers)
```

No ML correction is used for site-level feasibility without measured site training data. Previous German ML backtesting code lives in `legacy/historical_forecasting/` and is completely independent.

**Current limitations:** The frontend uses selected coordinates but does not resolve DISCOM service territories or exact property footprints. The fixed-price billing model does not support actual slab/tax/demand-net-metering rules. Result storage must be placed on persistent storage when deployed; do not assume filesystem persistence on ephemeral hosts. SQLite storage is anonymous with UUID4 possession-based access and should not store confidential bills. If production requires accounts and private records, design authenticated, permissioned access rather than extending public anonymous links.
