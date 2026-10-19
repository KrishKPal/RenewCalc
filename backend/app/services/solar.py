"""Physics-based PV output using pvlib solar geometry and PVWatts models."""
import numpy as np
import pandas as pd
from app.schemas import SiteInput


def maximum_modules(site: SiteInput) -> int:
    usable = site.roof_area_m2 * site.usable_fraction * site.packing_factor
    return max(0, int(np.floor(usable / site.panel_area_m2)))


def simulate_pv(weather: pd.DataFrame, latitude: float, longitude: float,
                site: SiteInput, module_count: int) -> pd.Series:
    if module_count < 0 or module_count > maximum_modules(site):
        raise ValueError("Module count exceeds physically available module area")
    if module_count == 0:
        return pd.Series(np.zeros(len(weather)), index=weather.index, name="solar_kwh")
    try:
        from pvlib import irradiance, pvsystem, temperature, solarposition, inverter
    except ImportError as exc:
        raise RuntimeError("pvlib is required for photovoltaic simulation. Install backend dependencies.") from exc

    interval_midpoints = weather.index + pd.Timedelta(minutes=30)
    sun = solarposition.get_solarposition(interval_midpoints, latitude, longitude)
    poa = irradiance.get_total_irradiance(
        surface_tilt=site.tilt_deg, surface_azimuth=site.azimuth_deg,
        solar_zenith=sun["apparent_zenith"].to_numpy(),
        solar_azimuth=sun["azimuth"].to_numpy(),
        dni=weather["direct_normal_irradiance"].to_numpy(),
        ghi=weather["shortwave_radiation"].to_numpy(),
        dhi=weather["diffuse_radiation"].to_numpy(),
        model="isotropic",
    )["poa_global"]
    poa = np.clip(np.asarray(poa, dtype=float), 0, None)
    effective_poa = np.asarray(poa) * (1 - site.shading_loss) * (1 - site.soiling_loss)
    wind_ms = weather["wind_speed_10m"].to_numpy() / 3.6
    cell_temp = temperature.faiman(effective_poa, weather["temperature_2m"].to_numpy(), wind_ms)
    capacity_dc_w = module_count * site.panel_wp
    dc = pvsystem.pvwatts_dc(effective_poa, cell_temp, pdc0=capacity_dc_w, gamma_pdc=-0.004)
    dc = np.maximum(0, np.asarray(dc)) * (1 - site.wiring_loss)
    inverter_ac_w = capacity_dc_w * site.inverter_ratio
    # PVWatts pdc0 is the inverter's DC reference rating: nominal AC clipping is eta*pdc0.
    ac = inverter.pvwatts(dc, pdc0=inverter_ac_w / 0.96, eta_inv_nom=0.96)
    ac = np.clip(np.nan_to_num(np.asarray(ac), nan=0), 0, inverter_ac_w)
    ac = np.where((weather["shortwave_radiation"].to_numpy() <= 0) |
                  (sun["apparent_elevation"].to_numpy() <= 0), 0, ac)
    # Each observation represents the average power during an exactly 1-hour interval.
    return pd.Series(ac / 1000, index=weather.index, name="solar_kwh")
