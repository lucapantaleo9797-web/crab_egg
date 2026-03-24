#!/usr/bin/env python3
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import colorsys

def remove_text_background(image):
    """Remove the repetitive text pattern background from the crab image."""
    # Convert to RGBA
    img_rgba = image.convert("RGBA")
    data = np.array(img_rgba)
    
    # The background appears to be light gray/white with text
    # We'll make pixels that are too light (grayish) transparent
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    
    # Create mask for background (light gray pixels)
    # Adjust threshold based on the background color
    gray_mask = (r > 200) & (g > 200) & (b > 200)
    
    # Also check for pixels that are very close to gray (similar R,G,B values)
    gray_diff = np.abs(r.astype(float) - g.astype(float)) + \
                np.abs(g.astype(float) - b.astype(float)) + \
                np.abs(r.astype(float) - b.astype(float))
    
    gray_similar_mask = (gray_diff < 30) & (r > 180)
    
    # Combine masks
    background_mask = gray_mask | gray_similar_mask
    
    # Set alpha to 0 for background pixels
    data[background_mask] = [0, 0, 0, 0]
    
    # Clean up edges with slight blur
    result = Image.fromarray(data, 'RGBA')
    
    # Apply slight gaussian blur to alpha channel for smoother edges
    alpha = result.split()[3]
    alpha = alpha.filter(ImageFilter.GaussianBlur(1))
    result.putalpha(alpha)
    
    return result

