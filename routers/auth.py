from fastapi import APIRouter, HTTPException, Header, Depends

from models import (
    User, UserRole,
    RegisterAthleteRequest, RegisterOrganizationRequest,
    LoginRequest, AuthResponse,
)
import storage

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = storage.get_user_id_by_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register/athlete", response_model=AuthResponse)
def register_athlete(body: RegisterAthleteRequest):
    if storage.email_exists(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    athlete = storage.create_athlete(
        name=body.name,
        category=body.category,
        height_cm=body.height_cm,
        arm_length_cm=body.arm_length_cm,
        functional_arms=body.functional_arms,
    )

    user = storage.create_user(
        email=body.email,
        password=body.password,
        role=UserRole.ATHLETE,
        athlete_id=athlete.id,
    )

    token = storage.issue_token(user.id)
    return AuthResponse(token=token, user_id=user.id, role=user.role, athlete_id=athlete.id)


@router.post("/register/organization", response_model=AuthResponse)
def register_organization(body: RegisterOrganizationRequest):
    if storage.email_exists(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = storage.create_user(
        email=body.email,
        password=body.password,
        role=UserRole.ORGANIZATION,
        org_name=body.org_name,
    )

    token = storage.issue_token(user.id)
    return AuthResponse(token=token, user_id=user.id, role=user.role, org_name=body.org_name)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    user = storage.get_user_by_email(body.email)
    if not user or user.password != body.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = storage.issue_token(user.id)
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
