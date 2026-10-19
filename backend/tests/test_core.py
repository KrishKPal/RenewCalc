from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest
from app.schemas import AssessmentRequest, ConsumptionInput, TariffInput, FinancialInput, SiteInput
from app.services.consumption import assumed_load, energy_balance
from app.services.billing import bill_periods
from app.services.finance import financial_projection
from app.services.solar import maximum_modules
from app.services.assessment import candidate_module_counts


def test_capacity_respects_area_and_integer_modules():
    site = SiteInput(roof_area_m2=30, usable_fraction=0.5, packing_factor=0.8, panel_area_m2=2.5)
    assert maximum_modules(site)==4


def test_no_capacity_when_too_small():
    assert maximum_modules(SiteInput(roof_area_m2=1)) == 0


def test_monthly_load_energy_conservation():
    index = pd.date_range("2024-01-01", "2024-03-01", inclusive="left", freq="h", tz="Asia/Kolkata").tz_convert("UTC")
    load = assumed_load(index, ConsumptionInput(monthly_kwh=480, category="residential"))
    monthly = load.groupby(load.index.tz_convert("Asia/Kolkata").month).sum()
    assert monthly.to_dict() == pytest.approx({1:480,2:480})


def test_grid_balance_identity_and_nonnegative():
    index = pd.date_range("2024-01-01", periods=3, freq="h",tz="UTC")
    pv = pd.Series([0., 4., 2.], index=index)
    load = pd.Series([3.,1.,2.],index=index)
    balance = energy_balance(pv,load)
    assert np.allclose(balance.self_consumed_kwh+balance.grid_export_kwh, balance.solar_kwh)
    assert np.allclose(balance.self_consumed_kwh+balance.grid_import_kwh, balance.demand_kwh)
    assert (balance>=0).all().all()


def test_fixed_charges_remain_under_net_billing():
    idx = pd.date_range("2024-01-05",periods=2,freq="h",tz="Asia/Kolkata")
    balance = energy_balance(pd.Series([10.,10.],index=idx),pd.Series([1.,1.],index=idx))
    result = bill_periods(balance,TariffInput(mode="net_billing",import_rate_inr_kwh=8,export_rate_inr_kwh=8,fixed_charge_inr_month=150))
    assert result["solar_bill_inr"].iloc[0]==150
    assert result["baseline_inr"].iloc[0]==166


def test_no_export_credit_without_export_mode():
    idx = pd.date_range("2024-03-01",periods=2,freq="h",tz="UTC")
    result = bill_periods(energy_balance(pd.Series([5.,5.],index=idx),pd.Series([0.,1.],index=idx)), TariffInput())
    assert result.export_credit_inr.iloc[0] == 0


def test_cash_flows_npv_and_no_payback():
    p=FinancialInput(horizon_years=5,tariff_escalation_year=0,maintenance_fraction_year=0,
                     inverter_replacement_year=5,inverter_replacement_fraction=0,maintenance_escalation_year=0,
                     discount_rate_year=0, panel_degradation_year=0)
    result=financial_projection(100,30,p)
    assert result["npv_inr"]==50
    assert result["simple_payback_years"]==pytest.approx(100/30, abs=0.01)
    no=financial_projection(1000,30,p)
    assert no["simple_payback_years"] is None
    assert no["npv_inr"]==-850


def test_candidate_counts_include_endpoints_and_are_bounded():
    choices = candidate_module_counts(300)
    assert choices[0]==1 and choices[-1]==300 and len(choices)<=20


def test_validation_blocks_unsupported_metering_and_invalid_months():
    with pytest.raises(ValueError):
        TariffInput(mode="no_export",export_rate_inr_kwh=5)
    with pytest.raises(ValueError):
        ConsumptionInput(monthly_kwh_profile=[20,50])


def test_degradation_can_change_self_consumption_non_linearly():
    from app.services.assessment import future_bill_savings
    idx = pd.date_range("2024-01-01", periods=48, freq="h", tz="Asia/Kolkata")
    solar = pd.Series([10.]*48,index=idx)
    load = pd.Series([2.]*48,index=idx)
    tariff = TariffInput(import_rate_inr_kwh=8)
    f = FinancialInput(horizon_years=5, panel_degradation_year=0.05,
                       tariff_escalation_year=0)
    values = future_bill_savings(solar,load,tariff,f)
    # PV surplus means 5% generation degradation does not reduce bill savings.
    assert values == pytest.approx([48*2*8]*5)
