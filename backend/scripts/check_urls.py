import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

with open("frontend/src/utils/productVariants.ts", "r", encoding="utf-8") as f:
    content = f.read()

urls = list(set(re.findall(r'https://images\.unsplash\.com/[^"\'\s`)]+', content)))
print(f"Total unique URLs to test: {len(urls)}")

dead_urls = []

def test_url(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                return (u, True, 200)
            return (u, False, resp.status)
    except urllib.error.HTTPError as e:
        return (u, False, e.code)
    except Exception as e:
        return (u, False, str(e))

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(test_url, u): u for u in urls}
    for f in as_completed(futures):
        u, ok, status = f.result()
        if not ok:
            print(f"DEAD [{status}]: {u}")
            dead_urls.append((u, status))
        else:
            # print(f"OK: {u}")
            pass

print(f"\n==========================================")
print(f"FINISHED! {len(dead_urls)} DEAD URLS FOUND:")
for u, status in dead_urls:
    print(f"[{status}] -> {u}")
print(f"==========================================")
