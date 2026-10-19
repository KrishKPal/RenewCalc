# Machine learning status

The new feasibility website deliberately uses physical solar simulation rather than an unvalidated site-level ML regressor. It has no claim of measured Indian PV site model MAE or calibrated uncertainty. Existing historical German solar generation forecasting, validation metrics and drift experiments remain in `legacy/historical_forecasting`.

A future legitimate PV residual-correction experiment requires consented measured, timestamped site generation data, actual site geometry/capacity, matching weather, chronological site-aware splits, physics-only baseline, held-out evaluation, and physical zero-at-night constraints. Do not train on simulated production as if it were independently measured ground truth.
