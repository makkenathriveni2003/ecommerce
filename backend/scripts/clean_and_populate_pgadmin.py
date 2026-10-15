"""
Database cleanup and catalogue enhancement script for Chow Zoon E-Commerce.
Removes legacy demo users (CBN/NTR) and political merchandise,
creates official Chow Zoon accounts, and populates PostgreSQL with
Amazon-grade e-commerce products with realistic pricing, stock, categories,
and rich descriptions. Re-indexes the ChromaDB vector store.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.database import database_connection
from app.core.security import hash_password
from app.services.ai import CatalogIndexer, ChromaVectorStore

ENHANCED_PRODUCTS = [
    {
        "name": "Apple MacBook Pro M3 (16GB, 512GB SSD)",
        "price": 169900.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500",
        "description": "Blazing fast M3 chip with 8-core CPU and 10-core GPU. Liquid Retina XDR 14-inch display, up to 22 hours battery life, 1080p FaceTime HD camera, and studio-quality 3-mic array. Limited-time 15% discount.",
        "stock": 20,
    },
    {
        "name": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
        "price": 28990.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",
        "description": "Industry-leading active noise cancellation with 8 microphones and Auto NC Optimizer. High-resolution audio, crystal-clear hands-free calling, up to 30 hours battery life with quick charge. Deal of the day.",
        "stock": 40,
    },
    {
        "name": "Apple iPhone 15 Pro (128GB, Natural Titanium)",
        "price": 129900.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500",
        "description": "Forged in titanium with aerospace-grade strength. A17 Pro gaming chip, groundbreaking 48MP camera system with 3x optical zoom, and programmable Action button.",
        "stock": 25,
    },
    {
        "name": "Samsung Galaxy Watch 6 Bluetooth Smartwatch",
        "price": 19999.0,
        "category": "Accessories",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500",
        "description": "Advanced sleep coaching, body composition ECG analysis, sapphire crystal glass, personalized heart rate zones, and fast wireless charging.",
        "stock": 50,
    },
    {
        "name": "Mechanical RGB Gaming Keyboard (Cherry MX Red)",
        "price": 4499.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500",
        "description": "Aircraft-grade aluminum frame, per-key RGB backlighting, 100% anti-ghosting N-key rollover, dedicated media volume roller, and detachable magnetic wrist rest.",
        "stock": 35,
    },
    {
        "name": "Ergonomic Vertical Wireless Mouse",
        "price": 1799.0,
        "category": "Accessories",
        "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500",
        "description": "Promotes neutral wrist and arm postures for smooth movement and less strain. 4000 DPI high-precision sensor with whisper-quiet clicks.",
        "stock": 65,
    },
    {
        "name": "Ultra-Wide 34-Inch Curved 144Hz Monitor",
        "price": 32999.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500",
        "description": "Immersive 1500R curvature with WQHD resolution (3440 x 1440). AMD FreeSync Premium, 1ms MPRT, HDR10, dual HDMI and DisplayPort connectivity.",
        "stock": 15,
    },
    {
        "name": "Noise Cancelling True Wireless Earbuds",
        "price": 6999.0,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500",
        "description": "Active hybrid noise cancellation with transparency pass-through mode. IPX5 water resistance, deep bass dynamic drivers, and 36-hour combined case playback.",
        "stock": 55,
    },
    {
        "name": "Classic Cotton Oxford Button-Down Shirt",
        "price": 1499.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=500",
        "description": "Pure 100% combed cotton oxford weave with tailored regular fit. Features wrinkle-resistant finish, buttoned cuffs, and chest pocket. Perfect for formal and casual styling.",
        "stock": 50,
    },
    {
        "name": "Vintage Washed Denim Jacket",
        "price": 2499.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=500",
        "description": "Classic mid-blue wash denim outerwear with copper shank buttons, twin welt pockets, and adjustable waist tabs. Durable heavy-twill denim.",
        "stock": 40,
    },
    {
        "name": "Premium Graphic Crewneck Streetwear Tee",
        "price": 799.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500",
        "description": "240 GSM heavyweight bio-washed cotton oversize t-shirt. High-density graphic chest print that resists fading through 50+ wash cycles.",
        "stock": 70,
    },
    {
        "name": "Women's Floral Summer A-Line Dress",
        "price": 1999.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500",
        "description": "Breezy chiffon floral print dress with sweetheart neckline, smocked bodice, and flutter sleeves. Perfect for daytime brunch or resort vacation wear.",
        "stock": 45,
    },
    {
        "name": "Tailored Slim Fit Denim Jeans",
        "price": 1799.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500",
        "description": "Stretch denim in midnight indigo rinse. 5-pocket styling with reinforced bar-tacks and branded rivet details.",
        "stock": 60,
    },
    {
        "name": "Traditional Embroidered Festive Kurti",
        "price": 1499.0,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500",
        "description": "Intricate zari threadwork on soft rayon blend fabric. Mandarin collar with three-quarter sleeves, designed for festive celebrations and gatherings.",
        "stock": 35,
    },
    {
        "name": "22K Gold Plated Royal Necklace Set",
        "price": 2499.0,
        "category": "Jewellery",
        "image": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=500",
        "description": "Handcrafted temple-inspired choker necklace with matching drop jhumka earrings. Anti-tarnish micron gold plating with sparkling cubic zirconia accents.",
        "stock": 25,
    },
    {
        "name": "Sparkling Crystal Teardrop Earrings",
        "price": 999.0,
        "category": "Jewellery",
        "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=500",
        "description": "Faceted Austrian crystals mounted on hypoallergenic sterling silver posts. Shimmers brilliantly under ambient light.",
        "stock": 50,
    },
    {
        "name": "Layered Minimalist Chain Bracelet",
        "price": 799.0,
        "category": "Jewellery",
        "image": "https://images.unsplash.com/photo-1611652022419-a9419f74343d?w=500",
        "description": "Double chain design with adjustable lobster claw clasp. Rose gold plated brass that resists tarnishing with daily wear.",
        "stock": 45,
    },
    {
        "name": "Solitaire Crystal Accent Fashion Ring",
        "price": 699.0,
        "category": "Jewellery",
        "image": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=500",
        "description": "Classic solitaire round cut stone in a 4-prong setting with comfort-fit band. Elegant statement piece for any occasion.",
        "stock": 60,
    },
    {
        "name": "Pro Cushion Performance Running Shoes",
        "price": 2499.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500",
        "description": "Responsive nitrogen-infused EVA midsole with breathable engineered mesh upper. High-traction rubber outsole ideal for marathon training and daily jogs.",
        "stock": 40,
    },
    {
        "name": "All-Day Comfort Lifestyle Sneakers",
        "price": 2199.0,
        "category": "Shoes",
        "image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500",
        "description": "Low-top retro silhouette with padded collar, memory foam footbed, and vulcanized rubber sole for effortless city walking.",
        "stock": 50,
    },
    {
        "name": "Structured Vegan Leather Tote Handbag",
        "price": 1899.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500",
        "description": "Roomy interior compartment accommodating up to a 13-inch laptop. Premium gold hardware, zippered security pocket, and detachable crossbody strap.",
        "stock": 35,
    },
    {
        "name": "Water-Resistant Commuter Laptop Backpack (30L)",
        "price": 1599.0,
        "category": "Bags",
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500",
        "description": "Ergonomic padded shoulder straps, dedicated padded 15.6-inch laptop sleeve, external USB charging passthrough port, and luggage strap.",
        "stock": 55,
    },
]

def main():
    print("Connecting to database...")
    with database_connection() as conn:
        # 1. Clean up CBN and NTR users from PostgreSQL
        print("Cleaning up legacy users...")
        conn.execute(
            """
            DELETE FROM users
            WHERE email IN ('cbn@shopzone.com', 'cbn@gmail.com', 'ntr@shopzone.com', 'ntr@gmail.com')
               OR LOWER(name) LIKE '%chandra%'
               OR LOWER(name) LIKE '%ntr%'
            """
        )

        # 2. Ensure Chow Zoon Administrator exists
        admin = conn.execute("SELECT id FROM users WHERE email = 'admin@chowzoon.com'").fetchone()
        if not admin:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                ("Chow Zoon Administrator", "admin@chowzoon.com", hash_password("adminpassword123"), "admin"),
            )
            print("Created Chow Zoon Administrator: admin@chowzoon.com / adminpassword123")
        else:
            conn.execute(
                """
                UPDATE users SET name = 'Chow Zoon Administrator', password_hash = %s, role = 'admin'
                WHERE email = 'admin@chowzoon.com'
                """,
                (hash_password("adminpassword123"),),
            )
            print("Updated Chow Zoon Administrator")

        # 3. Ensure Chow Zoon Valued Customer exists
        customer = conn.execute("SELECT id FROM users WHERE email = 'customer@chowzoon.com'").fetchone()
        if not customer:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                ("Valued Customer", "customer@chowzoon.com", hash_password("customer12345"), "shopper"),
            )
            print("Created Customer: customer@chowzoon.com / customer12345")
        else:
            conn.execute(
                """
                UPDATE users SET name = 'Valued Customer', password_hash = %s, role = 'shopper'
                WHERE email = 'customer@chowzoon.com'
                """,
                (hash_password("customer12345"),),
            )
            print("Updated Chow Zoon Customer")

        # 4. Remove political / legacy items from products table
        print("Cleaning up political merchandise...")
        # First check order items references
        conn.execute(
            """
            DELETE FROM products
            WHERE id NOT IN (SELECT DISTINCT product_id FROM order_items)
              AND (
                LOWER(name) LIKE '%tdp%'
                OR LOWER(name) LIKE '%chandra%'
                OR LOWER(name) LIKE '%devara%'
                OR LOWER(name) LIKE '%visionary leader%'
              )
            """
        )
        # If any remained due to order items, update their names & descriptions to general products
        conn.execute(
            """
            UPDATE products
            SET name = 'Classic Cotton Graphic T-Shirt',
                description = 'Premium soft combed cotton casual t-shirt with durable print and comfortable regular fit.',
                category = 'Fashion',
                price = 599.0,
                image = 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500'
            WHERE LOWER(name) LIKE '%tdp%'
               OR LOWER(name) LIKE '%chandra%'
               OR LOWER(name) LIKE '%devara%'
               OR LOWER(name) LIKE '%visionary leader%'
            """
        )

        # 5. Insert / Update enhanced Amazon-grade products into PostgreSQL
        print("Populating high-quality e-commerce products...")
        for p in ENHANCED_PRODUCTS:
            existing = conn.execute(
                "SELECT id FROM products WHERE LOWER(name) = LOWER(%s)",
                (p["name"],),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE products
                    SET price = %s, category = %s, image = %s, description = %s, stock = %s
                    WHERE id = %s
                    """,
                    (p["price"], p["category"], p["image"], p["description"], p["stock"], existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO products (name, price, category, image, description, stock)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (p["name"], p["price"], p["category"], p["image"], p["description"], p["stock"]),
                )

        print("Database products updated successfully.")

    # 6. Re-index ChromaDB Vector Store
    print("Re-indexing ChromaDB vector store...")
    store = ChromaVectorStore()
    indexer = CatalogIndexer(vector_store=store)
    result = indexer.reindex_all_products(clear_existing=True)
    print(f"ChromaDB reindexing complete: {result['products_indexed']} products indexed, {result['chunks_indexed']} chunks created.")
    print("All tasks finished successfully.")

if __name__ == "__main__":
    main()
