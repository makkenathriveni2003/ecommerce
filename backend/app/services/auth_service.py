from typing import Any, Dict
from fastapi import HTTPException
from ..core.security import hash_password, verify_password, create_access_token
from ..db.database import database_connection, UniqueViolation


def register_user(name: str, email: str, password: str) -> Dict[str, Any]:
    email_clean = email.strip().lower()
    name_clean = name.strip()
    if not name_clean or "@" not in email_clean:
        raise HTTPException(
            status_code=422, detail="A valid name and email are required"
        )

    try:
        with database_connection() as connection:
            existing = connection.execute(
                "SELECT id FROM users WHERE email = %s",
                (email_clean,),
            ).fetchone()
            if existing is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Email already registered. Please sign in instead.",
                )

            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, 'shopper')
                """,
                (name_clean, email_clean, hash_password(password)),
            )
    except HTTPException:
        raise
    except UniqueViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Email already registered. Please sign in instead.",
        ) from error
    except Exception as error:
        if "unique" in str(error).lower() or "duplicate" in str(error).lower():
            raise HTTPException(
                status_code=409,
                detail="Email already registered. Please sign in instead.",
            ) from error
        raise

    return {"success": True, "message": "Registration successful"}


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    email_clean = email.strip().lower()
    if "@" not in email_clean:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    with database_connection() as connection:
        user = connection.execute(
            """
            SELECT id, name, email, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email_clean,),
        ).fetchone()

    if user is None or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["email"], role=user["role"])
    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }
