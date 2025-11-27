from typing import Dict, Any, Literal
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field
from google.api_core import retry

# Load environment variables
load_dotenv()

# 1. Define the Structure (The Contract)
class WeatherDecision(BaseModel):
    condition_category: Literal["CLEAR", "CLOUDY", "RAINY", "WINDY", "STORMY", "MISTY", "SNOWY"]
    speech_text: str = Field(description="A short, witty, or serious 1-sentence remark for a drone pilot.")
    drone_action: str = Field(description="Short action command like 'SAFE TO FLY' or 'GROUND ALL DRONES'.")
    drone_condition: str = Field(description="Short description of flying conditions, e.g., 'PERFECT CONDITIONS'.")
    is_safe: bool = Field(description="Boolean indicating if it is safe to fly.")

class WeatherAnalyst:
    """
    Agent responsible for analyzing weather data and generating insights using AI.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found in .env file. AI features will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def analyze(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the weather data to provide a summary and recommendations using AI.
        """
        if not weather_data:
            return {"summary": "No data available", "recommendation": "N/A"}

        # Basic data extraction for fallback/context
        temp = weather_data.get('temperature', 0)
        condition = weather_data.get('condition', 'Unknown')
        wind_knots = weather_data.get('windspeed_knots', 0)
        visibility = weather_data.get('visibility', 10000)
        humidity = weather_data.get('humidity', 50)
        weather_code = weather_data.get('weathercode', 0)

        # Defaults
        decision = WeatherDecision(
            condition_category="CLEAR",
            speech_text=f"Expect {condition} conditions.",
            drone_action="SAFE TO FLY",
            drone_condition="GOOD CONDITIONS",
            is_safe=True
        )
        
        if self.model:
            try:
                prompt = f"""
                You are the Chief Safety Officer for a Drone Startup. 
                Analyze this weather data for Chennai (VOMM) and decide if we can fly.
                
                Data:
                - Condition: {condition}
                - Wind: {wind_knots} knots
                - Visibility: {visibility} meters
                - Temperature: {temp}°C
                
                Rules:
                - If wind > 20 knots or gusts > 25, it is WINDY and unsafe.
                - If visibility < 3000m, it is MISTY/LOW VISIBILITY.
                - Be professional but engaging.
                """
                
                # Ask the LLM to return JSON matching our Pydantic model
                result = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=WeatherDecision
                    )
                )
                
                # Parse into Python object
                decision = WeatherDecision.model_validate_json(result.text)
                    
            except Exception as e:
                print(f"AI Analysis failed: {e}")
                # Fallback logic
                is_bad_flying = (wind_knots > 15) or (weather_code >= 51) or (visibility < 2000)
                if is_bad_flying:
                    decision.drone_action = "DRONE OPERATION IS NOT ADVISED."
                    decision.drone_condition = "BAD CONDITION TO OPERATE DRONE"
                    decision.is_safe = False
                    decision.condition_category = "STORMY" if "storm" in condition.lower() else "WINDY"

        # Map Decision to Finalizer Format
        alert_color = "green" if decision.is_safe else "red"
        if "CAUTION" in decision.drone_action:
            alert_color = "orange"

        # 4. Visibility Text
        if visibility > 9000:
            vis_text = "GOOD VISIBILITY"
        elif visibility > 2000:
            vis_text = "MODERATE VISIBILITY"
        else:
            vis_text = "POOR VISIBILITY"

        # 5. Humidity Text (Range simulation)
        hum_min = max(0, humidity - 5)
        hum_max = min(100, humidity + 5)
        humidity_text = f"{hum_min} - {hum_max}%"

        # Generate Summary
        summary = f"Currently {temp}°C and {condition.lower()}."
        
        return {
            "summary": summary,
            "recommendation": decision.drone_action,
            "details": weather_data,
            "card_data": {
                "main_condition": decision.condition_category.replace("_", " "), # e.g. RAINY_DAY -> RAINY DAY
                "drone_condition": decision.drone_condition,
                "drone_action": decision.drone_action,
                "speech_text": decision.speech_text,
                "visibility_text": vis_text,
                "humidity_text": humidity_text,
                "alert_color": alert_color
            }
        }

if __name__ == "__main__":
    analyst = WeatherAnalyst()
    dummy_data = {
        "temperature": 15.4,
        "condition": "Overcast",
        "precipitation": 0.0,
        "windspeed_knots": 12.0,
        "visibility": 10000
    }
    print(analyst.analyze(dummy_data))
