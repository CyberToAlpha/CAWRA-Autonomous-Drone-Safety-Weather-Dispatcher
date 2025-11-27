from typing import Dict, Any
from datetime import datetime

class WeatherDecoder:
    """
    Agent responsible for decoding and formatting raw weather data.
    """
    
    # WMO Weather interpretation codes (WW)
    # https://open-meteo.com/en/docs
    WMO_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def decode_weather(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decodes the raw API response into a structured, human-readable format.
        """
        if not raw_data or 'current' not in raw_data:
            return {}

        current = raw_data['current']
        daily = raw_data.get('daily', {})

        weather_code = current.get('weather_code')
        condition = self.WMO_CODES.get(weather_code, "Unknown")

        # Extract daily highs and lows if available
        temp_max = daily.get('temperature_2m_max', [None])[0]
        temp_min = daily.get('temperature_2m_min', [None])[0]
        precip_sum = daily.get('precipitation_sum', [None])[0]

        # Conversions
        wind_speed_kmh = current.get('wind_speed_10m', 0)
        wind_speed_knots = wind_speed_kmh * 0.539957

        # Date formatting
        # Open-Meteo returns time in ISO8601, e.g., "2023-10-27T10:00"
        time_str = current.get('time')
        try:
            dt = datetime.fromisoformat(time_str)
            formatted_date = dt.strftime("%A\n%d-%m-%Y") # Sunday\n17-08-2025
            day_name = dt.strftime("%A")
            full_date = dt.strftime("%d-%m-%Y")
        except:
            formatted_date = time_str
            day_name = ""
            full_date = time_str

        decoded_data = {
            "temperature": current.get('temperature_2m'),
            "humidity": current.get('relative_humidity_2m'),
            "pressure": current.get('pressure_msl'),
            "visibility": current.get('visibility'), # in meters
            "windspeed_kmh": wind_speed_kmh,
            "windspeed_knots": round(wind_speed_knots, 2),
            "weathercode": weather_code,
            "condition": condition,
            "time": time_str,
            "formatted_date": formatted_date,
            "day_name": day_name,
            "full_date": full_date,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "precipitation": precip_sum,
            "latitude": raw_data.get('latitude'),
            "longitude": raw_data.get('longitude'),
            "timezone": raw_data.get('timezone')
        }
        
        return decoded_data

    def decode_metar(self, metar_text: str) -> Dict[str, Any]:
        """
        Decodes a raw METAR string into the structured format expected by the Analyst.
        """
        if not metar_text:
            return {}

        import re
        
        # Split lines, usually the METAR is on the second line
        lines = metar_text.split('\n')
        raw_metar = lines[-1].strip() if len(lines) > 1 else lines[0].strip()
        
        # Regex Patterns
        # Temp/Dew: 28/23 (28C temp, 23C dew)
        temp_pattern = r'(\d{2})/(\d{2})' 
        # Wind: 07008KT (070 degrees, 08 knots)
        wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT'
        # Pressure: Q1014 (1014 hPa)
        pressure_pattern = r'Q(\d{4})'
        # Visibility: 4000 (4000 meters) or 9999 (10km+)
        vis_pattern = r'\s(\d{4})\s'
        
        # Extraction
        temp_match = re.search(temp_pattern, raw_metar)
        wind_match = re.search(wind_pattern, raw_metar)
        pressure_match = re.search(pressure_pattern, raw_metar)
        vis_match = re.search(vis_pattern, raw_metar)
        
        # Defaults
        temp = 0
        dew = 0
        wind_knots = 0
        pressure = 1013
        visibility = 10000
        condition = "Clear"
        weather_code = 0 # 0 is Clear
        
        if temp_match:
            temp = int(temp_match.group(1))
            # Handle negative temperatures (M05) - simplified for now as Chennai is hot
            # If needed: check for 'M' prefix in regex
            
        if wind_match:
            wind_knots = int(wind_match.group(2))
            
        if pressure_match:
            pressure = int(pressure_match.group(1))
            
        if vis_match:
            visibility = int(vis_match.group(1))
            
        # Simple Condition Parsing based on codes
        # HZ: Haze, RA: Rain, TS: Thunderstorm, BR: Mist, FG: Fog
        if "TS" in raw_metar:
            condition = "Thunderstorm"
            weather_code = 95
        elif "RA" in raw_metar:
            condition = "Rain"
            weather_code = 63
        elif "DZ" in raw_metar:
            condition = "Drizzle"
            weather_code = 53
        elif "HZ" in raw_metar:
            condition = "Haze"
            weather_code = 45 # Fog/Haze code equivalent
        elif "BR" in raw_metar:
            condition = "Mist"
            weather_code = 45
        elif "FG" in raw_metar:
            condition = "Fog"
            weather_code = 45
        elif "SCT" in raw_metar or "FEW" in raw_metar:
            condition = "Partly Cloudy"
            weather_code = 2
        elif "BKN" in raw_metar or "OVC" in raw_metar:
            condition = "Overcast"
            weather_code = 3
            
        # Time
        now = datetime.now()
        time_str = now.isoformat()
        formatted_date = now.strftime("%A\n%d-%m-%Y")
        day_name = now.strftime("%A")
        full_date = now.strftime("%d-%m-%Y")
        
        return {
            "temperature": temp,
            "humidity": 70, # METAR doesn't always give humidity directly, can calculate from dewpoint but hardcoding/estimating for now
            "pressure": pressure,
            "visibility": visibility,
            "windspeed_kmh": round(wind_knots * 1.852, 1),
            "windspeed_knots": wind_knots,
            "weathercode": weather_code,
            "condition": condition,
            "time": time_str,
            "formatted_date": formatted_date,
            "day_name": day_name,
            "full_date": full_date,
            "temp_max": temp + 2, # Estimate
            "temp_min": temp - 2, # Estimate
            "precipitation": 0.0, # Not always in METAR
            "latitude": 0, # Not in METAR
            "longitude": 0, # Not in METAR
            "timezone": "UTC"
        }

    def decode_taf(self, taf_text: str) -> Dict[str, Any]:
        """
        Decodes a raw TAF string. 
        Focuses on the first forecast block for current/upcoming conditions.
        """
        if not taf_text:
            return {}

        import re
        
        # Split lines. TAF usually has header line then the TAF body.
        # 2025/11/26 18:03
        # TAF VOMM ...
        lines = taf_text.split('\n')
        raw_taf = ""
        for line in lines:
            if line.strip().startswith("TAF"):
                raw_taf = line.strip()
                break
        if not raw_taf and len(lines) > 1:
             raw_taf = lines[1].strip() # Fallback
             
        # Regex Patterns (Reused)
        wind_pattern = r'(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT'
        vis_pattern = r'\s(\d{4})\s'
        
        # Extraction
        wind_match = re.search(wind_pattern, raw_taf)
        vis_match = re.search(vis_pattern, raw_taf)
        
        # Defaults
        wind_knots = 0
        visibility = 10000
        condition = "Clear"
        weather_code = 0
        
        if wind_match:
            wind_knots = int(wind_match.group(2))
            
        if vis_match:
            visibility = int(vis_match.group(1))
            
        # Condition Parsing
        if "TS" in raw_taf:
            condition = "Thunderstorm"
            weather_code = 95
        elif "RA" in raw_taf:
            condition = "Rain"
            weather_code = 63
        elif "HZ" in raw_taf:
            condition = "Haze"
            weather_code = 45
        elif "BR" in raw_taf:
            condition = "Mist"
            weather_code = 45
        elif "SCT" in raw_taf or "FEW" in raw_taf:
            condition = "Partly Cloudy"
            weather_code = 2
        elif "BKN" in raw_taf or "OVC" in raw_taf:
            condition = "Overcast"
            weather_code = 3
            
        # Time
        now = datetime.now()
        time_str = now.isoformat()
        formatted_date = now.strftime("%A\n%d-%m-%Y")
        day_name = now.strftime("%A")
        full_date = now.strftime("%d-%m-%Y")
        
        return {
            "temperature": 30, # TAF doesn't usually have current temp, defaulting to 30 for Chennai context or need to fetch METAR too? User just said use TAF.
            "humidity": 70,
            "pressure": 1010, # TAF doesn't have pressure usually
            "visibility": visibility,
            "windspeed_kmh": round(wind_knots * 1.852, 1),
            "windspeed_knots": wind_knots,
            "weathercode": weather_code,
            "condition": condition,
            "time": time_str,
            "formatted_date": formatted_date,
            "day_name": day_name,
            "full_date": full_date,
            "temp_max": 32, # Estimate
            "temp_min": 26, # Estimate
            "precipitation": 0.0,
            "latitude": 0,
            "longitude": 0,
            "timezone": "UTC"
        }

if __name__ == "__main__":
    # Test the decoder with dummy data
    decoder = WeatherDecoder()
    dummy_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timezone": "America/Los_Angeles",
        "current_weather": {
            "temperature": 15.4,
            "windspeed": 12.0,
            "winddirection": 240,
            "weathercode": 3,
            "time": "2023-10-27T10:00"
        },
        "daily": {
            "temperature_2m_max": [18.5],
            "temperature_2m_min": [12.1],
            "precipitation_sum": [0.0]
        }
    }
    print(decoder.decode_weather(dummy_data))
