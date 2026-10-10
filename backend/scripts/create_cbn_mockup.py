import os
import numpy as np
from PIL import Image, ImageFilter

def create_cbn_white_tshirt_mockup(
    portrait_path="C:/Users/Dell/.gemini/antigravity/brain/fa69aaf8-447a-4a12-8fed-73fca83bb2f8/.user_uploaded/media_1791613117491_4e7a9a93.png",
    output_path="frontend/public/images/cbn_referral_shirt.jpg",
    shirt_template="frontend/public/images/tdp_logo_tshirt.jpg"
):
    # 1. Load original shirt photo
    img = Image.open(shirt_template)
    arr = np.array(img, dtype=float)
    h, w, _ = arr.shape
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    sat = np.where(max_c == 0, 0, (max_c - min_c) / max_c)
    lum_bg = 0.299 * r + 0.587 * g + 0.114 * b

    # Background mask
    bg_score = np.clip((lum_bg - 220) / 15, 0, 1) * np.clip((0.15 - sat) / 0.10, 0, 1)
    bg_weight = bg_score
    shirt_weight = 1.0 - bg_weight

    # Luminance
    lum = 0.5 * r + 0.5 * g
    clean_lum = lum.copy()

    # Inpaint chest graphic area cleanly
    chest_y1, chest_y2 = 78, 305
    chest_x1, chest_x2 = 80, 355
    in_chest_box = np.zeros((h, w), dtype=bool)
    in_chest_box[chest_y1:chest_y2, chest_x1:chest_x2] = True

    is_pure_fabric = in_chest_box & (sat > 0.82) & (r > 190) & (g > 150) & (b < 95)
    needs_inpaint = in_chest_box & (~is_pure_fabric)

    # Dilate needs_inpaint mask by 2 pixels to cover anti-aliased edges
    mask_img = Image.fromarray(np.uint8(needs_inpaint * 255), mode='L')
    dilated_mask = np.array(mask_img.filter(ImageFilter.MaxFilter(5))) > 0

    # Row-by-row horizontal interpolation across dilated mask
    for y in range(chest_y1, chest_y2):
        mask_row = dilated_mask[y]
        if not np.any(mask_row):
            continue
        valid_xs = np.where(in_chest_box[y] & (~dilated_mask[y]))[0]
        bad_xs = np.where(mask_row)[0]
        if len(valid_xs) >= 2:
            clean_lum[y, bad_xs] = np.interp(bad_xs, valid_xs, clean_lum[y, valid_xs])

    # Smooth the inpainted region
    patch_img = Image.fromarray(np.uint8(np.clip(clean_lum, 0, 255)), mode='L')
    blurred_patch = np.array(patch_img.filter(ImageFilter.GaussianBlur(1.8)), dtype=float)
    clean_lum[dilated_mask] = blurred_patch[dilated_mask]

    # Normalize luminance across shirt fabric
    lum_norm = np.clip((clean_lum - 125) / (246 - 125), 0.0, 1.0)
    white_tone = 200.0 + 53.0 * (lum_norm ** 0.88)

    # Construct pristine white shirt
    result = np.zeros_like(arr)
    for c in range(3):
        bg_c = lum_bg
        fg_c = white_tone + (1.0 if c == 2 else 0.0)
        result[:, :, c] = bg_weight * bg_c + shirt_weight * fg_c

    white_tee = Image.fromarray(np.uint8(np.clip(result, 0, 255)))

    # Upscale white tee to high resolution 1200 x 1440
    target_w = 1200
    target_h = int(h * (target_w / w))
    white_tee_hd = white_tee.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Load portrait graphic
    portrait = Image.open(portrait_path).convert('RGBA')

    # Target print width on chest (proportional to chest width)
    pw = 490
    ph = int(portrait.height * (pw / portrait.width))
    portrait_hd = portrait.resize((pw, ph), Image.Resampling.LANCZOS)

    # Position: center chest
    px = (target_w - pw) // 2
    py = int(target_h * 0.26)

    white_tee_rgba = white_tee_hd.convert('RGBA')

    # Composite portrait onto white t-shirt
    white_tee_rgba.paste(portrait_hd, (px, py), portrait_hd)

    # Final RGB output
    final_referral_shirt = white_tee_rgba.convert('RGB')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_referral_shirt.save(output_path, quality=95)
    final_referral_shirt.save('frontend/public/images/cbn_white_tshirt.jpg', quality=95)
    print(f"Referral mockup saved successfully to {output_path}")
    return output_path

if __name__ == "__main__":
    create_cbn_white_tshirt_mockup()
