# ETL Pipeline — CSV/API → Validate → Transform → Load (SQLite/PostgreSQL)

A modular, runnable Python ETL pipeline that:

- **Extracts** raw data from a CSV file and a REST API
- **Validates** every record against a strict schema (Pydantic v2) — bad rows are quarantined, never silently dropped or silently corrupted
- **Transforms**: cleans strings, normalizes dates, deduplicates, derives new columns
- **Loads** into a SQL database (SQLite out of the box, PostgreSQL with one env var change) using SQLAlchemy
- **Logs** every stage to console + a rotating log file
- **Alerts** on failure (Slack/Teams webhook, or CRITICAL log line if no webhook is configured)

Architecture diagram: [`diagrams/architecture_diagram.png`](diagrams/architecture_diagram.png)

## Project structure

```
etl-pipeline/
├── pipeline.py              # Main orchestrator — run this
├── config.py                # All settings, reads from environment variables
├── extract/
│   ├── csv_extractor.py     # Reads the raw CSV
│   └── api_extractor.py     # Calls the weather REST API, with retry+backoff
├── validate/
│   ├── schemas.py           # Pydantic models — the schema "contract"
│   └── validator.py         # Runs records through a schema, splits valid/rejected
├── transform/
│   └── transformer.py       # Cleaning, normalization, derived columns
├── load/
│   └── loader.py            # SQLAlchemy table definitions + load functions
├── utils/
│   ├── logger_config.py     # Shared logger (console + rotating file)
│   └── alerts.py            # Failure alerting (webhook or log-only)
├── sample_data/
│   └── raw_sales.csv        # Intentionally messy sample data (see below)
├── tests/
│   └── test_pipeline.py     # pytest unit tests for validation + transform
├── schema.sql               # Exported DDL (SQLite, with PostgreSQL equivalent)
├── diagrams/
│   └── architecture_diagram.png/.svg
├── requirements.txt
└── .env.example
```

## Why the sample CSV has "bad" rows

`sample_data/raw_sales.csv` deliberately contains a blank customer name, an
invalid email, a negative quantity, a missing price, a slash-formatted date,
and an absurd 999-unit order. This is so a real run of the pipeline actually
*demonstrates* the validation layer catching and quarantining bad data,
rather than just working on a clean toy file. Every rejected row is logged
with the specific validation error and written to a `rejected_records` audit
table in the database — nothing is thrown away silently.

## Setup

```bash
# 1. Clone and enter the repo
git clone <your-repo-url>
cd etl-pipeline

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the pipeline

```bash
python pipeline.py
```

That's it — by default it uses SQLite and creates `etl_pipeline.db` in the
project folder. No database server, no credentials needed.

Logs stream to your console **and** get written to `logs/pipeline.log`.

## Running the tests

```bash
pytest tests/ -v
```

## Switching to PostgreSQL

No code changes needed — set two environment variables before running:

```bash
# Windows (PowerShell)
$env:DB_ENGINE="postgres"
$env:DB_URL="postgresql+psycopg2://user:password@localhost:5432/etl_db"
python pipeline.py

# Mac/Linux
export DB_ENGINE=postgres
export DB_URL="postgresql+psycopg2://user:password@localhost:5432/etl_db"
python pipeline.py
```

You'll also need `psycopg2-binary` installed (already in `requirements.txt`)
and a running PostgreSQL instance with the target database created.

## Configuring alerts

By default, failures are only written to the log file at `CRITICAL` level.
To get a live notification, set a Slack or Microsoft Teams incoming webhook
URL:

```bash
export ALERT_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

## What happens on bad data

Each source has a configurable `MAX_REJECT_RATE` (default 30%). If more than
that fraction of rows in a batch fail validation, the pipeline **aborts the
load for that source** (to avoid loading a systematically broken batch),
fires an alert, and records the failed run in the `pipeline_runs` audit
table — while still letting the *other* source's pipeline run independently.

## Database schema

See [`schema.sql`](schema.sql) for the full DDL. Four tables:

| Table | Purpose |
|---|---|
| `sales` | Cleaned, validated sales records |
| `weather_snapshots` | Cleaned, validated API pulls |
| `rejected_records` | Audit trail of every row that failed validation, with the specific error(s) |
| `pipeline_runs` | One row per pipeline run per source: counts + status, for monitoring trends over time |

## Sample execution log

A real run's output is included at
[`execution_log_sample.txt`](execution_log_sample.txt) for reference —
showing validation catching bad rows, a successful load, and the run
summary.

## Notes on the demo API

The weather extractor calls Open-Meteo's free public forecast API (no key
required) by default. If you're running this somewhere with restricted
outbound network access, point `WEATHER_API_URL` (see `.env.example`) at any
reachable JSON endpoint that returns `latitude`, `longitude`, and a
`current` object with `temperature_2m`, `relative_humidity_2m`, and
`wind_speed_10m` — or swap in your own extractor following the same pattern
in `extract/api_extractor.py`.
