import os
from datetime import date

import pandas as pd
import requests
import snowflake.connector
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def fetch_weather(city: str, latitude: float, longitude: float, timezone: str, start_date: str, end_date: str) -> pd.DataFrame:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "timezone": timezone,
        "start_date": start_date,
        "end_date": end_date,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    hourly = payload.get("hourly", {})
    timestamps = hourly.get("time", [])
    if not timestamps:
        raise RuntimeError("No weather rows returned from API.")

    rows = []
    for i, observed_at in enumerate(timestamps):
        rows.append(
            {
                "CITY": city,
                "LATITUDE": float(latitude),
                "LONGITUDE": float(longitude),
                "OBSERVED_AT": observed_at,
                "TEMPERATURE_2M": hourly.get("temperature_2m", [None] * len(timestamps))[i],
                "RELATIVE_HUMIDITY_2M": hourly.get("relative_humidity_2m", [None] * len(timestamps))[i],
                "PRECIPITATION": hourly.get("precipitation", [None] * len(timestamps))[i],
                "WIND_SPEED_10M": hourly.get("wind_speed_10m", [None] * len(timestamps))[i],
                "SOURCE": "open-meteo",
            }
        )

    df = pd.DataFrame(rows)
    df["OBSERVED_AT"] = pd.to_datetime(df["OBSERVED_AT"], utc=False)
    return df


def snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    account = required_env("SNOWFLAKE_ACCOUNT")
    user = required_env("SNOWFLAKE_USER")
    password = required_env("SNOWFLAKE_PASSWORD")
    warehouse = required_env("SNOWFLAKE_WAREHOUSE")
    database = required_env("SNOWFLAKE_DATABASE")
    schema = required_env("SNOWFLAKE_SCHEMA")
    role = os.getenv("SNOWFLAKE_ROLE")

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role,
    )


def main() -> None:
    load_dotenv()

    city = os.getenv("WEATHER_CITY", "Seattle")
    latitude = float(os.getenv("WEATHER_LATITUDE", "47.6062"))
    longitude = float(os.getenv("WEATHER_LONGITUDE", "-122.3321"))
    timezone = os.getenv("WEATHER_TIMEZONE", "UTC")

    today = date.today().isoformat()
    start_date = os.getenv("WEATHER_START_DATE") or today
    end_date = os.getenv("WEATHER_END_DATE") or today

    weather_df = fetch_weather(
        city=city,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        start_date=start_date,
        end_date=end_date,
    )

    conn = snowflake_connection()
    try:
        success, nchunks, nrows, output = write_pandas(
            conn=conn,
            df=weather_df,
            table_name="WEATHER_HOURLY_RAW",
            database=required_env("SNOWFLAKE_DATABASE"),
            schema=required_env("SNOWFLAKE_SCHEMA"),
            auto_create_table=False,
            quote_identifiers=False,
        )
        if not success:
            raise RuntimeError("write_pandas did not report success.")

        print(f"Loaded {nrows} rows into RAW.WEATHER_HOURLY_RAW across {nchunks} chunk(s).")
        print(output)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
