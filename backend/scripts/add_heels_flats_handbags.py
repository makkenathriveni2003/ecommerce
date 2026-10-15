import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.db.database import database_connection

NEW_PRODUCTS = [
    # --- HEELS ---
    {
        "name": "Classic Pointed-Toe Stiletto Pump Heels",
        "price": 3499.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=500",
        "description": "Sleek pointed-toe high stiletto pump heels crafted from glossy patent vegan leather with 3.5-inch slender heel and cushioned memory foam insole for evening elegance.",
        "stock": 40,
    },
    {
        "name": "Ankle Strap Chunky Block Heel Sandals",
        "price": 2799.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1535043934128-cf0b28d52f95?w=500",
        "description": "Contemporary 2.5-inch block heel sandals featuring an adjustable buckle ankle strap, open toe silhouette, and stable non-slip rubber sole for all-day comfort.",
        "stock": 45,
    },
    {
        "name": "Chic Pointed Slingback Kitten Heels",
        "price": 2499.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1581101767113-1677fc2beaa8?w=500",
        "description": "Effortlessly sophisticated 1.75-inch low kitten heels with elasticated slingback strap and elongated pointed toe, designed for workwear and semi-formal outings.",
        "stock": 35,
    },
    {
        "name": "Strappy Braided Platform Wedge Heels",
        "price": 2999.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1562273138-f46be4ebdf33?w=500",
        "description": "Boho-chic espadrille platform wedge heels featuring intricately braided faux-leather straps, soft microfiber footbed, and 3-inch lightweight cork wedge.",
        "stock": 30,
    },

    # --- FLATS ---
    {
        "name": "Quilted Bow-Accent Cushioned Ballet Flats",
        "price": 1699.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=500",
        "description": "Timeless Parisian-style round-toe ballet flats with quilted stitch detailing, delicate front bow, and ultra-flexible slip-resistant sole for daily commuting.",
        "stock": 55,
    },
    {
        "name": "Pointed-Toe Slip-On Backless Mule Flats",
        "price": 1899.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1575537302964-96cd47c06b1b?w=500",
        "description": "Minimalist backless slide mule flats featuring a sharp pointed toe, smooth matte finish, and padded arch support for effortless slip-on sophistication.",
        "stock": 40,
    },
    {
        "name": "Braided T-Strap Summer Beach Flat Sandals",
        "price": 1299.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=500",
        "description": "Breezy summer flat sandals with artisanal braided T-strap, adjustable buckle closure, and cushioned ergonomic footbed built for relaxed weekend strolls.",
        "stock": 60,
    },
    {
        "name": "Tailored Horsebit Penny Loafer Flats",
        "price": 2199.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1595341888016-a392ef81b7de?w=500",
        "description": "Classic preppy loafer flats adorned with a polished golden horsebit metallic buckle, stitched apron toe, and shock-absorbing heel cushion.",
        "stock": 45,
    },

    # --- HANDBAGS ---
    {
        "name": "Signature Italian Vegan Leather Structured Tote Handbag",
        "price": 2899.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=500",
        "description": "Spacious everyday luxury tote handbag with dual rolled handles, zippered central divider, and protective metal bottom studs. Easily fits laptops up to 14 inches.",
        "stock": 40,
    },
    {
        "name": "Chic Quilted Chain-Strap Crossbody Flap Bag",
        "price": 2199.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500",
        "description": "Compact quilted flap bag with sliding gold-tone chain shoulder strap that transitions seamlessly from crossbody to double-shoulder carry.",
        "stock": 50,
    },
    {
        "name": "Minimalist Crescent Moon Shoulder Hobo Handbag",
        "price": 1999.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1591561954557-26941169b49e?w=500",
        "description": "Trending 90s-inspired crescent curved silhouette with smooth vegan leather, secure magnetic snap closure, and wide ergonomic shoulder strap.",
        "stock": 45,
    },
    {
        "name": "Classic Structured Top-Handle Satchel Handbag",
        "price": 2599.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1575032617751-6ddec2089882?w=500",
        "description": "Elegant dual-tone satchel bag featuring structured trapezoid silhouette, turn-lock front clasp, top carry handle, and detachable adjustable shoulder strap.",
        "stock": 35,
    },
]


def add_products():
    added_count = 0
    with database_connection() as conn:
        for pdata in NEW_PRODUCTS:
            exists = conn.execute(
                "SELECT id FROM products WHERE name = %s OR image = %s",
                (pdata["name"], pdata["image"]),
            ).fetchone()
            if not exists:
                conn.execute(
                    """
                    INSERT INTO products (name, price, category, image, description, stock)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        pdata["name"],
                        pdata["price"],
                        pdata["category"],
                        pdata["image"],
                        pdata["description"],
                        pdata["stock"],
                    ),
                )
                added_count += 1
                print(f"Added product: {pdata['name']} ({pdata['category']})")
            else:
                print(f"Product already exists: {pdata['name']}")

    print(f"\nSuccessfully added {added_count} new products into database!")

    # Re-index into ChromaDB vector store
    try:
        from backend.app.services.ai import CatalogIndexer, ChromaVectorStore
        store = ChromaVectorStore()
        indexer = CatalogIndexer(vector_store=store)
        count = indexer.reindex_all_products(clear_existing=False)
        print(f"Re-indexed {count} products in ChromaDB semantic vector store.")
    except Exception as ai_e:
        print(f"Semantic search indexing note: {ai_e}")

    # Invalidate Redis AI and products caches
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=0)
        for k in r.scan_iter("ai_cache:*"):
            r.delete(k)
        print("Cleared Redis AI search cache.")
    except Exception:
        pass


if __name__ == "__main__":
    add_products()
