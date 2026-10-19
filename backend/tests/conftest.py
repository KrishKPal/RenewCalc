import numpy as np
import pandas as pd
import pytest

@pytest.fixture
def weather_48h():
    idx = pd.date_range("2023-06-01", periods=48, freq="h", tz="UTC")
    h = idx.hour.to_numpy()
    radiation = 650*np.maximum(0, np.sin(np.pi*(h-5)/13))
    return pd.DataFrame({
        "shortwave_radiation": radiation,
        "direct_normal_irradiance": radiation*.65,
        "diffuse_radiation": radiation*.35,
        "temperature_2m": 27 + np.zeros(48),
        "wind_speed_10m": 8 + np.zeros(48),
    },index=idx)
