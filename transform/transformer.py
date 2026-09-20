"""
transformer.py
--------------
Transform stage. Takes validated Pydantic model instances (guaranteed
type-correct at this point) and applies business logic: derived
columns, normalization, deduplication.
"""

from typing import List
import pandas as pd

from validate.schemas import SalesRecord, WeatherRecord


def transform_sales(records: List[SalesRecord], logger) -> pd.DataFrame:
    if not records:
        logger.warning("No valid sales records to transform.")
        return pd.DataFrame()

    df = pd.DataFrame([r.model_dump() for r in records])

    before = len(df)
    df.drop_duplicates(subset=["order_id"], keep="first", inplace=True)
    deduped = before - len(df)
    if deduped:
        logger.info(f"Removed {deduped} duplicate order_id rows during transform.")

    df["city"] = df["city"].str.strip().str.title()
    df["customer_name"] = df["customer_name"].str.strip().str.title()
    df["product"] = df["product"].str.strip()
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date.astype(str)

    logger.info(f"Transform complete: {len(df)} sales rows ready for load.")
    return df


def transform_weather(records: List[WeatherRecord], logger) -> pd.DataFrame:
    if not records:
        logger.warning("No valid weather records to transform.")
        return pd.DataFrame()

    df = pd.DataFrame([r.model_dump() for r in records])
    df["temperature_c"] = df["temperature_c"].round(1)
    df["fetched_at"] = pd.to_datetime(df["fetched_at"]).astype(str)

    logger.info(f"Transform complete: {len(df)} weather rows ready for load.")
    return df
