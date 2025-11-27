from agents.analyst import WeatherAnalyst
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def debug_analyst():
    print("--- Debugging WeatherAnalyst ---")
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    analyst = WeatherAnalyst()
    # Force the model we want to test
    analyst.model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print(f"Model: {analyst.model.model_name}")
    
    dummy_data = {
        "temperature": 28,
        "condition": "Cloudy",
        "windspeed_knots": 12,
        "visibility": 8000
    }
    
    print("\nAttempting Analysis...")
    try:
        result = analyst.analyze(dummy_data)
        print("\n[SUCCESS] Analysis Result:")
        print(result['card_data'])
    except Exception as e:
        print(f"\n[ERROR] Analysis Failed: {e}")
        
    print("\n--- Listing Available Models ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Failed to list models: {e}")

if __name__ == "__main__":
    debug_analyst()
