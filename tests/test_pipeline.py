"""
test_pipeline.py
-----------------
Minimal unit tests covering the two riskiest parts of the pipeline:
schema validation (does it correctly accept good rows and reject bad
ones?) and transform logic (are derived columns computed correctly?).

Run with:  pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import pandas as pd

from validate.schemas import SalesRecord
from validate.validator import validate_records
from transform.transformer import transform_sales

silent_logger = logging.getLogger("test")
silent_logger.addHandler(logging.NullHandler())


def test_valid_sales_record_passes():
    record = {
        "order_id": "1",
        "customer_name": "Test User",
        "city": "Mumbai",
        "product": "Wireless Mouse",
        "quantity": "2",
        "unit_price": "499.00",
        "order_date": "2026-08-01",
        "email": "test.user@example.com",
    }
    valid, rejected = validate_records([record], SalesRecord, silent_logger, "test")
    assert len(valid) == 1
    assert len(rejected) == 0


def test_negative_quantity_is_rejected():
    record = {
        "order_id": "2",
        "customer_name": "Test User",
        "city": "Mumbai",
        "product": "Wireless Mouse",
        "quantity": "-1",
        "unit_price": "499.00",
        "order_date": "2026-08-01",
        "email": "test.user@example.com",
    }
    valid, rejected = validate_records([record], SalesRecord, silent_logger, "test")
    assert len(valid) == 0
    assert len(rejected) == 1


def test_invalid_email_is_rejected():
    record = {
        "order_id": "3",
        "customer_name": "Test User",
        "city": "Mumbai",
        "product": "Wireless Mouse",
        "quantity": "1",
        "unit_price": "499.00",
        "order_date": "2026-08-01",
        "email": "not-an-email",
    }
    valid, rejected = validate_records([record], SalesRecord, silent_logger, "test")
    assert len(valid) == 0
    assert len(rejected) == 1


def test_slash_date_is_normalized():
    record = {
        "order_id": "4",
        "customer_name": "Test User",
        "city": "Mumbai",
        "product": "Wireless Mouse",
        "quantity": "1",
        "unit_price": "499.00",
        "order_date": "2026/08/01",
        "email": "test.user@example.com",
    }
    valid, rejected = validate_records([record], SalesRecord, silent_logger, "test")
    assert len(valid) == 1
    assert str(valid[0].order_date) == "2026-08-01"


def test_transform_computes_total_amount():
    record = SalesRecord.model_validate(
        {
            "order_id": 5,
            "customer_name": "test user",
            "city": "mumbai",
            "product": "Wireless Mouse",
            "quantity": 3,
            "unit_price": 100.0,
            "order_date": "2026-08-01",
            "email": "test.user@example.com",
        }
    )
    df = transform_sales([record], silent_logger)
    assert df.iloc[0]["total_amount"] == 300.0
    assert df.iloc[0]["city"] == "Mumbai"          # title-cased
    assert df.iloc[0]["customer_name"] == "Test User"


def test_transform_deduplicates_order_id():
    record = SalesRecord.model_validate(
        {
            "order_id": 6,
            "customer_name": "Test User",
            "city": "Mumbai",
            "product": "Wireless Mouse",
            "quantity": 1,
            "unit_price": 100.0,
            "order_date": "2026-08-01",
            "email": "test.user@example.com",
        }
    )
    df = transform_sales([record, record], silent_logger)
    assert len(df) == 1
