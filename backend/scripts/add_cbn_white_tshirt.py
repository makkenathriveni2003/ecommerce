import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.schemas import ProductData
from app.services.product_service import create_product
from app.db.session import SessionLocal
from app.models.models import Product

def add_cbn_product():
    db = SessionLocal()
    existing = db.query(Product).filter(
        (Product.name == "Chandra Babu Printed White T-Shirt") |
        (Product.name == "Chandra Babu Naidu Printed White T-Shirt")
    ).first()
    if existing:
        print(f"Product already exists with ID: {existing.id} ({existing.name})")
        return existing.to_dict()

    new_prod_data = ProductData(
        name="Chandra Babu Printed White T-Shirt",
        price=599.0,
        category="Fashion",
        image="/images/cbn_front_hd.jpg",
        description="Premium white graphic T-shirt featuring a high-definition bold full-chest front print of visionary leader N. Chandrababu Naidu. Crafted from 100% bio-wash combed cotton for ultimate comfort and durability. Regular fit, fade-resistant digital screen print. Original Price: ₹999 (40% off). Colors: White. Sizes: S, M, L, XL, XXL.",
        stock=50
    )
    
    created = create_product(new_prod_data)
    print(f"Successfully created Chandra Babu product with ID: {created['id']}")
    return created

if __name__ == "__main__":
    add_cbn_product()
