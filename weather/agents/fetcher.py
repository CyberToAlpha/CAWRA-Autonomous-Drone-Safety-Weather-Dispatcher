import requests
from typing import Dict, Any, Optional

class WeatherFetcher:
    """
    Agent responsible for fetching weather data from Open-Meteo API.
    """
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_weather(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Fetches current weather and daily forecast for the given coordinates.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,pressure_msl,wind_speed_10m,visibility",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto"
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def fetch_metar(self, station_code: str) -> Optional[str]:
        """
        Fetches raw METAR data for a given station code (e.g., VOMM).
        """
        url = f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code.upper()}.TXT"
        try:
            response = requests.get(url)
            response.raise_for_status()
            # The file format is usually:
            # 2023/10/27 10:00
            # VOMM 271000Z ...
            # We want the second line usually, or just the whole thing to parse later.
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching METAR data: {e}")
            return None

    def fetch_taf(self, station_code: str) -> Optional[str]:
        """
        Fetches raw TAF data for a given station code (e.g., VOMM).
        """
        url = f"https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{station_code.upper()}.TXT"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching TAF data: {e}")
            return None

if __name__ == "__main__":
    # Test the fetcher
    fetcher = WeatherFetcher()
    # Coordinates for San Francisco
    weather_data = fetcher.fetch_weather(37.7749, -122.4194)
    if weather_data:
        print("Successfully fetched weather data:")
        print(weather_data)
    else:
        print("Failed to fetch weather data.")
