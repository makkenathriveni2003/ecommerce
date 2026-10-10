import os
import sys

backend_dir = r"c:\Users\Dell\Downloads\day9-fastapi\backend"
sys.path.insert(0, backend_dir)

from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import hash_password

def add_ntr_admin():
    db = SessionLocal()
    try:
        users_to_ensure = [
            {
                "name": "NTR (Admin)",
                "email": "ntr@shopzone.com",
                "role": "admin",
                "password": "ntr12345"
            },
            {
                "name": "N.T. Rama Rao Jr.",
                "email": "ntr@gmail.com",
                "role": "admin",
                "password": "ntr12345"
            }
        ]

        for u in users_to_ensure:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                existing.name = u["name"]
                existing.role = u["role"]
                existing.password_hash = hash_password(u["password"])
                print(f"Updated existing user: {u['email']} (role: {u['role']})")
            else:
                new_user = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"]
                )
                db.add(new_user)
                print(f"Created new user: {u['email']} (role: {u['role']})")
        
        db.commit()
        print("Successfully committed NTR admin users to the database.")
    except Exception as e:
        db.rollback()
        print(f"Error updating users: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_ntr_admin()
