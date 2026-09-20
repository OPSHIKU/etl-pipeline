"""
config.py
---------
Central configuration for the ETL pipeline. Reads from environment variables
so the same codebase can target SQLite (default, zero-setup) or PostgreSQL
(production) without any code changes.

To switch to PostgreSQL, set:
    DB_ENGINE=postgres
    DB_URL=postgresql+psycopg2://user:password@host:5432/dbname
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ---- Database ----
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")  # "sqlite" or "postgres"

if DB_ENGINE == "postgres":
    DATABASE_URL = os.getenv(
        "DB_URL", "postgresql+psycopg2://user:password@localhost:5432/etl_db"
    )
else:
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'etl_pipeline.db'}"

# ---- Sources ----
CSV_SOURCE_PATH = BASE_DIR / "sample_data" / "raw_sales.csv"
API_SOURCE_URL = os.getenv(
    "WEATHER_API_URL",
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=19.076&longitude=72.877&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
    "&timezone=Asia%2FKolkata",
)  # Mumbai coordinates, no API key required

# ---- Logging ----
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ---- Alerts ----
# Set a Slack/Teams incoming webhook URL to get automated failure alerts.
# Left blank by default -> pipeline logs a CRITICAL line instead of calling out.
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

# ---- Validation thresholds ----
MAX_REJECT_RATE = float(os.getenv("MAX_REJECT_RATE", "0.30"))  # abort load if >30% rows fail
