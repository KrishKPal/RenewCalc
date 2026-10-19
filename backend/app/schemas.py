"""Validated API contracts. Monetary inputs are INR; energy inputs are kWh."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class LocationInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = "Asia/Kolkata"
    country_code: str = "IN"

    @model_validator(mode="after")
    def check_coverage(self):
        if not (6 <= self.latitude <= 38.5 and 68 <= self.longitude <= 97.5):
            raise ValueError("Location is outside the India-focused assessment bounding box")
        return self


class SiteInput(BaseModel):
    roof_area_m2: float = Field(gt=0, le=100000)
    usable_fraction: float = Field(default=0.7, gt=0, le=1)
    panel_wp: float = Field(default=550, ge=100, le=1000)
    panel_area_m2: float = Field(default=2.6, ge=0.5, le=5)
    tilt_deg: float = Field(default=20, ge=0, le=90)
    azimuth_deg: float = Field(default=180, ge=0, lt=360)
    inverter_ratio: float = Field(default=0.85, ge=0.5, le=1.5)
    shading_loss: float = Field(default=0.08, ge=0, le=0.7)
    soiling_loss: float = Field(default=0.03, ge=0, le=0.5)
    wiring_loss: float = Field(default=0.02, ge=0, le=0.3)
    packing_factor: float = Field(default=0.85, gt=0, le=1)


class ConsumptionInput(BaseModel):
    category: Literal["residential", "commercial", "industrial", "farm", "institutional"] = "residential"
    monthly_kwh: float = Field(default=450, gt=0, le=100000000)
    monthly_kwh_profile: list[float] | None = None
    operating_start_hour: int = Field(default=9, ge=0, le=23)
    operating_end_hour: int = Field(default=18, ge=1, le=24)

    @model_validator(mode="after")
    def validate_months(self):
        if self.monthly_kwh_profile is not None:
            if len(self.monthly_kwh_profile) != 12 or any(x < 0 for x in self.monthly_kwh_profile):
                raise ValueError("monthly_kwh_profile must have 12 nonnegative values")
            if sum(self.monthly_kwh_profile) <= 0:
                raise ValueError("At least one month's consumption must be positive")
        return self


class TariffInput(BaseModel):
    mode: Literal["no_export", "net_billing"] = "no_export"
    import_rate_inr_kwh: float = Field(default=8, ge=0, le=1000)
    export_rate_inr_kwh: float = Field(default=0, ge=0, le=1000)
    fixed_charge_inr_month: float = Field(default=150, ge=0, le=1000000)
    source: Literal["user_provided"] = "user_provided"

    @model_validator(mode="after")
    def check_export(self):
        if self.mode == "no_export" and self.export_rate_inr_kwh != 0:
            raise ValueError("Export rate must be zero for no_export")
        return self


class FinancialInput(BaseModel):
    installation_cost_inr_kwp: float = Field(default=55000, gt=0, le=10000000)
    maintenance_fraction_year: float = Field(default=0.01, ge=0, le=0.2)
    maintenance_escalation_year: float = Field(default=0.03, ge=-0.1, le=0.3)
    panel_degradation_year: float = Field(default=0.005, ge=0, le=0.05)
    tariff_escalation_year: float = Field(default=0.03, ge=-0.1, le=0.3)
    discount_rate_year: float = Field(default=0.08, ge=0, le=0.5)
    inverter_replacement_year: int = Field(default=12, ge=1, le=30)
    inverter_replacement_fraction: float = Field(default=0.12, ge=0, le=1)
    horizon_years: int = Field(default=25, ge=5, le=30)
    budget_inr: float | None = Field(default=None, gt=0)
    objective: Literal["max_npv", "min_payback", "max_self_consumption", "max_generation"] = "max_npv"


class AssessmentRequest(BaseModel):
    location: LocationInput
    site: SiteInput
    consumption: ConsumptionInput
    tariff: TariffInput
    finance: FinancialInput
    weather_start_year: int = Field(default=2023, ge=2010, le=2024)
    weather_end_year: int = Field(default=2023, ge=2010, le=2024)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.weather_start_year > self.weather_end_year or self.weather_end_year - self.weather_start_year > 4:
            raise ValueError("Study period must be chronological and at most five years")
        if self.location.country_code.upper() != "IN":
            raise ValueError("Initial release supports Indian locations only")
        if self.location.timezone != "Asia/Kolkata":
            raise ValueError("Indian assessments use Asia/Kolkata time")
        return self


class LocationCandidate(BaseModel):
    id: int | None = None
    name: str
    admin1: str | None = None
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str | None = None


class AssessmentSummary(BaseModel):
    id: str
    created_at: datetime
    result: dict
