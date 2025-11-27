from agents.finalizer import WeatherFinalizer
from datetime import datetime

from agents.finalizer import WeatherFinalizer
from agents.analyst import WeatherAnalyst
from datetime import datetime

def test_variations():
    finalizer = WeatherFinalizer()
    analyst = WeatherAnalyst()
    
    # Test Scenarios with raw data for the AI to analyze
    scenarios = [
        {
            "condition": "Clear",
            "temperature": 28,
            "windspeed_knots": 5,
            "visibility": 10000,
            "humidity": 40,
            "weathercode": 0
        },
        {
            "condition": "Storm",
            "temperature": 24,
            "windspeed_knots": 25, # High wind -> Should trigger warning
            "visibility": 1500,    # Low vis -> Should trigger warning
            "humidity": 85,
            "weathercode": 95
        },
        {
            "condition": "Mist",
            "temperature": 22,
            "windspeed_knots": 8,
            "visibility": 1000,    # Very low vis -> Should trigger warning
            "humidity": 90,
            "weathercode": 45
        },
        {
            "condition": "Windy",
            "temperature": 26,
            "windspeed_knots": 22, # High wind -> Should trigger warning
            "visibility": 10000,
            "humidity": 50,
            "weathercode": 1
        }
    ]

    print("Generating AI-powered test cards...")
    for data in scenarios:
        cond = data['condition']
        print(f"\nTesting Scenario: {cond} (Wind: {data['windspeed_knots']}kt, Vis: {data['visibility']}m)")
        
        # AI Analysis
        analysis = analyst.analyze(data)
        
        # Add time for filename uniqueness
        analysis['details']['time'] = f"2025-TEST-{cond}"
        analysis['details']['day_name'] = "TestDay"
        analysis['details']['full_date'] = "01-01-2025"
        
        print(f"[AI DECISION]: {analysis['card_data']['drone_action']}")
        print(f"[AI SPEECH]: {analysis['card_data']['speech_text']}")
        
        finalizer.generate_image(analysis)

if __name__ == "__main__":
    test_variations()
