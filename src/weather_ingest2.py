import os
import requests
from datetime import date
from dotenv import load_dotenv

def fetch_env(name):
    value = os.getenv(name)
    if not value:
        return f'{name} not found'
    return value

def weather_fetch(latitude, longitude, timezone, start_date, end_date):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": latitude,
              "longitude": longitude,
              "timzone": timezone,
              "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
              "start_date": start_date,
              "end_date": end_date}
    response = requests.get(url,params = params,timeout=30)
    ##response.raise_for_status()
    payload = response.json()
    return payload
    
def main():
    load_dotenv()
    latitude = fetch_env('WEATHER_LATITUDE')
    longitude = fetch_env('WEATHER_LONGITUDE')
    timezone = os.getenv("WEATHER_TIMEZONE","UTC")
    today = date.today().isoformat()
    start_date = os.getenv("WEATHER_START_DATE") or today
    end_date = os.getenv("WEATHER_END_DATE") or today
    try:
        result = weather_fetch(latitude, longitude, timezone, start_date, end_date)
    except Exception as e:
        raise RuntimeError(f"Input validation or API call failed: {e}")
    finally:
        print(result)    
    
if __name__ == "__main__":
    main()


