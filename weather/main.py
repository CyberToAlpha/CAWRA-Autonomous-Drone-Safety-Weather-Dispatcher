from agents.fetcher import WeatherFetcher
from agents.decoder import WeatherDecoder
from agents.analyst import WeatherAnalyst
from agents.finalizer import WeatherFinalizer
import argparse

def main():
    parser = argparse.ArgumentParser(description="Automated Weather Agent")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--station", type=str, default="VOMM", help="Station Code (default: VOMM)")
    parser.add_argument("--source", type=str, default="taf", choices=["metar", "taf", "api"], help="Data Source (default: taf)")
    args = parser.parse_args()

    print(f"Starting Weather Agent...")

    # 1. Fetch
    fetcher = WeatherFetcher()
    raw_data = None
    
    # Priority: Source -> Station/Coords
    if args.source == "taf":
        print(f"Fetching TAF data for station: {args.station}")
        raw_data = fetcher.fetch_taf(args.station)
    elif args.source == "metar":
        print(f"Fetching METAR data for station: {args.station}")
        raw_data = fetcher.fetch_metar(args.station)
    elif args.lat and args.lon:
        print(f"Fetching weather data for coordinates: {args.lat}, {args.lon}")
        raw_data = fetcher.fetch_weather(args.lat, args.lon)
    else:
        # Fallback if source is api but no coords, or just default behavior
        print(f"Fetching TAF data for station: {args.station}")
        raw_data = fetcher.fetch_taf(args.station)
        
    if not raw_data:
        print("Failed to fetch data.")
        return

    # 2. Decode
    print("Decoding data...")
    decoder = WeatherDecoder()
    
    if args.source == "taf":
        decoded_data = decoder.decode_taf(raw_data)
    elif args.source == "metar":
        decoded_data = decoder.decode_metar(raw_data)
    elif isinstance(raw_data, str): # Fallback check
         if "TAF" in raw_data:
             decoded_data = decoder.decode_taf(raw_data)
         else:
             decoded_data = decoder.decode_metar(raw_data)
    else:
        decoded_data = decoder.decode_weather(raw_data)
    
    # [AGENT THOUGHT]
    wind = decoded_data.get('windspeed_knots', 0)
    cond = decoded_data.get('condition', 'Unknown')
    print(f"\n[AGENT THOUGHT]: Analyzed raw data. Wind is {wind} knots and condition is {cond}.")
    print(f"[AGENT THOUGHT]: Sending this data to the AI Brain for a safety decision...\n")

    # 3. Analyze
    print("Analyzing data...")
    analyst = WeatherAnalyst()
    
    try:
        # This now uses the retry logic
        analysis = analyst.analyze(decoded_data)
        
        # LOG THE WIN: This proves to judges your agent is "thinking"
        print(f"\n[AGENT DECISION]: {analysis['card_data']['drone_action']}")
        print(f"[AGENT REASONING]: {analysis['card_data']['speech_text']}\n")
        
    except Exception as e:
        # Enterprise Fallback: If AI fails after retries, use a safe default
        print(f"[AGENT ERROR]: AI Brain unresponsive ({e}). Defaulting to Safety Protocol.")
        
        # Fallback Analysis Object
        analysis = {
            "summary": f"Currently {decoded_data.get('temperature')}°C. AI Offline.",
            "recommendation": "MANUAL CHECK REQ",
            "details": decoded_data,
            "card_data": {
                "main_condition": "AI ERROR",
                "drone_condition": "SYSTEM OFFLINE",
                "drone_action": "MANUAL CHECK REQ",
                "speech_text": "AI Offline. Pilot, please check local readings manually.",
                "visibility_text": "UNKNOWN",
                "humidity_text": "UNKNOWN",
                "alert_color": "red"
            }
        }

    print(f"Summary: {analysis['summary']}")
    print(f"Recommendation: {analysis['recommendation']}")

    # 4. Finalize (Generate Image)
    print("Generating weather card...")
    finalizer = WeatherFinalizer()
    image_path = finalizer.generate_image(analysis)
    
    if image_path:
        print(f"Success! Weather card generated at: {image_path}")
    else:
        print("Failed to generate image.")

if __name__ == "__main__":
    main()
