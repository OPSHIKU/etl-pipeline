"""
schemas.py
----------
Pydantic v2 models used as the automated schema-validation gate between
Extract and Transform. Every raw record is coerced into one of these
models; anything that fails is quarantined (never silently dropped) and
reported in the run's rejection report.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError

__all__ = ["SalesRecord", "WeatherRecord", "ValidationError"]


class SalesRecord(BaseModel):
    """Schema contract for one row of the raw sales CSV extract."""

    order_id: int
    customer_name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=100)          # rejects negative / absurd bulk-order typos
    unit_price: float = Field(gt=0)
    order_date: date
    email: EmailStr

    @field_validator("order_date", mode="before")
    @classmethod
    def parse_flexible_date(cls, value):
        """Accepts both 2026-08-01 and 2026/08/01 style dates."""
        if isinstance(value, date):
            return value
        text = str(value).strip().replace("/", "-")
        return date.fromisoformat(text)

    @field_validator("customer_name", "city", "product", mode="before")
    @classmethod
    def not_blank(cls, value):
        if value is None or str(value).strip() == "":
            raise ValueError("field cannot be blank")
        return str(value).strip()


class WeatherRecord(BaseModel):
    """Schema contract for one snapshot pulled from the weather API."""

    fetched_at: str
    latitude: float
    longitude: float
    temperature_c: float = Field(ge=-90, le=60)
    relative_humidity_pct: float = Field(ge=0, le=100)
    wind_speed_kmh: float = Field(ge=0)
