import re

content = open('frontend/src/utils/productVariants.ts', encoding='utf-8').read()
matches = re.findall(r'name:\s*"([^"]+)",\s*hex:\s*"([^"]+)",\s*baseImage:\s*"([^"]+)"', content)
print(f'Total presets: {len(matches)}')
for i, (name, hex_val, url) in enumerate(matches, 1):
    print(f'{i}. {name} | {hex_val} | {url}')
