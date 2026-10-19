# Data sources and data quality

- **Open-Meteo Geocoding API:** `https://geocoding-api.open-meteo.com/v1/search`. Filter `countryCode=IN`; return all candidate matches for explicit selection. PIN-code matching has not been validated or added.
- **Open-Meteo Historical Weather API:** `https://archive-api.open-meteo.com/v1/archive` (`models=era5`, hourly GHI, DNI, DHI, 2m temperature and 10m wind). Radiation is hourly mean W/m² for the *preceding hour*. Index shift by one hour makes each observation represent the start of its physical interval. Solar position is calculated at its midpoint. Per-hour power in kW is integrated over a one-hour step into kWh. Dates use UTC internal storage and `Asia/Kolkata` local billing boundaries.
- **Weather data quality:** strict hourly intervals, expected number of complete India-local calendar-year hours, correct units, finite values, no gaps, reasonable irradiance bounds. Hard errors instead of synthetic fallback. Cache key includes coordinates, dataset and year range; TTL 30 days. The free hosted Open-Meteo API is noncommercial. See https://open-meteo.com/en/pricing and follow required attribution.
- **pvlib:** https://pvlib-python.readthedocs.io/. Fixed-tilt geometry, irradiance transposition, Faiman temperature, PVWatts DC/inverter and clipping. Does not replace professional solar installation engineering.
- **Tariffs:** no officially verified utility tariff records included. Real tariff source would require DISCOM and regulator orders, effective dates, slabs, demand charges, fixed charges, taxes and export settlement rules. App only supports user-entered *illustrative* flat import and optional monthly export-credit scenarios.
- **Incentives:** no official subsidy eligibility applied. Sources to research include https://mnre.gov.in/ and state agencies. No verified incentives implemented.
- **PVGIS:** not implemented in this release; must use versioned API adapters before future integration.
- **ML measured generation:** no site-level Indian PV measurements integrated. Legacy OPSD German forecasting remains an independent experiment.

Data may be revised by providers; cached metadata records retrieval time. No live validation of external API responses was possible in the offline build environment.
