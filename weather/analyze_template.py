from PIL import Image
import sys

def find_bubble(image_path):
    try:
        img = Image.open(image_path).convert('L') # Grayscale
        width, height = img.size
        pixels = img.load()
        # Find max brightness and quadrant stats
        max_val = 0
        max_pos = (0, 0)
        
        sum_tl, sum_tr, sum_bl, sum_br = 0, 0, 0, 0
        count = (width // 2) * (height // 2)
        
        for y in range(height):
            for x in range(width):
                val = pixels[x, y]
                if val > max_val:
                    max_val = val
                    max_pos = (x, y)
                
                if x < width // 2:
                    if y < height // 2: sum_tl += val
                    else: sum_bl += val
                else:
                    if y < height // 2: sum_tr += val
                    else: sum_br += val
                    
        print(f"Max Brightness: {max_val} at {max_pos}")
        print(f"Avg Brightness TL: {sum_tl / count}")
        print(f"Avg Brightness TR: {sum_tr / count}")
        print(f"Avg Brightness BL: {sum_bl / count}")
        print(f"Avg Brightness BR: {sum_br / count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_bubble("assets/template_clear.png")
