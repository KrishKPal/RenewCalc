"use client";
import { FormEvent, useEffect, useState } from "react";
import dynamic from "next/dynamic";
const LocationMap = dynamic(() => import("@/components/LocationMap"), {ssr: false});
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2, Search, AlertCircle, CloudSun, Calculator, MapPin, ClipboardCheck, LoaderCircle } from "lucide-react";
import { apiJson, LocationCandidate, money } from "@/lib/api";

type Form = {
  place: string; latitude: string; longitude: string; locationName: string;
  category: string; roofArea: string; usableFraction: string; panelWp: string; panelArea: string;
  tilt: string; azimuth: string; shade: string; soiling: string; wiring: string; inverterRatio: string;
  monthlyKwh: string; operatingStart: string; operatingEnd: string;
  importRate: string; exportRate: string; fixedCharge: string; exportMode: string;
  installationCost: string; maintenance: string; maintenanceEscalation: string; degradation: string; escalation: string;
  discount: string; budget: string; objective: string;
};
const defaults: Form = {
  place: "", latitude: "", longitude: "", locationName: "", category: "residential",
  roofArea: "70", usableFraction: "70", panelWp: "550", panelArea: "2.6",
  tilt: "20", azimuth: "180", shade: "8", soiling: "3", wiring: "2", inverterRatio: "85",
  monthlyKwh: "450", operatingStart: "9", operatingEnd: "18", importRate: "8",
  exportRate: "0", fixedCharge: "150", exportMode: "no_export", installationCost: "55000",
  maintenance: "1", maintenanceEscalation: "3", degradation: "0.5", escalation: "3", discount: "8", budget: "",
  objective: "max_npv"
};
const steps = ["Location", "Site & system", "Consumption & tariff", "Economics", "Review"];
const categories = ["residential", "commercial", "industrial", "farm", "institutional"];
const objectives = [
  ["max_npv", "Best net present value"], ["min_payback", "Shortest payback"],
  ["max_self_consumption", "Most directly used solar"], ["max_generation", "Highest annual generation"]
];

