export const API = ""; // Use same-origin Next.js proxy. Never expose a localhost backend to visitors.

export type LocationCandidate = {
  id: number | null; name: string; admin1: string | null; country: string;
  country_code: string; latitude: number; longitude: number; timezone: string | null;
};

export type AssessmentResult = {
  id: string;
  result: {
    computed_at: string;
    status: string;
    explanation: string;
    location: { name: string; latitude: number; longitude: number };
    selected: {capacity_kwp: number; annual_kwh: number; capex_inr: number; year_one_bill_savings_inr: number;
      npv_inr: number; modules: number; simple_payback_years: number | null};
    finance: {npv_inr: number; irr_pct: number | null; simple_payback_years: number | null;
      discounted_payback_years: number | null; lifetime_net_benefit_inr: number;
      cash_flows: Array<{year: number; net_cash_flow_inr: number; cumulative_inr: number}>};
    annual_generation_kwh: number; annual_demand_kwh: number;
    annual_self_consumed_kwh: number; annual_export_kwh: number; annual_grid_import_kwh: number;
    annual_baseline_bill_inr: number; annual_solar_bill_inr: number;
    monthly: Array<{month: number; generation_kwh: number; demand_kwh: number; baseline_bill_inr: number; solar_bill_inr: number}>;
    sample_hours: Array<{time: string; solar_kwh: number; demand_kwh: number; self_consumed_kwh: number}>;
    historical_annual_yield_kwh: Array<{year: number; generation_kwh: number}>;
    scenarios: Array<{name: string; weather_reference_year: number | null; capex_adjustment_pct: number; tariff_escalation_adjustment_pct_points: number; annual_generation_kwh: number; npv_inr: number; payback_years: number | null}>;
    alternatives: Array<{modules: number; capacity_kwp: number; annual_kwh: number;
      npv_inr: number; capex_inr: number; simple_payback_years: number | null}>;
    sources: Array<{provider: string; dataset?: string; url?: string; retrieved_at?: string; status?: string}>;
    assumptions: string[]; calculation_version: string;
  };
};

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method?.toUpperCase() || "GET";
  const timeoutMs = method === "POST" ? 120000 : 20000;
  let response: Response;
  try {
    response = await fetch(`/api/v1/${path.replace(/^\/?api\/v1\//, "").replace(/^\//, "")}`, {
      cache: "no-store",
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof DOMException && (error.name === "TimeoutError" || error.name === "AbortError")) {
      throw new Error(method === "POST"
        ? "This calculation is taking too long. Please try again. If it continues, check the backend logs."
        : "The service is taking too long to respond. Please try again.");
    }
    throw new Error("Could not reach RenewCalc. Please check your connection and try again. If this continues, the calculation service may be offline.");
  }
  if (!response.ok) {
    let message = `The service returned an error (${response.status}).`;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") message = payload.detail;
      else if (Array.isArray(payload.detail)) {
        message = payload.detail.map((item: {msg?: string}) => item.msg || "Invalid field").join("; ");
      }
    } catch { /* Proxy errors may be HTML. */ }
    if ([502, 503, 504].includes(response.status) && message.startsWith("The service returned")) {
      message = "The calculation service is unavailable or still starting. Try again shortly and check the FastAPI terminal if running locally.";
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const money = (n: number) => new Intl.NumberFormat("en-IN", {style: "currency", currency: "INR", maximumFractionDigits: 0}).format(n);
export const number = (n: number, digits = 0) => new Intl.NumberFormat("en-IN", {maximumFractionDigits: digits}).format(n);
