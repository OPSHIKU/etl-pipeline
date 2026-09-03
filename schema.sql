-- ============================================================
-- ETL Pipeline Database Schema
-- Generated from live SQLite run. Portable to PostgreSQL with
-- minor type-name changes (INTEGER->SERIAL for autoincrement PKs).
-- ============================================================

CREATE TABLE pipeline_runs (
	id INTEGER NOT NULL, 
	run_timestamp DATETIME NOT NULL, 
	source_name VARCHAR(50) NOT NULL, 
	rows_extracted INTEGER, 
	rows_valid INTEGER, 
	rows_rejected INTEGER, 
	status VARCHAR(20), 
	PRIMARY KEY (id)
);

CREATE TABLE rejected_records (
	id INTEGER NOT NULL, 
	source_name VARCHAR(50) NOT NULL, 
	run_timestamp DATETIME NOT NULL, 
	row_index INTEGER, 
	raw_record TEXT, 
	errors TEXT, 
	PRIMARY KEY (id)
);

CREATE TABLE sales (
	order_id INTEGER NOT NULL, 
	customer_name VARCHAR(120) NOT NULL, 
	city VARCHAR(80) NOT NULL, 
	product VARCHAR(120) NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price FLOAT NOT NULL, 
	total_amount FLOAT NOT NULL, 
	order_date DATE NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	loaded_at DATETIME NOT NULL, 
	PRIMARY KEY (order_id)
);

CREATE TABLE weather_snapshots (
	id INTEGER NOT NULL, 
	fetched_at DATETIME NOT NULL, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	temperature_c FLOAT NOT NULL, 
	relative_humidity_pct FLOAT NOT NULL, 
	wind_speed_kmh FLOAT NOT NULL, 
	loaded_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

-- ============================================================
-- PostgreSQL equivalent (used automatically when DB_ENGINE=postgres —
-- SQLAlchemy's create_all() generates this from the same Table objects
-- in load/loader.py, no code changes needed). Included here for
-- reference / manual provisioning if you'd rather run the DDL yourself.
-- ============================================================

-- CREATE TABLE sales (
--     order_id        INTEGER PRIMARY KEY,
--     customer_name   VARCHAR(120) NOT NULL,
--     city            VARCHAR(80)  NOT NULL,
--     product         VARCHAR(120) NOT NULL,
--     quantity        INTEGER NOT NULL,
--     unit_price      DOUBLE PRECISION NOT NULL,
--     total_amount    DOUBLE PRECISION NOT NULL,
--     order_date      DATE NOT NULL,
--     email           VARCHAR(255) NOT NULL,
--     loaded_at       TIMESTAMP NOT NULL
-- );
--
-- CREATE TABLE weather_snapshots (
--     id                      SERIAL PRIMARY KEY,
--     fetched_at              TIMESTAMP NOT NULL,
--     latitude                DOUBLE PRECISION NOT NULL,
--     longitude               DOUBLE PRECISION NOT NULL,
--     temperature_c           DOUBLE PRECISION NOT NULL,
--     relative_humidity_pct   DOUBLE PRECISION NOT NULL,
--     wind_speed_kmh          DOUBLE PRECISION NOT NULL,
--     loaded_at               TIMESTAMP NOT NULL
-- );
--
-- CREATE TABLE rejected_records (
--     id             SERIAL PRIMARY KEY,
--     source_name    VARCHAR(50) NOT NULL,
--     run_timestamp  TIMESTAMP NOT NULL,
--     row_index      INTEGER,
--     raw_record     TEXT,
--     errors         TEXT
-- );
--
-- CREATE TABLE pipeline_runs (
--     id              SERIAL PRIMARY KEY,
--     run_timestamp   TIMESTAMP NOT NULL,
--     source_name     VARCHAR(50) NOT NULL,
--     rows_extracted  INTEGER,
--     rows_valid      INTEGER,
--     rows_rejected   INTEGER,
--     status          VARCHAR(20)
-- );

