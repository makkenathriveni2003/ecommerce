import sys
sys.path.insert(0, ".")
from backend.app.db.database import database_connection

updates = [
    (123, "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600", "Athletic heather grey sleeveless training hoodie featuring drawstring hood, front kangaroo pouch, and drop armholes for unconstrained range of motion."),
    (124, "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600", "Breezy terracotta rust relaxed linen tank top engineered for summer airflow with dropped shoulder cut."),
    (127, "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600", "MicroModal ultra-soft white lounge undershirt with silk-smooth second-skin feel and anti-chafing flatlock seams.")
]

with database_connection() as conn:
    with conn.cursor() as cur:
        for pid, img, desc in updates:
            cur.execute("UPDATE products SET image = %s, description = %s WHERE id = %s", (img, desc, pid))
            print(f"Updated product ID {pid} successfully.")
    conn.commit()

print("Database clothing update complete!")
