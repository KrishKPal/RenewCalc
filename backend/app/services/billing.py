"""User-specified simple net billing; not an official regulated tariff model."""
import pandas as pd
from app.schemas import TariffInput


def bill_periods(balance: pd.DataFrame, tariff: TariffInput) -> pd.DataFrame:
    if balance.index.tz is None:
        raise ValueError("Billing requires timezone-aware timestamps")
    local = balance.index.tz_convert("Asia/Kolkata")
    periods = balance.groupby([local.year, local.month]).sum(numeric_only=True)
    periods.index.names = ["year", "month"]
    periods["baseline_inr"] = periods["demand_kwh"] * tariff.import_rate_inr_kwh + tariff.fixed_charge_inr_month
    energy_charge = periods["grid_import_kwh"] * tariff.import_rate_inr_kwh
    raw_credit = periods["grid_export_kwh"] * tariff.export_rate_inr_kwh if tariff.mode == "net_billing" else 0
    # Assumed credit can offset variable energy charges, never fixed charges.
    periods["export_credit_inr"] = pd.Series(raw_credit, index=periods.index).clip(lower=0).combine(energy_charge, min)
    periods["solar_bill_inr"] = energy_charge - periods["export_credit_inr"] + tariff.fixed_charge_inr_month
    periods["savings_inr"] = periods["baseline_inr"] - periods["solar_bill_inr"]
    return periods
