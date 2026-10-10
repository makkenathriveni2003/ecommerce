import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.schemas import ProductData
from app.services.product_service import create_product, get_products
from app.db.session import SessionLocal
from app.models.models import Product

def add_devara_product():
    db = SessionLocal()
    existing = db.query(Product).filter(Product.name == "Devara shirts").first()
    if existing:
        print(f"Product 'Devara shirts' already exists with ID: {existing.id}")
        return existing.to_dict()

    new_prod_data = ProductData(
        name="Devara shirts",
        price=599.0,
        category="Fashion",
        image="/images/devara_white_tshirt.jpg",
        description="Premium white T-shirt featuring a bold Devara-inspired design. Comfortable fabric, stylish look, and perfect for movie fans and casual wear. Printed T-shirt with cinematic warrior print. Original Price: ₹999 (40% off). Sizes: S, M, L, XL, XXL. Color: White.",
        stock=25
    )
    
    created = create_product(new_prod_data)
    print(f"Successfully created product: {created}")
    return created

if __name__ == "__main__":
    add_devara_product()
