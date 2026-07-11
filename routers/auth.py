import secrets

from fastapi import APIRouter, HTTPException, Header, Depends

from models import (
    Athlete, User, UserRole,
    RegisterAthleteRequest, RegisterOrganizationRequest,
    LoginRequest, AuthResponse,
)
import storage

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(user_id: int) -> str:
    token = secrets.token_hex(16)
    storage.tokens_db[token] = user_id
    return token


def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = storage.tokens_db.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = storage.users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register/athlete", response_model=AuthResponse)
def register_athlete(body: RegisterAthleteRequest):
    if any(u.email == body.email for u in storage.users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    athlete = Athlete(
        id=storage.next_athlete_id(),
        name=body.name,
        category=body.category,
        height_cm=body.height_cm,
        arm_length_cm=body.arm_length_cm,
        functional_arms=body.functional_arms,
    )
    storage.athletes_db[athlete.id] = athlete

    user = User(
        id=storage.next_user_id(),
        email=body.email,
        password=body.password,
        role=UserRole.ATHLETE,
        athlete_id=athlete.id,
    )
    storage.users_db[user.id] = user

    token = _issue_token(user.id)
    return AuthResponse(token=token, user_id=user.id, role=user.role, athlete_id=athlete.id)


@router.post("/register/organization", response_model=AuthResponse)
def register_organization(body: RegisterOrganizationRequest):
    if any(u.email == body.email for u in storage.users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=storage.next_user_id(),
        email=body.email,
        password=body.password,
        role=UserRole.ORGANIZATION,
        org_name=body.org_name,
    )
    storage.users_db[user.id] = user

    token = _issue_token(user.id)
    return AuthResponse(token=token, user_id=user.id, role=user.role, org_name=body.org_name)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    user = next((u for u in storage.users_db.values() if u.email == body.email), None)
    if not user or user.password != body.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _issue_token(user.id)
    return AuthResponse(
        token=token,
        user_id=user.id,
        role=user.role,
        athlete_id=user.athlete_id,
        org_name=user.org_name,
    )


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)):
    return AuthResponse(
        token=None,
        user_id=current_user.id,
        role=current_user.role,
        athlete_id=current_user.athlete_id,
        org_name=current_user.org_name,
    )