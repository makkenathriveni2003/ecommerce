from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from ..db.database import database_connection


def get_chat_history(user: dict[str, Any], customer: str | None = None) -> List[Dict[str, Any]]:
    with database_connection() as connection:
        if user["role"] == "admin":
            if customer and customer.strip():
                c_email = customer.strip().lower()
                rows = connection.execute(
                    """
                    SELECT id, sender_email, sender_name, sender_role,
                           recipient_email, message, created_at
                    FROM chat_messages
                    WHERE (sender_email = %s)
                       OR (recipient_email = %s)
                    ORDER BY created_at ASC
                    LIMIT 200
                    """,
                    (c_email, c_email),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, sender_email, sender_name, sender_role,
                           recipient_email, message, created_at
                    FROM chat_messages
                    ORDER BY created_at ASC
                    LIMIT 200
                    """
                ).fetchall()
        else:
            u_email = user["email"].strip().lower()
            rows = connection.execute(
                """
                SELECT id, sender_email, sender_name, sender_role,
                       recipient_email, message, created_at
                FROM chat_messages
                WHERE sender_email = %s OR recipient_email = %s
                ORDER BY created_at ASC
                LIMIT 200
                """,
                (u_email, u_email),
            ).fetchall()

    return [
        {
            "id": row["id"],
            "sender_email": row["sender_email"],
            "sender_name": row["sender_name"],
            "sender_role": row["sender_role"],
            "recipient_email": row["recipient_email"],
            "text": row["message"],
            "created_at": str(row["created_at"]),
        }
        for row in rows
    ]


def save_chat_message(user: dict[str, Any], recipient_email: str, text: str) -> Dict[str, Any]:
    text_clean = text.strip()
    if not text_clean:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    recipient = recipient_email.strip().lower()
    if user["role"] != "admin":
        recipient = "admin"

    with database_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO chat_messages (
                sender_email, sender_name, sender_role, recipient_email, message
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (user["email"], user["name"], user["role"], recipient, text_clean),
        ).fetchone()

    msg_id = row["id"] if row else 0
    created_at = str(row["created_at"]) if row else datetime.now(timezone.utc).isoformat()
    return {
        "id": msg_id,
        "sender_email": user["email"],
        "sender_name": user["name"],
        "sender_role": user["role"],
        "recipient_email": recipient,
        "text": text_clean,
        "created_at": created_at,
    }
