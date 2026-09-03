"""
loader.py
---------
Load stage. Uses SQLAlchemy Core so the exact same code targets SQLite
(default, zero-config) or PostgreSQL (set DB_ENGINE=postgres in env) —
no branching logic needed per-database.

Also responsible for creating the `rejected_records` audit table so
every quarantined row from the validation stage is queryable, not lost.
"""

import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
    text,
)

import config

metadata = MetaData()

sales_table = Table(
    "sales",
    metadata,
    Column("order_id", Integer, primary_key=True),
    Column("customer_name", String(120), nullable=False),
    Column("city", String(80), nullable=False),
    Column("product", String(120), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False),
    Column("total_amount", Float, nullable=False),
    Column("order_date", Date, nullable=False),
    Column("email", String(255), nullable=False),
    Column("loaded_at", DateTime, nullable=False),
)

weather_snapshots_table = Table(
    "weather_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fetched_at", DateTime, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("temperature_c", Float, nullable=False),
    Column("relative_humidity_pct", Float, nullable=False),
    Column("wind_speed_kmh", Float, nullable=False),
    Column("loaded_at", DateTime, nullable=False),
)

rejected_records_table = Table(
    "rejected_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_name", String(50), nullable=False),
    Column("run_timestamp", DateTime, nullable=False),
    Column("row_index", Integer),
    Column("raw_record", Text),
    Column("errors", Text),
)

pipeline_runs_table = Table(
    "pipeline_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_timestamp", DateTime, nullable=False),
    Column("source_name", String(50), nullable=False),
    Column("rows_extracted", Integer),
    Column("rows_valid", Integer),
    Column("rows_rejected", Integer),
    Column("status", String(20)),
)


def get_engine():
    return create_engine(config.DATABASE_URL, future=True)


def init_db(engine, logger):
    metadata.create_all(engine)
    logger.info(f"Database schema ensured at: {config.DATABASE_URL}")


def load_dataframe(engine, df: pd.DataFrame, table_name: str, logger, pk_col: str = None):
    if df.empty:
        logger.warning(f"No rows to load into '{table_name}' — skipping load.")
        return 0

    df = df.copy()
    df["loaded_at"] = datetime.now(timezone.utc)

    with engine.begin() as conn:
        if pk_col:
            # Upsert-lite: delete existing PKs present in this batch, then insert.
            # Makes reruns of the same batch idempotent instead of erroring on PK conflict.
            existing_ids = [int(x) for x in df[pk_col].tolist()]
            if existing_ids:
                id_list = ",".join(str(i) for i in existing_ids)
                conn.execute(text(f"DELETE FROM {table_name} WHERE {pk_col} IN ({id_list})"))
        df.to_sql(table_name, conn, if_exists="append", index=False)

    logger.info(f"Loaded {len(df)} rows into table '{table_name}'.")
    return len(df)


def log_rejections(engine, rejected: list, source_name: str, logger):
    if not rejected:
        return
    run_ts = datetime.now(timezone.utc)
    rows = [
        {
            "source_name": source_name,
            "run_timestamp": run_ts,
            "row_index": r["row_index"],
            "raw_record": json.dumps(r["raw_record"], default=str),
            "errors": json.dumps(r["errors"], default=str),
        }
        for r in rejected
    ]
    with engine.begin() as conn:
        conn.execute(rejected_records_table.insert(), rows)
    logger.info(f"Logged {len(rows)} rejected records from '{source_name}' to audit table.")


def log_run_summary(engine, source_name, extracted, valid, rejected, status, logger):
    with engine.begin() as conn:
        conn.execute(
            pipeline_runs_table.insert(),
            {
                "run_timestamp": datetime.now(timezone.utc),
                "source_name": source_name,
                "rows_extracted": extracted,
                "rows_valid": valid,
                "rows_rejected": rejected,
                "status": status,
            },
        )
    logger.info(
        f"Run summary recorded for '{source_name}': "
        f"extracted={extracted}, valid={valid}, rejected={rejected}, status={status}"
    )
