"""Runs when optional scientific engine is installed; never replaces it with mocks."""
import pandas as pd
import pytest
from app.schemas import SiteInput
from app.services.solar import simulate_pv

pvlib = pytest.importorskip("pvlib", reason="pvlib is not installed in this environment")


def test_physics_zero_at_night_and_capacity_scaling(weather_48h):
    site = SiteInput(roof_area_m2=70)
    a = simulate_pv(weather_48h,18.5,73.8,site,1)
    b = simulate_pv(weather_48h,18.5,73.8,site,2)
    assert (a>=0).all()
    assert a.notna().all()
    assert (a[weather_48h.shortwave_radiation==0]==0).all()
    pd.testing.assert_series_equal(b,2*a,check_names=False,rtol=1e-5)


def test_orientation_affects_production(weather_48h):
    south=simulate_pv(weather_48h,18.5,73.8,SiteInput(roof_area_m2=50,azimuth_deg=180),3)
    west=simulate_pv(weather_48h,18.5,73.8,SiteInput(roof_area_m2=50,azimuth_deg=270),3)
    assert abs(float(south.sum())-float(west.sum()))>1e-3
