import sys
sys.path.insert(0, "backend")
import re
from app.services.ai.vector_store import ChromaVectorStore
from app.services.product_service import get_products

vs = ChromaVectorStore()

CATEGORY_KEYWORDS = {
    "shoes": ["shoe", "footwear", "sneaker", "flat", "heel", "mule", "loafer", "sandal", "pumps"],
    "laptops": ["laptop", "computer", "macbook", "notebook", "pc"],
    "phones": ["phone", "mobile", "iphone", "smartphone"],
    "audio": ["headphone", "earbud", "audio", "airpod", "tws", "earphones"],
    "bags": ["bag", "tote", "handbag", "satchel", "backpack", "purse", "clutch", "hobo", "crossbody"],
    "jewellery": ["jewel", "earring", "necklace", "ring", "bracelet", "choker", "pendant"],
    "apparel": ["dress", "kurti", "shirt", "tee", "jean", "hoodie", "apparel", "top", "anarkali", "pant", "denim", "tank", "vest", "clothing"],
}

def detect_category_focus(text: str) -> list[str] | None:
    for cat_name, kw_list in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(k)}\b", text) or k in text for k in kw_list):
            return kw_list
    return None

def analyze_user_query(clean_query, category_filter=None):
    text = clean_query.strip().lower()
    clean_words = re.findall(r"\b[a-zA-Z0-9]+\b", text)
    greeting_words = {"hi", "hello", "hloo", "hlw", "hey", "heyy", "helo", "hii", "hiii", "good morning", "good afternoon", "good evening", "good day", "how are you", "who are you", "help", "test"}
    if text in greeting_words or (len(clean_words) <= 2 and any(text.startswith(g) for g in ["hi", "hello", "hloo", "hey", "helo"])):
        return {"type": "greeting", "msg": "Hello! Welcome to GenZ Zone..."}
    out_of_scope = ["pizza", "burger", "biryani", "food", "medicine", "car", "bike", "flight", "weather", "joke", "movie ticket"]
    if any(re.search(rf"\b{kw}\b", text) for kw in out_of_scope):
        return {"type": "out_of_scope", "msg": "Sorry, that item is not available in our GenZ Zone catalogue."}
        
    m_max = re.search(r"(?:under|below|less than|within|upto|up to|budget of|max(?:imum)?)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)", text)
    if not m_max:
        m_max = re.search(r"(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:lopu|varaku|under|below|budget|or less)", text)
    max_price = float(m_max.group(1).replace(",", "")) if m_max else None

    required_keywords = detect_category_focus(text)

    raw_docs = vs.query_similar(clean_query, top_k=25)
    
    # Filter candidates
    candidates = []
    
    def matches_item(p_name: str, p_cat: str, p_price: float) -> bool:
        if max_price is not None and p_price > max_price:
            return False
        if required_keywords:
            text_target = f"{p_name} {p_cat}".lower()
            if not any(k in text_target for k in required_keywords):
                return False
        return True

    for d in raw_docs:
        meta = d.get("metadata", {})
        p_name = str(meta.get("product_name", ""))
        p_cat = str(meta.get("category", ""))
        p_price = float(meta.get("price", 999999))
        if matches_item(p_name, p_cat, p_price):
            candidates.append(d)

    # If we need more items, augment directly from DB
    if len(candidates) < 4:
        db_prods = get_products(0, 100)
        for p in db_prods:
            p_price = float(p.get("price", 0))
            if matches_item(p["name"], p["category"], p_price):
                doc_id = f"prod_{p['id']}_chunk_0"
                if not any(c.get("id") == doc_id or c.get("metadata", {}).get("product_id") == p["id"] for c in candidates):
                    candidates.append({
                        "id": doc_id,
                        "metadata": {
                            "product_id": p["id"],
                            "product_name": p["name"],
                            "price": p_price,
                            "category": p["category"],
                            "stock": p.get("stock", 50),
                            "url": f"/products/{p['id']}",
                        }
                    })

    if max_price is not None and not candidates:
        return {"type": "no_results_price", "msg": f"We searched our catalogue, but currently do not have items in that category under ₹{int(max_price):,} in stock."}

    if not candidates:
        return {"type": "no_results", "msg": f"I searched our GenZ Zone catalogue, but could not find matching products for '{clean_query}'. That item is not available in our store."}

    return {"type": "product_search", "docs": [(d["metadata"]["product_name"], d["metadata"]["price"]) for d in candidates[:4]]}

print("1. hloo:", analyze_user_query("hloo"))
print("2. pizza:", analyze_user_query("do you have pizza"))
print("3. products under 2000:", analyze_user_query("any products under 2000"))
print("4. shoes under 2000:", analyze_user_query("shoes under 2000"))
print("5. laptops under 2000:", analyze_user_query("laptops under 2000"))
print("6. laptops in stock:", analyze_user_query("Show me laptops and computers in stock"))