def create_futuristic_city(width, height):
    """Generate a cyberpunk-style futuristic city scene."""
    # Create base image with dark gradient background
    img = Image.new('RGB', (width, height), (10, 0, 20))
    draw = ImageDraw.Draw(img)
    
    # Create gradient sky
    for y in range(height // 2):
        # Purple to dark blue gradient
        ratio = y / (height // 2)
        r = int(30 * (1 - ratio) + 10 * ratio)
        g = int(0 * (1 - ratio) + 10 * ratio)
        b = int(50 * (1 - ratio) + 30 * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Draw buildings with neon lights
    buildings = []
    
    # Background layer of buildings (smaller, darker)
    for i in range(15):
        x = random.randint(-50, width)
        w = random.randint(40, 80)
        h = random.randint(150, 300)
        y = height - h
        
        # Dark building color
        building_color = (20, 20, 30)
        draw.rectangle([(x, y), (x + w, height)], fill=building_color)
        
        # Add window lights
        for wy in range(y + 10, height - 10, 15):
            for wx in range(x + 5, x + w - 5, 10):
                if random.random() > 0.3:
                    # Random neon colors for windows
                    hue = random.choice([0.8, 0.9, 0.5, 0.3])  # Purple, pink, cyan, green
                    lightness = random.uniform(0.6, 0.8)
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, lightness)
                    window_color = tuple(int(c * 255) for c in rgb)
                    draw.rectangle([(wx, wy), (wx + 6, wy + 10)], fill=window_color)
    
    # Foreground layer of buildings (larger, more detailed)
    for i in range(10):
        x = random.randint(-100, width)
        w = random.randint(80, 150)
        h = random.randint(250, 450)
        y = height - h
        
        # Slightly lighter building
        building_color = (30, 30, 40)
        draw.rectangle([(x, y), (x + w, height)], fill=building_color)
        buildings.append((x, y, w, h))
        
        # Add neon strips
        if random.random() > 0.5:
            neon_color = random.choice([(255, 0, 100), (0, 255, 255), (255, 0, 255), (100, 255, 0)])
            for ny in range(y, y + h - 50, 60):
                draw.rectangle([(x, ny), (x + w, ny + 2)], fill=neon_color)
        
        # Add windows with glow
        for wy in range(y + 20, height - 20, 25):
            for wx in range(x + 10, x + w - 10, 15):
                if random.random() > 0.4:
                    hue = random.choice([0.8, 0.9, 0.5, 0.3])
                    lightness = random.uniform(0.7, 0.9)
                    rgb = colorsys.hsv_to_rgb(hue, 0.9, lightness)
                    window_color = tuple(int(c * 255) for c in rgb)
                    # Window
                    draw.rectangle([(wx, wy), (wx + 10, wy + 18)], fill=window_color)
                    # Glow effect
                    glow_color = tuple(int(c * 0.3) for c in window_color)
                    draw.rectangle([(wx - 2, wy - 2), (wx + 12, wy + 20)], outline=glow_color, width=2)
    
    # Add flying vehicles (light streaks)
    for i in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(50, height // 2)
        x2 = x1 + random.randint(50, 150)
        y2 = y1 + random.randint(-10, 10)
        
        # Random neon color for light trail
        trail_color = random.choice([(255, 100, 150), (100, 255, 255), (255, 150, 100)])
        draw.line([(x1, y1), (x2, y2)], fill=trail_color, width=2)
        
        # Brighter head of vehicle
        draw.ellipse([(x2 - 4, y2 - 4), (x2 + 4, y2 + 4)], fill=(255, 255, 255))
    
    # Add some fog/atmosphere
    fog = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    fog_draw = ImageDraw.Draw(fog)
    
    # Bottom fog
    for y in range(height - 100, height):
        alpha = int((y - (height - 100)) * 1.5)
        fog_draw.rectangle([(0, y), (width, y + 1)], fill=(100, 50, 150, alpha))
    
    # Composite fog
    img = Image.alpha_composite(img.convert('RGBA'), fog)
    
    # Add some bloom/glow effect
    img_blur = img.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.blend(img, img_blur, 0.3)
    
    return img.convert('RGB'), buildings

def create_holographic_effect(crab_img):
    """Add holographic/glitch effects to the crab."""
    # Create copies for RGB shift effect
    r, g, b, a = crab_img.split()
    
    # Shift channels for glitch effect
    r = r.transform(r.size, Image.AFFINE, (1, 0, 3, 0, 1, 0))
    b = b.transform(b.size, Image.AFFINE, (1, 0, -3, 0, 1, 0))
    
    # Recombine
    glitched = Image.merge('RGBA', (r, g, b, a))
    
    # Add scan lines
    draw = ImageDraw.Draw(glitched)
    for y in range(0, glitched.height, 4):
        draw.line([(0, y), (glitched.width, y)], fill=(0, 255, 255, 50), width=1)
    
    # Enhance colors for neon effect
    enhancer = ImageEnhance.Color(glitched)
    glitched = enhancer.enhance(1.5)
    
    return glitched

def main():
    print("Loading crab image...")
    crab_original = Image.open('/Users/macbookpro/Desktop/download.jpg')
    
    print("Removing text background...")
    crab_clean = remove_text_background(crab_original)
    
    # Create futuristic city background
    print("Generating futuristic city scene...")
    city_bg, buildings = create_futuristic_city(1920, 1080)
    
    # Scale crab to be giant (towering over buildings)
    # Make it about 1/3 of the image height
    crab_height = 400
    aspect_ratio = crab_clean.width / crab_clean.height
    crab_width = int(crab_height * aspect_ratio)
    
    print("Scaling and positioning giant crab...")
    crab_scaled = crab_clean.resize((crab_width, crab_height), Image.Resampling.LANCZOS)
    
    # Add holographic effects to make it look more futuristic
    print("Adding holographic effects...")
    crab_holographic = create_holographic_effect(crab_scaled)
    
    # Position crab in the city (slightly off-center for drama)
    crab_x = 1920 // 2 - crab_width // 2 + 100
    crab_y = 1080 - crab_height + 50  # Positioned to look like it's walking among buildings
    
    # Create composite
    print("Compositing final image...")
    final = city_bg.copy().convert('RGBA')
    
    # Add crab shadow for depth
    shadow = Image.new('RGBA', crab_scaled.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    # Create elliptical shadow
    shadow_draw.ellipse([(0, crab_height - 50), (crab_width, crab_height)], 
                        fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    final.paste(shadow, (crab_x, crab_y + 50), shadow)
    
    # Paste the holographic crab
    final.paste(crab_holographic, (crab_x, crab_y), crab_holographic)
    
    # Add some additional effects
    # Neon glow around the crab
    crab_glow = crab_holographic.filter(ImageFilter.GaussianBlur(radius=10))
    enhancer = ImageEnhance.Brightness(crab_glow)
    crab_glow = enhancer.enhance(1.5)
    
    # Paste glow behind crab
    glow_layer = Image.new('RGBA', final.size, (0, 0, 0, 0))
    glow_layer.paste(crab_glow, (crab_x, crab_y), crab_glow)
    final = Image.alpha_composite(final, glow_layer)
    
    # Add "CRABZILLA 2089" holographic text
    draw = ImageDraw.Draw(final)
    text = "CRABZILLA 2089"
    # Using basic font, but with effects
    for offset in range(3):
        draw.text((1920 // 2 - 100 + offset, 100 + offset), text, 
                 fill=(0, 255, 255, 150 - offset * 50))
    draw.text((1920 // 2 - 100, 100), text, fill=(255, 255, 255, 255))
    
    # Final color adjustments
    final = final.convert('RGB')
    enhancer = ImageEnhance.Contrast(final)
    final = enhancer.enhance(1.1)
    
    print("Saving final image...")
    final.save('/Users/macbookpro/Desktop/crab_futuristic_city.jpg', 'JPEG', quality=95)
    print("Done! Giant holographic crab now terrorizes the cyberpunk city!")

if __name__ == "__main__":
    main()