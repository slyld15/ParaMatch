from fastapi import APIRouter, HTTPException
from models import Athlete, AthleteCreate, Match
import storage

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.post("", response_model=Athlete)
def create_athlete(body: AthleteCreate):
    athlete = Athlete(id=storage.next_athlete_id(), **body.model_dump())
    storage.athletes_db[athlete.id] = athlete
    return athlete


@router.get("", response_model=list[Athlete])
def list_athletes():
    return list(storage.athletes_db.values())


@router.get("/{athlete_id}", response_model=Athlete)
def get_athlete(athlete_id: int):
    athlete = storage.athletes_db.get(athlete_id)
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    return athlete


@router.get("/{athlete_id}/matches", response_model=list[Match])
def get_athlete_matches(athlete_id: int):
    if athlete_id not in storage.athletes_db:
        raise HTTPException(status_code=404, detail="Athlete not found")

    result = []
    for match in storage.matches_db.values():
        tournament = storage.tournaments_db.get(match.tournament_id)
        if not tournament or not tournament.published:
            continue
        if match.athlete_a_id == athlete_id or match.athlete_b_id == athlete_id:
            result.append(match)
    return result