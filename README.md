# Weather -> Snowflake Pipeline

This project ingests hourly weather data from Open-Meteo and loads it into Snowflake.

## Architecture

1. `src/weather_ingest.py` fetches hourly weather data for a configured location.
2. Script loads rows into `RAW.WEATHER_HOURLY_RAW`.
3. Snowflake `STREAM` + `TASK` merges latest records into `ANALYTICS.WEATHER_HOURLY`.

## Prerequisites

- Python 3.10+
- Snowflake account and credentials
- A Snowflake warehouse (update SQL if not using `COMPUTE_WH`)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
# edit .env with your Snowflake credentials and weather location
```

4. Run Snowflake setup SQL:

```sql
-- In Snowflake worksheet
-- Execute: snowflake/sql/01_setup.sql
```

5. Enable the merge task (after confirming warehouse name):

```sql
ALTER TASK WEATHER_DB.RAW.TASK_MERGE_WEATHER_HOURLY RESUME;
```

## Run ingestion

```bash
python src/weather_ingest.py
```

## Validate

```sql
SELECT COUNT(*) FROM WEATHER_DB.RAW.WEATHER_HOURLY_RAW;
SELECT * FROM WEATHER_DB.ANALYTICS.WEATHER_HOURLY ORDER BY OBSERVED_AT DESC LIMIT 20;
```

## Scheduling options

- External scheduler: cron, Airflow, GitHub Actions, etc. to run `python src/weather_ingest.py`.
- Internal Snowflake task handles upserts from RAW to ANALYTICS hourly.
