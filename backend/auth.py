"""
Backward-compatibility adapter for auth module.
Re-exports from app.core.security.
"""
from app.core.security import (
    create_access_token,
    read_access_token,
    hash_password,
    verify_password,
    validate_token_configuration,
    require_authenticated_user,
    require_admin,
    verify_object_ownership,
)

__all__ = [
    "create_access_token",
    "read_access_token",
    "hash_password",
    "verify_password",
    "validate_token_configuration",
    "require_authenticated_user",
    "require_admin",
    "verify_object_ownership",
]
