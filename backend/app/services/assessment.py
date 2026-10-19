"""Single source of truth for capacity optimization and assessment results."""
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from app.schemas import AssessmentRequest, TariffInput, FinancialInput
from app.services.billing import bill_periods
from app.services.consumption import assumed_load, energy_balance
from app.services.finance import financial_projection
from app.services.solar import maximum_modules, simulate_pv


def candidate_module_counts(max_modules: int, max_candidates: int = 18) -> list[int]:
    if max_modules < 1:
        return []
    if max_modules <= max_candidates:
        return list(range(1, max_modules + 1))
    return sorted(set([1, max_modules, *[max(1, int(round(x))) for x in np.linspace(1, max_modules, max_candidates)]]))


def future_bill_savings(solar: pd.Series, load: pd.Series,
                        tariff: TariffInput, finance: FinancialInput) -> list[float]:
    """Recompute hourly self-use and monthly export credits after each year's degradation.

    Costs are representative means across the observed sample weather years.
    User import tariff escalates; fixed charge cancels from before/after savings;
    user export credit remains constant, not assumed to grow with retail tariffs.
    """
    index = solar.index.tz_convert("Asia/Kolkata")
    year_code = index.year - min(index.year)
    month_code = year_code * 12 + index.month - 1
    month_count = int(month_code.max()) + 1
    years_observed = len(set(index.year))
    demand = load.to_numpy()
    output = solar.to_numpy()
    monthly_demand = np.bincount(month_code, weights=demand, minlength=month_count)
    savings = []
    for year in range(1, finance.horizon_years + 1):
        effective_solar = output * (1 - finance.panel_degradation_year) ** (year - 1)
        imported = np.maximum(demand - effective_solar, 0)
        exported = np.maximum(effective_solar - demand, 0)
        monthly_import = np.bincount(month_code, weights=imported, minlength=month_count)
        monthly_export = np.bincount(month_code, weights=exported, minlength=month_count)
        import_rate = tariff.import_rate_inr_kwh * (1 + finance.tariff_escalation_year) ** (year - 1)
        credit = (np.minimum(monthly_import * import_rate, monthly_export * tariff.export_rate_inr_kwh)
                  if tariff.mode == "net_billing" else 0)
        savings.append(float(((monthly_demand - monthly_import) * import_rate + credit).sum() / years_observed))
    return savings


def analyze(request: AssessmentRequest, weather: pd.DataFrame, weather_meta: dict) -> dict:
    cap = maximum_modules(request.site)
    if cap < 1:
        raise ValueError("Not enough usable roof area for one configured solar module")
    max_budget = request.finance.budget_inr
    price_per_module = request.site.panel_wp / 1000 * request.finance.installation_cost_inr_kwp
    if max_budget is not None:
        cap = min(cap, int(max_budget // price_per_module))
    if cap < 1:
        raise ValueError("Budget is insufficient for one solar module")
    load = assumed_load(weather.index, request.consumption)
    options = []
    candidates = candidate_module_counts(cap)
    # Fixed DC/AC ratio and percentage losses make PVWatts output linear in module count.
    # Simulate once to avoid repeating expensive solar-position calculations.
    solar_per_module = simulate_pv(weather, request.location.latitude, request.location.longitude, request.site, 1)
    for modules in candidates:
        solar = solar_per_module * modules
        balance = energy_balance(solar, load)
        bills = bill_periods(balance, request.tariff)
        annual_savings = float(bills["savings_inr"].sum()) / len(set(bills.index.get_level_values("year")))
        annual_generation = float(balance["solar_kwh"].sum()) / len(set(bills.index.get_level_values("year")))
        annual_self = float(balance["self_consumed_kwh"].sum()) / len(set(bills.index.get_level_values("year")))
        cap_kw = modules * request.site.panel_wp / 1000
        cost = cap_kw * request.finance.installation_cost_inr_kwp
        savings_series = future_bill_savings(solar, load, request.tariff, request.finance)
        finance = financial_projection(cost, annual_savings, request.finance, yearly_savings_override=savings_series)
        options.append({"modules": modules, "capacity_kwp": round(cap_kw, 3),
                        "annual_kwh": round(annual_generation, 2), "self_consumed_kwh": round(annual_self, 2),
                        "year_one_bill_savings_inr": round(annual_savings, 2),
                        "npv_inr": finance["npv_inr"], "simple_payback_years": finance["simple_payback_years"],
                        "capex_inr": finance["capex_inr"]})
    obj = request.finance.objective
    if obj == "max_npv":
        selected = max(options, key=lambda x: x["npv_inr"])
    elif obj == "min_payback":
        eligible = [x for x in options if x["simple_payback_years"] is not None]
        selected = min(eligible, key=lambda x: x["simple_payback_years"]) if eligible else max(options, key=lambda x: x["npv_inr"])
    elif obj == "max_self_consumption":
        selected = max(options, key=lambda x: x["self_consumed_kwh"])
    else:
        selected = max(options, key=lambda x: x["annual_kwh"])
    if selected["npv_inr"] <= 0:
        recommendation = "not_financially_attractive"
        rationale = "No evaluated configuration has positive NPV under the supplied assumptions."
    else:
        recommendation = "consider_installation"
        rationale = f"Selected {selected['capacity_kwp']:.2f} kWp using the '{obj}' objective; check rooftop suitability and tariff assumptions."
    solar = solar_per_module * selected["modules"]
    balance = energy_balance(solar, load)
    bills = bill_periods(balance, request.tariff)
    year_count = len(set(bills.index.get_level_values("year")))
    yearly_savings = float(bills["savings_inr"].sum()) / year_count
    financing = financial_projection(selected["capex_inr"], yearly_savings, request.finance,
                                    yearly_savings_override=future_bill_savings(solar, load, request.tariff, request.finance))
    yearly_gen = balance["solar_kwh"].groupby(balance.index.tz_convert("Asia/Kolkata").year).sum()
    # Deterministic stress scenarios, not calibrated probability intervals.
    local_years = solar.index.tz_convert("Asia/Kolkata").year
    annual_by_year = solar.groupby(local_years).sum()
    low_year = int(annual_by_year.idxmin())
    high_year = int(annual_by_year.idxmax())
    stressed = []
    for name, sample_year, capex_factor, escalation_adjustment in [
        ("Conservative", low_year, 1.10, -0.015),
        ("Expected", None, 1.0, 0.0),
        ("Optimistic", high_year, 0.90, 0.015),
    ]:
        indices = (local_years == sample_year) if sample_year is not None else np.ones(len(solar), dtype=bool)
        scenario_finance = request.finance.model_copy(update={
            "tariff_escalation_year": max(-0.1, min(0.3, request.finance.tariff_escalation_year + escalation_adjustment)),
        })
        scenario_savings = future_bill_savings(solar[indices], load[indices], request.tariff, scenario_finance)
        scenario_capex = selected["capex_inr"] * capex_factor
        scenario_projection = financial_projection(scenario_capex, scenario_savings[0], scenario_finance,
                                                   yearly_savings_override=scenario_savings)
        stressed.append({"name": name, "weather_reference_year": sample_year,
                         "capex_adjustment_pct": round(100 * (capex_factor - 1), 1),
                         "tariff_escalation_adjustment_pct_points": round(escalation_adjustment*100, 1),
                         "annual_generation_kwh": round(float(solar[indices].sum()) / (len(set(local_years[indices]))), 2),
                         "npv_inr": scenario_projection["npv_inr"],
                         "payback_years": scenario_projection["simple_payback_years"]})

    monthly = bills.groupby(level=1).mean(numeric_only=True)
    monthly_out = [{"month": int(idx),
                    "generation_kwh": round(float(item["solar_kwh"]), 1),
                    "demand_kwh": round(float(item["demand_kwh"]), 1),
                    "baseline_bill_inr": round(float(item["baseline_inr"]), 1),
                    "solar_bill_inr": round(float(item["solar_bill_inr"]), 1)}
                   for idx, item in monthly.iterrows()]
    # Limit hourly response size; full load simulation still uses all observations.
    hourly = balance.iloc[:24*14]
    hourly_out = [{"time": idx.isoformat(), "solar_kwh": round(float(row.solar_kwh), 3),
                   "demand_kwh": round(float(row.demand_kwh), 3),
                   "self_consumed_kwh": round(float(row.self_consumed_kwh), 3)}
                  for idx, row in hourly.iterrows()]
    return {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "location": request.location.model_dump(), "category": request.consumption.category,
        "status": recommendation, "explanation": rationale,
        "selected": selected, "finance": financing, "alternatives": options,
        "annual_generation_kwh": round(float(balance["solar_kwh"].sum()) / year_count, 2),
        "annual_demand_kwh": round(float(balance["demand_kwh"].sum()) / year_count, 2),
        "annual_self_consumed_kwh": round(float(balance["self_consumed_kwh"].sum()) / year_count, 2),
        "annual_export_kwh": round(float(balance["grid_export_kwh"].sum()) / year_count, 2),
        "annual_grid_import_kwh": round(float(balance["grid_import_kwh"].sum()) / year_count, 2),
        "annual_baseline_bill_inr": round(float(bills["baseline_inr"].sum()) / year_count, 2),
        "annual_solar_bill_inr": round(float(bills["solar_bill_inr"].sum()) / year_count, 2),
        "monthly": monthly_out, "sample_hours": hourly_out, "scenarios": stressed,
        "historical_annual_yield_kwh": [{"year": int(k), "generation_kwh": round(float(v), 2)} for k,v in yearly_gen.items()],
        "sources": [weather_meta, {"provider": "User-supplied tariff", "status": "user_provided",
                                   "note": "Simplified flat import and optional export credit; not an official DISCOM tariff."}],
        "assumptions": ["Hourly demand is a category-specific assumed profile, not metered data.",
                        "Usable roof area, shading, module price and orientation are user-supplied assumptions.",
                        "No tax, sanctioned demand charges, subsidies or regulated settlement carryovers are modeled.",
                        "Each financial year re-evaluates solar self-use and exported energy after assumed degradation; retail import tariffs escalate, export credit does not. Historical years are averaged.",
                        "Stress scenarios use lowest/highest observed weather-year yield, CAPEX +/-10%, and tariff escalation +/-1.5 percentage points; not calibrated confidence intervals.",
                        "Local structural/electrical approvals, distribution constraints, and commercial API licences require independent verification."],
        "input": request.model_dump(), "calculation_version": "renewcalc-feasibility-0.1",
    }
