from pydantic import BaseModel
from typing import Optional
from enum import Enum


class TournamentType(str, Enum):
    OPEN = "OPEN"
    INVITATIONAL = "INVITATIONAL"


class UserRole(str, Enum):
    ATHLETE = "ATHLETE"
    ORGANIZATION = "ORGANIZATION"


class Athlete(BaseModel):
    id: int
    name: str
    category: str
    height_cm: int
    arm_length_cm: int
    functional_arms: int


class AthleteCreate(BaseModel):
    name: str
    category: str
    height_cm: int
    arm_length_cm: int
    functional_arms: int


class Tournament(BaseModel):
    id: int
    name: str
    type: TournamentType
    description: Optional[str] = None
    athlete_ids: list[int] = []
    published: bool = False
    current_round: int = 1


class TournamentCreate(BaseModel):
    name: str
    type: TournamentType
    description: Optional[str] = None


class AddAthletesRequest(BaseModel):
    athlete_ids: list[int]


class Match(BaseModel):
    id: int
    tournament_id: int
    round: int
    athlete_a_id: int
    athlete_b_id: Optional[int] = None
    ebae_score: Optional[int] = None
    court: Optional[int] = None
    date: Optional[str] = None
    winner_id: Optional[int] = None


class MatchResult(BaseModel):
    winner_id: int


class User(BaseModel):
    id: int
    email: str
    password: str
    role: UserRole
    athlete_id: Optional[int] = None
    org_name: Optional[str] = None


class RegisterAthleteRequest(BaseModel):
    email: str
    password: str
    name: str
    category: str
    height_cm: int
    arm_length_cm: int
    functional_arms: int


class RegisterOrganizationRequest(BaseModel):
    email: str
    password: str
    org_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: Optional[str] = None
    user_id: int
    role: UserRole
    athlete_id: Optional[int] = None
    org_name: Optional[str] = None
