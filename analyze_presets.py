import urllib.request
import re
from PIL import Image
import os

content = open('frontend/src/utils/productVariants.ts', encoding='utf-8').read()
matches = re.findall(r'name:\s*"([^"]+)",\s*hex:\s*"([^"]+)",\s*baseImage:\s*"([^"]+)"', content)

os.makedirs('scratch_presets', exist_ok=True)

for i, (name, hex_val, url) in enumerate(matches, 1):
    clean_url = url.split('?')[0] + '?w=100'
    filename = f'scratch_presets/preset_{i}.jpg'
    try:
        if not os.path.exists(filename):
            urllib.request.urlretrieve(clean_url, filename)
        img = Image.open(filename).convert('RGB')
        # get center crop
        w, h = img.size
        center = img.crop((w//4, h//4, 3*w//4, 3*h//4))
        pixels = list(center.getdata())
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)
        print(f'{i:2d}. {name:<26} (hex {hex_val}) -> RGB: ({avg_r:3d}, {avg_g:3d}, {avg_b:3d}) | {url}')
    except Exception as e:
        print(f'{i:2d}. {name:<26} ERROR: {e}')
