"""Construct explicitly assumed hourly demand while conserving monthly totals."""
import numpy as np
import pandas as pd
from app.schemas import ConsumptionInput


def assumed_load(index: pd.DatetimeIndex, data: ConsumptionInput) -> pd.Series:
    if index.tz is None:
        raise ValueError("Load timestamps must be timezone-aware")
    hours_local = index.tz_convert("Asia/Kolkata")
    hours = hours_local.hour
    is_weekend = hours_local.dayofweek >= 5
    if data.category == "residential":
        weights = 0.55 + np.where((hours >= 6) & (hours < 9), 0.65, 0) + np.where((hours >= 18) & (hours < 23), 1.35, 0)
    elif data.category == "farm":
        weights = 0.35 + np.where((hours >= 6) & (hours < 18), 1.4, 0)
    else:
        in_operation = (hours >= data.operating_start_hour) & (hours < data.operating_end_hour)
        weights = 0.25 + np.where(in_operation, 2, 0)
        if data.category in {"commercial", "institutional"}:
            weights = weights * np.where(is_weekend, 0.5, 1)
    series = pd.Series(np.asarray(weights, dtype=float), index=index, name="load_kwh")
    buckets = pd.MultiIndex.from_arrays([hours_local.year, hours_local.month])
    denominators = series.groupby(buckets).transform("sum")
    profile = data.monthly_kwh_profile or [data.monthly_kwh] * 12
    monthly_targets = np.array(profile, dtype=float)[hours_local.month - 1]
    return (series / denominators * monthly_targets).rename("load_kwh")


def energy_balance(solar_kwh: pd.Series, load_kwh: pd.Series) -> pd.DataFrame:
    if not solar_kwh.index.equals(load_kwh.index):
        raise ValueError("Solar and load timestamps must align")
    if solar_kwh.isna().any() or load_kwh.isna().any() or (solar_kwh < 0).any() or (load_kwh < 0).any():
        raise ValueError("Solar and demand must be finite nonnegative values")
    solar = solar_kwh.to_numpy()
    load = load_kwh.to_numpy()
    self_use = np.minimum(solar, load)
    return pd.DataFrame({
        "solar_kwh": solar, "demand_kwh": load, "self_consumed_kwh": self_use,
        "grid_import_kwh": np.maximum(0, load - solar),
        "grid_export_kwh": np.maximum(0, solar - load),
    }, index=solar_kwh.index)