export default function AssessPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>(defaults);
  const [locations, setLocations] = useState<LocationCandidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const [detailedDemand, setDetailedDemand] = useState(false);
  const [monthlyValues, setMonthlyValues] = useState<string[]>(Array(12).fill("450"));
  const [showMap, setShowMap] = useState(false);
  const [locationChosen, setLocationChosen] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [waitingSeconds, setWaitingSeconds] = useState(0);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem("renewcalc-form-v1") ?? sessionStorage.getItem("renewcast-form-v1");
      if (stored) {
        const restored = {...defaults, ...JSON.parse(stored)};
        setForm(restored);
        setLocationChosen(Boolean(restored.locationName && restored.latitude && restored.longitude));
      }
      const monthlyStored = sessionStorage.getItem("renewcalc-months-v1") ?? sessionStorage.getItem("renewcast-months-v1");
      if (monthlyStored) { const payload = JSON.parse(monthlyStored); if (Array.isArray(payload.values) && payload.values.length===12) { setMonthlyValues(payload.values); setDetailedDemand(!!payload.enabled); } }
    } catch { /* Storage is optional. */ }
  }, []);
  useEffect(() => {
    try { sessionStorage.setItem("renewcalc-form-v1", JSON.stringify(form)); } catch { /* Private browsing may block storage. */ }
  }, [form]);
  useEffect(() => { try {sessionStorage.setItem("renewcalc-months-v1",JSON.stringify({enabled:detailedDemand,values:monthlyValues}));} catch {} },[detailedDemand,monthlyValues]);
  const update = (key: keyof Form, value: string) => setForm(previous => ({...previous, [key]: value}));
  const field = (key: keyof Form, label: string, suffix = "", help = "", min?: number, max?: number) =>
    <div className="field"><label htmlFor={key}>{label}{suffix ? ` (${suffix})` : ""}</label>
      <input id={key} type="number" inputMode="decimal" min={min} max={max} step="any" value={form[key]}
             onChange={event => update(key, event.target.value)}/>{help && <span className="field-help">{help}</span>}</div>;

  useEffect(() => {
    const query = form.place.trim();
    if (locationChosen || query.length < 3) {
      setLocations([]);
      setSearching(false);
      setSearchError("");
      return;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setSearching(true);
      setSearchError("");
      try {
        const results = await apiJson<LocationCandidate[]>(
          `/api/v1/locations/search?q=${encodeURIComponent(query)}`,
          {signal: controller.signal}
        );
        if (!controller.signal.aborted) {
          setLocations(results);
          if (results.length === 0) setSearchError("No matches found. You can also choose a point on the map.");
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setLocations([]);
          setSearchError(err instanceof Error ? err.message : "Location search is unavailable. Try the map.");
        }
      } finally {
        if (!controller.signal.aborted) setSearching(false);
      }
    }, 450);
    return () => {window.clearTimeout(timer); controller.abort();};
  }, [form.place, locationChosen]);

  useEffect(() => {
    if (!loading) {setWaitingSeconds(0); return;}
    const started = Date.now();
    const interval = window.setInterval(() => setWaitingSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(interval);
  }, [loading]);

  const choose = (item: LocationCandidate) => {
    setLocationChosen(true);
    setForm(previous => ({...previous, latitude: String(item.latitude), longitude: String(item.longitude),
      locationName: `${item.name}${item.admin1 ? `, ${item.admin1}` : ""}, India`, place: item.name}));
    setLocations([]); setSearchError(""); setError("");
  };
  const selectMapPoint = (lat: number, lon: number) => {
    setLocationChosen(true);
    setLocations([]);
    setSearchError("");
    setForm(previous => ({...previous, place: "", latitude: String(lat), longitude: String(lon),
      locationName: `Map selection near ${lat.toFixed(3)}, ${lon.toFixed(3)}, India`}));
  };
  const validateStep = (index: number): string => {
    if (index === 0 && (!form.locationName.trim() || form.latitude === "" || form.longitude === "" || !Number.isFinite(Number(form.latitude)) || !Number.isFinite(Number(form.longitude)) || Math.abs(Number(form.latitude)) > 90 || Math.abs(Number(form.longitude)) > 180))
      return "Select a search result or enter valid latitude, longitude and a location name.";
    if (index === 1 && (+form.roofArea <= 0 || +form.panelArea <= 0 || +form.panelWp <= 0)) return "Enter positive roof area and panel specifications.";
    if (index === 2 && (+form.monthlyKwh <= 0 || +form.importRate < 0 || +form.fixedCharge < 0)) return "Enter valid monthly demand and tariff assumptions.";
    if (index === 2 && detailedDemand && (monthlyValues.some(value=>value==="" || !Number.isFinite(+value) || +value<0) || monthlyValues.reduce((sum,value)=>sum + +value,0)<=0)) return "Enter 12 nonnegative monthly kWh values, with at least one positive month.";
    if (index === 3 && (+form.installationCost <= 0 || (form.budget && +form.budget <= 0))) return "Enter a positive installation-cost estimate and budget.";
    return "";
  };
  const goNext = () => {
    const issue = validateStep(step); if (issue) { setError(issue); return; }
    setError(""); setStep(n => Math.min(4, n+1));
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError("");
    for (let i=0; i<4; i++) {const problem = validateStep(i); if (problem) {setStep(i); setError(problem); return;}}
    setLoading(true);
    const pct = (v: string) => Number(v) / 100;
    const payload = {
      location: {name: form.locationName, latitude: +form.latitude, longitude: +form.longitude, timezone: "Asia/Kolkata", country_code: "IN"},
      site: {roof_area_m2: +form.roofArea, usable_fraction: pct(form.usableFraction),
        panel_wp: +form.panelWp, panel_area_m2: +form.panelArea, tilt_deg: +form.tilt, azimuth_deg: +form.azimuth,
        inverter_ratio: pct(form.inverterRatio), shading_loss: pct(form.shade), soiling_loss: pct(form.soiling),
        wiring_loss: pct(form.wiring), packing_factor: 0.85},
      consumption: {category: form.category, monthly_kwh: +form.monthlyKwh,
        monthly_kwh_profile: detailedDemand ? monthlyValues.map(Number) : null,
        operating_start_hour: +form.operatingStart, operating_end_hour: +form.operatingEnd},
      tariff: {mode: form.exportMode, import_rate_inr_kwh: +form.importRate,
        export_rate_inr_kwh: form.exportMode === "no_export" ? 0 : +form.exportRate,
        fixed_charge_inr_month: +form.fixedCharge, source: "user_provided"},
      finance: {installation_cost_inr_kwp: +form.installationCost,
        maintenance_fraction_year: pct(form.maintenance), maintenance_escalation_year: pct(form.maintenanceEscalation), panel_degradation_year: pct(form.degradation),
        tariff_escalation_year: pct(form.escalation), discount_rate_year: pct(form.discount),
        budget_inr: form.budget ? +form.budget : null, objective: form.objective},
      weather_start_year: 2023, weather_end_year: 2023
    };
    try {
      const data = await apiJson<{id: string}>("/api/v1/assessments", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
      router.push(`/results/${data.id}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Assessment failed."); }
    finally { setLoading(false); }
  };

  return <div className="page-shell"><div className="container"><div className="page-header">
    <p className="kicker">YOUR SOLAR ASSESSMENT</p><h1>Your rooftop, in numbers.</h1>
    <p>Start with your location, then tell us about your space and electricity use. We’ll calculate a solar scenario that fits your inputs.</p>
  </div><div className="wizard-layout"><aside className="wizard-nav"><h3>Your assessment</h3>{steps.map((title,i)=><div key={title} className={`wizard-step ${i===step?"active":""}`}><span className="step-number">{i<step?<CheckCircle2 size={16}/>:i+1}</span>{title}</div>)}<div className="wizard-tip" style={{marginTop:24}}>Tip: Have a recent electricity bill handy for better estimates.</div></aside>
  <form className="panel form-panel" onSubmit={submit}><div className="progress" role="progressbar" aria-label="Assessment progress" aria-valuenow={step+1} aria-valuemin={1} aria-valuemax={5}><div style={{width:`${(step+1)*20}%`}}/></div>
    {step===0 && <><h2><MapPin size={25} style={{display:"inline",verticalAlign:"middle",marginRight:10}}/>Where is the installation?</h2><p>Search a city or drop a pin on the map. We’ll use it to find your area’s solar weather.</p>
      <div className="field location-search-field"><label htmlFor="place">Your city or locality</label>
        <div className="search-input-wrap"><Search size={20} aria-hidden="true"/><input id="place" autoComplete="off"
          aria-autocomplete="list" aria-controls="city-suggestions" aria-expanded={locations.length > 0}
          value={form.place} onChange={e=>{
            setLocationChosen(false); setSearchError(""); setError(""); setLocations([]);
            setForm(previous => ({...previous, place:e.target.value, latitude:"", longitude:"", locationName:""}));
          }} placeholder="Try Pune, Mumbai or Bengaluru" />
          {searching && <LoaderCircle size={18} className="search-spinner" aria-label="Finding places"/>}</div>
        <span className="field-help">Type at least three characters. Select a result to confirm the location.</span></div>
      {locations.length>0 && <div className="location-results" id="city-suggestions" role="listbox" aria-label="Matching locations">{locations.map((loc,i)=><button type="button" role="option" aria-selected="false" key={`${loc.id}-${i}`} className="location-option" onClick={()=>choose(loc)}><span><MapPin size={16}/> {loc.name}{loc.admin1 ? `, ${loc.admin1}` : ""}, India</span><span>Choose <ArrowRight size={15}/></span></button>)}</div>}
      {searchError && <div role="status" className="search-feedback">{searchError}</div>}
      {form.locationName && <div className="alert alert-info"><CheckCircle2 size={18}/> Selected: {form.locationName} ({(+form.latitude).toFixed(3)}, {(+form.longitude).toFixed(3)})</div>}
      <button type="button" className="text-link" onClick={()=>setShowMap(!showMap)} style={{background:"none",border:0,padding:0,marginBottom:16}}>{showMap?"Hide":"Choose on"} interactive map ↗</button>
      {showMap && <LocationMap latitude={Number(form.latitude)||18.52} longitude={Number(form.longitude)||73.86} onPick={selectMapPoint}/>}
      <div className="fields" style={{marginTop:25}}>{field("latitude","Latitude","degrees")} {field("longitude","Longitude","degrees")}</div>
      <div className="field" style={{marginTop:15}}><label htmlFor="locationName">Confirmed location name</label><input id="locationName" value={form.locationName} onChange={e=>update("locationName",e.target.value)} placeholder="e.g. Pune, Maharashtra, India"/></div>
      <div className="hint-note"><AlertCircle size={16}/> Actual rooftop shade, orientation and building conditions can affect the final result.</div>
    </>}
    {step===1 && <><h2>Tell us about the installation</h2><p>Provide actual area and an approximate panel layout. All defaults are editable assumptions, not contractor specifications.</p>
      <div className="field wide" style={{marginBottom:25}}><label>What type of energy user are you?</label><div className="choice-row">{categories.map(c=><button type="button" key={c} className={`choice ${form.category===c?"active":""}`} onClick={()=>update("category",c)}>{c[0].toUpperCase()+c.slice(1)}</button>)}</div></div>
      <div className="fields">{field("roofArea","Gross installation area","m²","Area before access corridors and setbacks.",0)}{field("usableFraction","Usable share","%","Accounts for obstacles and setbacks.",1,100)}{field("panelWp","Panel rated power","Wp", "Example assumption; confirm supplier specifications.")}{field("panelArea","Area per panel","m²")}{field("tilt","Panel tilt","degrees", "0° is horizontal; 90° is vertical.")}{field("azimuth","Panel azimuth","degrees","180° south; 90° east; 270° west.")}</div>
      <button type="button" className="text-link" onClick={()=>setAdvanced(!advanced)} style={{background:"none",border:0,padding:0}}>{advanced?"Hide":"Show"} advanced equipment assumptions ↗</button>
      {advanced && <div className="fields" style={{marginTop:20}}>{field("shade","Shading loss","%")}{field("soiling","Soiling loss","%")}{field("wiring","Wiring loss","%")}{field("inverterRatio","Inverter AC / panel DC","%")}</div>}
    </>}
    {step===2 && <><h2>Your electricity consumption</h2><p>Electricity demand determines how much solar energy you can use directly. The simple mode constructs an illustrative hourly load profile, not a measured one.</p>
      <div className="fields">{field("monthlyKwh","Average monthly electricity use","kWh","Check your electricity bill's units consumed.")}{field("importRate","Assumed grid energy rate","₹/kWh","Your own assumption, not an official tariff.")}{field("fixedCharge","Monthly fixed charge","₹","This remains payable after rooftop solar.")}</div>
      <div style={{marginTop:23,marginBottom:18}}><label style={{display:"inline-flex",alignItems:"center",gap:9,fontSize:13,fontWeight:700}}><input type="checkbox" checked={detailedDemand} onChange={e=>{setDetailedDemand(e.target.checked);if(e.target.checked && monthlyValues.every(x=>x==="450"))setMonthlyValues(Array(12).fill(form.monthlyKwh));}}/> Enter individual consumption for each month</label></div>
      {detailedDemand && <div className="fields">{["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].map((month,i)=><div className="field" key={month}><label htmlFor={`month-${i}`}>{month} demand (kWh)</label><input id={`month-${i}`} type="number" min="0" step="any" value={monthlyValues[i]} onChange={e=>setMonthlyValues(previous=>previous.map((v,j)=>j===i?e.target.value:v))}/></div>)}</div>}
      <div className="field" style={{marginTop:21}}><label htmlFor="exportMode">What happens to exported solar?</label><select id="exportMode" value={form.exportMode} onChange={e=>{update("exportMode",e.target.value);if(e.target.value==="no_export")update("exportRate","0");}}><option value="no_export">Assume no export compensation</option><option value="net_billing">User-assumed export credit (simple monthly net billing)</option></select><span className="field-help">Real net-metering and settlement rules vary by utility. Neither mode asserts legal eligibility.</span></div>
      {form.exportMode==="net_billing" && <div style={{marginTop:17}} className="fields">{field("exportRate","Assumed export credit","₹/kWh")}</div>}
      {form.category!=="residential" && <div className="fields" style={{marginTop:20}}>{field("operatingStart","Operating hours start","0–23")}{field("operatingEnd","Operating hours end","1–24")}</div>}
      <div className="hint-note"><AlertCircle size={16}/> These rates are your estimate. Actual utility bills and export credits may differ.</div>
    </>}
    {step===3 && <><h2>Financial assumptions</h2><p>These values drive the 25-year cash-flow model. Edit them to reflect supplier quotes and your investment criteria.</p>
      <div className="fields">{field("installationCost","Installed cost per kWp","₹/kWp","Estimate only; no verified market quote.")}{field("budget","Maximum investment budget","₹","Optional; leave blank for no cap.")}{field("maintenance","Annual O&M, percent of CAPEX","%")}{field("maintenanceEscalation","Annual O&M inflation","%")}{field("degradation","Annual panel degradation","%")}{field("escalation","Annual electricity rate increase","%")}{field("discount","Investment discount rate","%")}</div>
      <div className="field" style={{marginTop:23}}><label htmlFor="objective">Choose your sizing priority</label><select id="objective" value={form.objective} onChange={e=>update("objective",e.target.value)}>{objectives.map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></div>
      <div className="alert alert-info"><Calculator size={17}/> The model includes inverter replacement and annual maintenance, but excludes tax, financing and government subsidies.</div>
    </>}
    {step===4 && <><h2>Review your scenario</h2><p>We’ll use historical regional weather from 2023 and evaluate system sizes for your roof and budget. Your first assessment can take a little longer while data loads.</p>
      <div className="summary-grid"><div className="summary-cell"><span>Location</span><strong>{form.locationName}</strong></div><div className="summary-cell"><span>Site category</span><strong>{form.category}</strong></div><div className="summary-cell"><span>Gross area</span><strong>{form.roofArea} m²</strong></div><div className="summary-cell"><span>Monthly demand</span><strong>{detailedDemand?"12-month entered profile":form.monthlyKwh+" kWh"}</strong></div><div className="summary-cell"><span>Grid import assumption</span><strong>₹{form.importRate}/kWh</strong></div><div className="summary-cell"><span>Installed cost estimate</span><strong>{money(+form.installationCost)}/kWp</strong></div></div>
      <div className="hint-note"><AlertCircle size={16}/> Your result is an estimate, not a contractor quotation or guaranteed return. Final installation needs professional site checks.</div>
    </>}
    {error && <div role="alert" className="alert alert-error"><AlertCircle size={18}/>{error}</div>}
    <div className="wizard-controls"><button type="button" className="button button-soft" onClick={()=>{setError("");setStep(n=>Math.max(0,n-1));}} disabled={step===0}><ArrowLeft size={16}/> Back</button>{step<4 ? <button type="button" onClick={goNext} className="button button-dark">Continue <ArrowRight size={17}/></button> : <button disabled={loading} type="submit" className="button button-dark">{loading ? <><span className="spinner"/> {waitingSeconds < 12 ? "Starting assessment…" : waitingSeconds < 40 ? "Processing weather and energy…" : "Still working — please keep this tab open…"}</> : <>Calculate feasibility <CloudSun size={18}/></>}</button>}</div>
  </form></div></div></div>;
}
