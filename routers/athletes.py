from fastapi import APIRouter, HTTPException
from models import Athlete, AthleteCreate, Match
import storage

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.post("", response_model=Athlete)
def create_athlete(body: AthleteCreate):
    return storage.create_athlete(
        name=body.name,
        category=body.category,
        height_cm=body.height_cm,
        arm_length_cm=body.arm_length_cm,
        functional_arms=body.functional_arms,
    )


@router.get("", response_model=list[Athlete])
def list_athletes():
    return storage.list_athletes()


@router.get("/{athlete_id}", response_model=Athlete)
def get_athlete(athlete_id: int):
    athlete = storage.get_athlete(athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


@router.get("/{athlete_id}/matches", response_model=list[Match])
def get_athlete_matches(athlete_id: int):
    if not storage.get_athlete(athlete_id):
        raise HTTPException(status_code=404, detail="Athlete not found")
    return storage.get_published_matches_by_athlete(athlete_id)
