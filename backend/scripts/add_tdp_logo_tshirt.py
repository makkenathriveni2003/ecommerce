import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.schemas.schemas import ProductData
from app.services.product_service import create_product
from app.db.session import SessionLocal
from app.models.models import Product

def add_tdp_product():
    db = SessionLocal()
    existing = db.query(Product).filter(Product.name == "TDP Logo T-Shirt").first()
    if existing:
        print(f"Product 'TDP Logo T-Shirt' already exists with ID: {existing.id}")
        return existing.to_dict()

    new_prod_data = ProductData(
        name="TDP Logo T-Shirt",
        price=499.0,
        category="Fashion",
        image="/images/tdp_logo_tshirt.jpg",
        description="Show your support with this premium TDP logo t-shirt. Made from soft, breathable cotton for all-day comfort. Perfect for rallies, events or casual wear. 100% Cotton (Bio Wash), High Quality Fade Resistant Digital Print, Regular Fit. Colors: Yellow, White, Black. Sizes: S, M, L, XL, XXL.",
        stock=50
    )
    
    created = create_product(new_prod_data)
    print(f"Successfully created product with ID: {created['id']}")
    return created

if __name__ == "__main__":
    add_tdp_product()
