import os
from PIL import Image, ImageDraw, ImageFont

def create_logo():
    # Size
    size = (4096, 4096)
    
    # Colors
    bg_color = "#1a1a24"
    accent_color = "#7c5cfc"
    text_color = "#ffffff"
    
    # Create image
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded background
    r = 640
    width_bg = 128
    draw.rounded_rectangle([(160, 160), (3936, 3936)], radius=r, fill=bg_color, outline=accent_color, width=width_bg)
    
    # Draw "Q" symbol (simplified geometric shape)
    # Circle
    center = (2048, 1760)
    radius = 960
    width_circle = 192
    draw.ellipse([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], outline=text_color, width=width_circle)
    
    # Play triangle inside
    draw.polygon([(1840, 1440), (1840, 2080), (2400, 1760)], fill=accent_color)
    
    # "Quick" tail
    width_tail = 192
    draw.line([(2560, 2400), (3040, 3040)], fill=text_color, width=width_tail)
    
    # Save as PNG
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    img.save("assets/logo.png")
    img.save("assets/icon.ico", format="ICO", sizes=[(256, 256)])
    print("Logo created in assets/logo.png and assets/icon.ico")

if __name__ == "__main__":
    create_logo()
