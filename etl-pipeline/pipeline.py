"""
pipeline.py
-----------
Main orchestrator. Runs the full ETL flow for two independent sources
(CSV sales data, weather REST API), each going through the same
Extract -> Validate -> Transform -> Load stages, with logging and
alerting wrapped around every stage.

Run directly:
    python pipeline.py

Switch to PostgreSQL:
    set DB_ENGINE=postgres  (Windows)  /  export DB_ENGINE=postgres (Mac/Linux)
    set DB_URL=postgresql+psycopg2://user:pass@host:5432/etl_db
    python pipeline.py
"""

import sys
import traceback

import config
from utils.logger_config import get_logger
from utils.alerts import send_alert

from extract.csv_extractor import extract_csv
from extract.api_extractor import extract_weather_api

from validate.schemas import SalesRecord, WeatherRecord
from validate.validator import validate_records

from transform.transformer import transform_sales, transform_weather

from load.loader import get_engine, init_db, load_dataframe, log_rejections, log_run_summary

logger = get_logger()


def run_source_pipeline(source_name, extract_fn, schema, transform_fn, pk_col, engine):
    """Runs one full Extract->Validate->Transform->Load cycle for a single source.
    Isolated per-source so one source failing doesn't take down the other."""
    logger.info(f"===== Starting pipeline run for source: {source_name} =====")
    try:
        # EXTRACT
        raw_records = extract_fn()

        # VALIDATE
        valid_records, rejected = validate_records(raw_records, schema, logger, source_name)

        reject_rate = len(rejected) / len(raw_records) if raw_records else 0
        if reject_rate > config.MAX_REJECT_RATE:
            raise ValueError(
                f"Reject rate {reject_rate:.1%} exceeds threshold "
                f"{config.MAX_REJECT_RATE:.0%} for source '{source_name}'. Aborting load "
                f"to avoid loading a batch with systemic data-quality issues."
            )

        # TRANSFORM
        df = transform_fn(valid_records, logger)

        # LOAD
        rows_loaded = load_dataframe(engine, df, source_name, logger, pk_col=pk_col)
        log_rejections(engine, rejected, source_name, logger)
        log_run_summary(
            engine, source_name, len(raw_records), len(valid_records), len(rejected), "SUCCESS", logger
        )

        logger.info(f"===== Completed pipeline run for source: {source_name} =====\n")
        return {
            "source": source_name,
            "status": "SUCCESS",
            "extracted": len(raw_records),
            "loaded": rows_loaded,
            "rejected": len(rejected),
        }

    except Exception as exc:
        logger.error(f"Pipeline FAILED for source '{source_name}': {exc}")
        logger.debug(traceback.format_exc())
        send_alert(logger, subject=f"ETL pipeline failure: {source_name}", message=str(exc))
        try:
            log_run_summary(engine, source_name, 0, 0, 0, "FAILED", logger)
        except Exception:
            pass  # don't let a logging failure mask the original error
        return {"source": source_name, "status": "FAILED", "error": str(exc)}


def main():
    logger.info("############################################")
    logger.info("###   ETL PIPELINE RUN STARTING           ###")
    logger.info(f"###   Target database: {config.DB_ENGINE:<10}          ###")
    logger.info("############################################")

    engine = get_engine()
    init_db(engine, logger)

    results = []

    results.append(
        run_source_pipeline(
            source_name="sales",
            extract_fn=lambda: extract_csv(config.CSV_SOURCE_PATH, logger),
            schema=SalesRecord,
            transform_fn=transform_sales,
            pk_col="order_id",
            engine=engine,
        )
    )

    results.append(
        run_source_pipeline(
            source_name="weather_snapshots",
            extract_fn=lambda: extract_weather_api(config.API_SOURCE_URL, logger),
            schema=WeatherRecord,
            transform_fn=transform_weather,
            pk_col=None,
            engine=engine,
        )
    )

    logger.info("===== PIPELINE RUN SUMMARY =====")
    overall_status = "SUCCESS"
    for r in results:
        logger.info(f"  {r}")
        if r["status"] == "FAILED":
            overall_status = "PARTIAL_FAILURE"
    logger.info(f"Overall run status: {overall_status}")
    logger.info("############################################\n")

    sys.exit(0 if overall_status == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
