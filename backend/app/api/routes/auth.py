import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import CurrentUser, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.user import UserRole
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_token(user: User) -> str:
    return create_access_token({
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "name": user.name,
    })


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    existing = await User.find_one(User.email == payload.email.lower())
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password=hash_password(payload.password),
        role=payload.role,
    )
    await user.insert()

    token = _issue_token(user)
    return AuthResponse(
        message="Registration successful",
        token=token,
        user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role),
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user = await User.find_one(User.email == payload.email.lower())
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _issue_token(user)
    return AuthResponse(
        token=token,
        user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role),
    )


@router.post("/supabase", response_model=AuthResponse)
async def supabase_login(payload: dict):
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing Supabase access token")

    async with httpx.AsyncClient(base_url=settings.supabase_url) as client:
        response = await client.get(
            "/auth/v1/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "apikey": settings.supabase_anon_key,
            },
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase session")

    supabase_user = response.json()
    email = (supabase_user.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Supabase user has no email")

    user = await User.find_one(User.email == email)
    full_name = supabase_user.get("user_metadata", {}).get("full_name") or supabase_user.get("email", "Google User")
    if user:
        if full_name and user.name != full_name:
            user.name = full_name
            await user.save()
    else:
        user = User(
            name=full_name,
            email=email,
            password="",
            role=UserRole.buyer,
        )
        await user.insert()

    token = _issue_token(user)
    return AuthResponse(
        token=token,
        user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role),
    )


@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)):
    user = await User.get(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "user": UserOut(id=user.id, name=user.name, email=user.email, role=user.role),
    }
