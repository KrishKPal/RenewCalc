"""Unlevered project economics; no implied vendor quote or government subsidy."""
import numpy as np
from scipy.optimize import brentq
from app.schemas import FinancialInput


def financial_projection(capex_inr: float, first_year_savings_inr: float,
                         params: FinancialInput, savings_decay_year: float = 0.0,
                         yearly_savings_override: list[float] | None = None) -> dict:
    if yearly_savings_override is not None and len(yearly_savings_override) != params.horizon_years:
        raise ValueError("Yearly bill-savings list must match the analysis horizon")
    flows = [-capex_inr]
    rows = [{"year": 0, "net_cash_flow_inr": -capex_inr, "cumulative_inr": -capex_inr}]
    cumulative = -capex_inr
    payback = None
    discounted_payback = None
    discounted_running = -capex_inr
    for year in range(1, params.horizon_years + 1):
        tariff_factor = (1 + params.tariff_escalation_year) ** (year - 1)
        generation_factor = (1 - savings_decay_year) ** (year - 1)
        gross_savings = (yearly_savings_override[year - 1] if yearly_savings_override is not None
                         else first_year_savings_inr * generation_factor * tariff_factor)
        maintenance = capex_inr * params.maintenance_fraction_year * (1 + params.maintenance_escalation_year) ** (year - 1)
        replacement = capex_inr * params.inverter_replacement_fraction if year == params.inverter_replacement_year else 0
        cash_flow = gross_savings - maintenance - replacement
        previous = cumulative
        cumulative += cash_flow
        discounted_before = discounted_running
        discounted_running += cash_flow / (1 + params.discount_rate_year) ** year
        if payback is None and cumulative >= 0 and previous < 0 and cash_flow > 0:
            payback = year - 1 + (-previous / cash_flow)
        if discounted_payback is None and discounted_running >= 0 and discounted_before < 0 and cash_flow > 0:
            discounted_payback = year - 1 + (-discounted_before / (cash_flow / (1 + params.discount_rate_year) ** year))
        flows.append(cash_flow)
        rows.append({"year": year, "net_cash_flow_inr": round(cash_flow, 2),
                     "cumulative_inr": round(cumulative, 2),
                     "gross_bill_savings_inr": round(gross_savings, 2),
                     "maintenance_inr": round(maintenance, 2), "replacement_inr": round(replacement, 2)})
    net_present_value = sum(flow / (1 + params.discount_rate_year) ** year for year, flow in enumerate(flows))
    irr = None
    def npv_at(rate: float) -> float:
        return sum(flow / (1 + rate) ** year for year, flow in enumerate(flows))
    if any(flow > 0 for flow in flows) and any(flow < 0 for flow in flows):
        try:
            if npv_at(-0.95) * npv_at(5) < 0:
                candidate = brentq(npv_at, -0.95, 5)
                # Multiple sign changes can yield ambiguous IRR; decline to report one.
                if sum(np.sign(flows[i]) != np.sign(flows[i - 1]) for i in range(1, len(flows)) if flows[i] and flows[i - 1]) == 1:
                    irr = float(candidate)
        except (ValueError, OverflowError, ZeroDivisionError):
            pass
    return {
        "capex_inr": round(capex_inr, 2), "npv_inr": round(net_present_value, 2),
        "lifetime_net_benefit_inr": round(cumulative, 2),
        "irr_pct": round(100 * irr, 2) if irr is not None and np.isfinite(irr) else None,
        "simple_payback_years": round(payback, 2) if payback is not None else None,
        "discounted_payback_years": round(discounted_payback, 2) if discounted_payback is not None else None,
        "cash_flows": rows,
    }
