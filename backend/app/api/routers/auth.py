from typing import Any
from fastapi import APIRouter, Depends, Request
from ...core.config import settings
from ...core.rate_limit import limiter
from ...core.security import require_authenticated_user
from ...schemas.schemas import LoginData, RegisterData
from ...services.auth_service import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
@limiter.limit(settings.REGISTER_RATE_LIMIT)
def register(request: Request, data: RegisterData) -> dict[str, object]:
    return register_user(name=data.name, email=data.email, password=data.password)


@router.post("/login")
@limiter.limit(settings.LOGIN_RATE_LIMIT)
def login(request: Request, data: LoginData) -> dict[str, object]:
    return authenticate_user(email=data.email, password=data.password)


@router.get("/me")
def get_me(user: dict[str, Any] = Depends(require_authenticated_user)) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }
