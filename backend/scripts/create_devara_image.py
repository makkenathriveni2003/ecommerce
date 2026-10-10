import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_devara_image(output_path="frontend/public/images/devara_white_tshirt.jpg", width=1200, height=900):
    # 1. Base canvas: modern minimal warm neutral studio background (matching ShopZone palette)
    img = Image.new("RGB", (width, height), (245, 244, 240))
    draw = ImageDraw.Draw(img)

    # Soft radial gradient for studio lighting
    cx, cy = width // 2, height // 2
    for r in range(width, 0, -8):
        alpha = int(25 * (1 - r / width))
        val = 245 + int(alpha * 0.4)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(val, val, min(255, val + 2)))

    # Floor shadow beneath shirt
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    s_draw.ellipse([cx - 360, cy + 290, cx + 360, cy + 380], fill=(40, 42, 36, 45))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(30))
    img.paste(Image.alpha_composite(Image.new("RGBA", (width, height), (245, 244, 240, 255)), shadow_layer).convert("RGB"), (0, 0))
    draw = ImageDraw.Draw(img)

    # 2. Draw T-Shirt Silhouette (Unisex Crewneck White Tee)
    # Dimensions:
    body_left = cx - 240
    body_right = cx + 240
    body_top = cy - 230
    body_bottom = cy + 320

    # Shoulder line points
    left_shoulder = (cx - 260, body_top + 40)
    left_collar = (cx - 95, body_top + 10)
    center_collar_back = (cx, body_top + 5)
    center_collar_front = (cx, body_top + 45)
    right_collar = (cx + 95, body_top + 10)
    right_shoulder = (cx + 260, body_top + 40)

    # Sleeves
    left_sleeve_tip = (cx - 380, body_top + 170)
    left_armpit = (cx - 250, body_top + 160)
    right_sleeve_tip = (cx + 380, body_top + 170)
    right_armpit = (cx + 250, body_top + 160)

    # Shirt outer path
    shirt_poly = [
        left_collar,
        left_shoulder,
        (cx - 370, body_top + 110),
        left_sleeve_tip,
        left_armpit,
        (body_left, body_bottom),
        (body_right, body_bottom),
        right_armpit,
        right_sleeve_tip,
        (cx + 370, body_top + 110),
        right_shoulder,
        right_collar,
        center_collar_back,
    ]

    # White Fabric Body Fill with soft shading
    shirt_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shirt_layer)

    # Base white fabric (crisp #FAFAFA with very subtle warmth)
    sh_draw.polygon(shirt_poly, fill=(250, 250, 252, 255))

    # Inner collar scoop
    sh_draw.pieslice([cx - 95, body_top - 20, cx + 95, body_top + 65], 0, 180, fill=(235, 233, 228, 255))
    sh_draw.pieslice([cx - 90, body_top - 15, cx + 90, body_top + 55], 0, 180, fill=(245, 245, 248, 255))
    # Ribbed collar hem border
    sh_draw.arc([cx - 95, body_top - 20, cx + 95, body_top + 65], 0, 180, fill=(210, 208, 202, 255), width=4)

    # Subtle fabric fold shadows
    # Left drape
    sh_draw.line([left_armpit[0], left_armpit[1] + 10, body_left + 40, body_bottom - 20], fill=(225, 223, 218, 120), width=6)
    # Right drape
    sh_draw.line([right_armpit[0], right_armpit[1] + 10, body_right - 40, body_bottom - 20], fill=(225, 223, 218, 120), width=6)
    # Center torso drape
    sh_draw.line([cx - 15, body_top + 140, cx - 30, body_bottom - 40], fill=(235, 233, 228, 80), width=8)

    # Sleeve hems
    sh_draw.line([(cx - 370, body_top + 110), left_sleeve_tip], fill=(215, 213, 208, 200), width=3)
    sh_draw.line([(cx + 370, body_top + 110), right_sleeve_tip], fill=(215, 213, 208, 200), width=3)
    # Bottom hem
    sh_draw.line([(body_left, body_bottom), (body_right, body_bottom)], fill=(215, 213, 208, 220), width=3)

    # Soft outer edge definition
    shirt_layer = shirt_layer.filter(ImageFilter.SMOOTH)
    img.paste(shirt_layer, (0, 0), shirt_layer)
    draw = ImageDraw.Draw(img)

    # 3. DEVARA GRAPHIC PRINT ON THE CHEST
    # Print boundaries: center of chest
    print_cx = cx
    print_cy = cy + 40
    print_w = 260
    print_h = 320

    # Graphic container frame (cinematic dark poster with fiery red and silver accents)
    poster_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(poster_layer)

    # Dark distressed background for the graphic print
    p_box = [print_cx - 130, print_cy - 150, print_cx + 130, print_cy + 130]
    p_draw.rectangle(p_box, fill=(18, 20, 24, 245))

    # Red warrior/blood horizon glow
    p_draw.polygon([
        (print_cx - 130, print_cy + 30),
        (print_cx + 130, print_cy + 10),
        (print_cx + 130, print_cy + 130),
        (print_cx - 130, print_cy + 130)
    ], fill=(138, 22, 22, 240))

    # Sea waves / coastal storm motif
    for wave_x in range(print_cx - 130, print_cx + 130, 20):
        p_draw.arc([wave_x, print_cy + 60, wave_x + 35, print_cy + 95], 0, 180, fill=(230, 70, 60, 200), width=3)
        p_draw.arc([wave_x - 10, print_cy + 80, wave_x + 25, print_cy + 115], 0, 180, fill=(255, 120, 100, 180), width=2)

    # Menacing shark fin / rocky cliffs in crimson waters
    p_draw.polygon([
        (print_cx + 50, print_cy + 75),
        (print_cx + 75, print_cy + 40),
        (print_cx + 85, print_cy + 75)
    ], fill=(12, 14, 18, 255))
    p_draw.polygon([
        (print_cx - 80, print_cy + 85),
        (print_cx - 55, print_cy + 45),
        (print_cx - 45, print_cy + 85)
    ], fill=(12, 14, 18, 255))

    # The Trident / Weapon Motif (Devara's iconic curved trident)
    trident_x = print_cx
    p_draw.line([trident_x, print_cy - 120, trident_x, print_cy + 30], fill=(225, 30, 30, 255), width=4)
    # Trident prongs
    p_draw.arc([trident_x - 35, print_cy - 130, trident_x + 35, print_cy - 70], 0, 180, fill=(225, 30, 30, 255), width=4)
    p_draw.line([trident_x - 35, print_cy - 135, trident_x - 35, print_cy - 100], fill=(225, 30, 30, 255), width=4)
    p_draw.line([trident_x + 35, print_cy - 135, trident_x + 35, print_cy - 100], fill=(225, 30, 30, 255), width=4)
    p_draw.polygon([
        (trident_x, print_cy - 145),
        (trident_x - 8, print_cy - 120),
        (trident_x + 8, print_cy - 120)
    ], fill=(255, 230, 100, 255))

    # Bold "DEVARA" Typography
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 38)
        font_sub = ImageFont.truetype("arialbd.ttf", 14)
        font_tag = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_tag = font_title

    # Title with dual-shadow cinematic style
    title_text = "DEVARA"
    p_draw.text((print_cx - 86, print_cy - 22), title_text, font=font_title, fill=(20, 2, 2, 255))
    p_draw.text((print_cx - 88, print_cy - 24), title_text, font=font_title, fill=(255, 255, 255, 255))

    # Subtitle: PART 1
    p_draw.text((print_cx - 32, print_cy + 18), "PART - 1", font=font_sub, fill=(255, 200, 50, 255))

    # Tagline: FEAR IS HEREDITY
    p_draw.text((print_cx - 62, print_cy + 105), "FEAR IS HEREDITY", font=font_tag, fill=(240, 240, 240, 220))

    # Distressed border lines around the print
    p_draw.rectangle(p_box, outline=(60, 64, 72, 180), width=2)
    p_draw.rectangle([p_box[0] + 5, p_box[1] + 5, p_box[2] - 5, p_box[3] - 5], outline=(180, 40, 40, 140), width=1)

    # Composite graphic onto shirt
    img.paste(poster_layer, (0, 0), poster_layer)

    # 4. Badge on top right: "40% OFF" Ribbon Pill
    badge_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge_layer)
    badge_x, badge_y = cx + 200, cy - 180
    b_draw.rounded_rectangle([badge_x, badge_y, badge_x + 95, badge_y + 36], radius=18, fill=(185, 28, 28, 250))
    try:
        font_badge = ImageFont.truetype("arialbd.ttf", 15)
    except Exception:
        font_badge = ImageFont.load_default()
    b_draw.text((badge_x + 14, badge_y + 9), "40% OFF", font=font_badge, fill=(255, 255, 255, 255))
    img.paste(badge_layer, (0, 0), badge_layer)

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "JPEG", quality=92)
    print(f"Successfully generated {output_path} ({width}x{height})")

if __name__ == "__main__":
    create_devara_image()
