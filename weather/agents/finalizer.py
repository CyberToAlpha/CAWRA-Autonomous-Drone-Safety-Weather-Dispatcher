from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, Tuple
import os
import random

class WeatherFinalizer:
    """
    Agent responsible for generating the final visual weather report matching the specific template.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Font paths (Windows defaults)
        self.font_regular = "arial.ttf"
        self.font_bold = "arialbd.ttf"
        self.font_italic = "ariali.ttf"
        
        # Custom Fonts
        self.font_racing = os.path.join("assets", "RacingSansOne-Regular.ttf")
        self.font_roca = os.path.join("assets", "RocaOne-Regular.ttf") # User needs to provide this or it falls back

    def _get_font(self, font_name: str, size: int):
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            # Fallback to Arial if custom font missing
            try:
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()

    def _get_background(self, width: int, height: int, condition: str) -> Image.Image:
        """
        Loads a background template from assets based on condition.
        """
        # Map condition to filename keywords
        c = condition.lower()
        filename = "template_clear.png" # Default
        if "rain" in c:
            filename = "template_rain.png"
        elif "storm" in c or "thunder" in c:
            filename = "template_storm.png"
        elif "cloud" in c or "overcast" in c:
            filename = "template_cloudy.png"
        elif "mist" in c or "fog" in c:
            filename = "template_mist.png"
        elif "wind" in c:
            filename = "template_windy.png"
        elif "clear" in c or "sunny" in c:
            filename = "template_clear.png"
            
        asset_path = os.path.join("assets", filename)
        
        # Try to load asset
        if os.path.exists(asset_path):
            try:
                bg = Image.open(asset_path).convert('RGB')
                bg = bg.resize((width, height), Image.Resampling.LANCZOS)
                return bg
            except Exception as e:
                print(f"Failed to load asset {asset_path}: {e}")

        # Fallback to black if template missing (shouldn't happen if setup correctly)
        return Image.new('RGB', (width, height), (0, 0, 0))

    def _draw_speech_text(self, draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, font: ImageFont.ImageFont, size: Tuple[int, int] = (350, 200)):
        """Draws text inside the pre-existing speech bubble."""
        x, y = xy
        w, h = size
        
        # Text wrapping
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            bbox = draw.textbbox((0, 0), " ".join(current_line), font=font)
            if bbox[2] > w - 20: # Reduced padding
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        # Draw text centered in bubble area
        text_y = y + (h - len(lines) * 25) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_x = x + (w - bbox[2]) // 2
            draw.text((text_x, text_y), line, font=font, fill=(0, 0, 0))
            text_y += 25

    def generate_image(self, analysis: Dict[str, Any]) -> str:
        if not analysis or 'details' not in analysis:
            return ""

        details = analysis['details']
        card_data = analysis.get('card_data', {})
        
        # 1. Grab the AI data specifically with fallbacks
        ai_speech = card_data.get('speech_text')
        ai_action = card_data.get('drone_action')
        
        # 2. Debug Print (CRITICAL: Proves to you it's working)
        print(f"[FINALIZER DEBUG] Speech Text Found: {ai_speech}")
        print(f"[FINALIZER DEBUG] Drone Action Found: {ai_action}")

        if not ai_speech:
            # Fallback if AI didn't return text
            ai_speech = analysis.get('recommendation', "Check local conditions.")
            
        drone_action = ai_action if ai_action else "CHECK MANUAL"
        
        # Canvas
        width, height = 1080, 1350
        image = self._get_background(width, height, card_data.get('main_condition', ''))
        draw = ImageDraw.Draw(image)
        
        # Fonts
        font_date_day = self._get_font(self.font_roca, 60)
        font_date_full = self._get_font(self.font_roca, 50)
        font_main = self._get_font(self.font_racing, 180)
        font_temp = self._get_font(self.font_roca, 40)
        font_bubble = self._get_font(self.font_roca, 20)
        font_mid = self._get_font(self.font_bold, 45)
        font_footer = self._get_font(self.font_bold, 28)

        # Center text helper
        def draw_centered(text, y, font, fill="white", shadow=True, stroke_width=0):
            bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
            w = bbox[2] - bbox[0]
            x = (width - w) // 2
            if shadow:
                draw.text((x+3, y+3), text, font=font, fill=(0,0,0,128), stroke_width=stroke_width)
            draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke_width)
            return y + (bbox[3] - bbox[1])

        # 1. Date (Dynamic)
        day_name = details.get('day_name', 'Sunday')
        full_date = details.get('full_date', '17-08-2025')
        
        y_cursor = 250
        draw_centered(day_name, y_cursor, font_date_day, stroke_width=2)
        y_cursor += 70
        draw_centered(full_date, y_cursor, font_date_full)

        # 2. Main Condition (Dynamic)
        y_cursor += 100
        main_cond = card_data.get('main_condition', 'WINDY')
        draw_centered(main_cond, y_cursor, font_main, stroke_width=3)

        # 3. Temperatures (Dynamic)
        y_cursor += 220
        temp_max = details.get('temp_max', 0)
        temp_min = details.get('temp_min', 0)
        draw_centered(f"Max Temp : {temp_max}°C", y_cursor, font_temp, stroke_width=1)
        y_cursor += 50
        draw_centered(f"Min Temp : {temp_min}°C", y_cursor, font_temp, stroke_width=1)

        # 4. Speech Bubble Text (Dynamic)
        # User requested: "little below from center to my right side edge"
        # Estimated: X=750 (Right), Y=700 (Below Center)
        # Adjusted: X moved right from 750 to 825. Y moved down from 700 to 745.
        self._draw_speech_text(draw, (798, 650), ai_speech, font_bubble, size=(271, 207))

        # 5. Middle Info (Dynamic)
        y_cursor += 200
        mid_text = f"{main_cond} WITH HUMIDITY OF {card_data.get('humidity_text', '')}"
        draw_centered(mid_text, y_cursor, font_mid)
        y_cursor += 60
        draw_centered(f"AND {card_data.get('visibility_text', '')}", y_cursor, font_mid)
        
        # 6. Footer Data (Dynamic)
        footer_h = 250
        footer_y = height - footer_h
        data_y = footer_y + 90 
        
        pressure = details.get('pressure', 1000)
        wind_knots = details.get('windspeed_knots', 0)
        
        draw.text((100, data_y), f"PRESSUR: {pressure}hPa - NORMAL", font=font_footer, fill="white")
        draw.text((600, data_y), f"WIND KNOT: {wind_knots} Knots (MAX)", font=font_footer, fill="white")
        
        cond_y = data_y + 50
        draw_centered(drone_action, cond_y + 30, font_footer, fill="white", shadow=False)

        # Save
        filename = f"weather_card_{details.get('time', 'now').replace(':', '-')}.png"
        filepath = os.path.join(self.output_dir, filename)
        image.save(filepath)
        print(f"Image saved to {filepath}")
        return filepath

if __name__ == "__main__":
    # Test
    finalizer = WeatherFinalizer()
    dummy_data = {
        "details": {
            "day_name": "Sunday",
            "full_date": "17-08-2025",
            "temp_max": 27,
            "temp_min": 24,
            "pressure": 1001,
            "windspeed_kmh": 18.52,
            "time": "2025-08-17T12:00"
        },
        "card_data": {
            "main_condition": "WINDY",
            "humidity_text": "60 - 67%",
            "visibility_text": "GOOD VISIBILITY",
            "speech_text": "Cloudy skies with hazy sunshine through the day and a fair breeze.",
            "drone_action": "GOOD CONDITION TO OPERATE DRONE"
        }
    }
    finalizer.generate_image(dummy_data)
