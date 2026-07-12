from fastapi import APIRouter, HTTPException, Depends
from models import (
    Tournament, TournamentCreate, TournamentType,
    AddAthletesRequest, Match, MatchResult, User, UserRole,
)
from matching import generate_fair_pairs, pad_to_power_of_two, generate_next_round
from routers.auth import get_current_user
import storage

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

COURTS = [1, 2, 3, 4]


def _assign_court(index: int) -> int:
    return COURTS[index % len(COURTS)]


def _save_pairs_as_matches(tournament_id: int, round_no: int, pairs: list[dict]) -> list[Match]:
    saved = []
    for i, p in enumerate(pairs):
        match = storage.create_match(
            tournament_id=tournament_id,
            round=round_no,
            athlete_a_id=p["a"].id,
            athlete_b_id=p["b"].id if p["b"] else None,
            ebae_score=p["score"],
            court=_assign_court(i) if p["b"] else None,
            date="Tomorrow 2:00 PM" if p["b"] else None,
        )
        saved.append(match)
    return saved


@router.post("", response_model=Tournament)
def create_tournament(body: TournamentCreate):
    return storage.create_tournament(name=body.name, type=body.type, description=body.description)


@router.get("", response_model=list[Tournament])
def list_tournaments():
    return storage.list_tournaments()


@router.get("/{tournament_id}", response_model=Tournament)
def get_tournament(tournament_id: int):
    t = storage.get_tournament(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return t


@router.get("/{tournament_id}/matches", response_model=list[Match])
def get_tournament_matches(tournament_id: int):
    return storage.get_matches_by_tournament(tournament_id)


@router.post("/{tournament_id}/athletes", response_model=Tournament)
def add_athletes(tournament_id: int, body: AddAthletesRequest):
    if not storage.get_tournament(tournament_id):
        raise HTTPException(status_code=404, detail="Tournament not found")
    for aid in body.athlete_ids:
        if not storage.get_athlete(aid):
            raise HTTPException(status_code=400, detail=f"Athlete {aid} does not exist")
    return storage.set_tournament_athletes(tournament_id, body.athlete_ids)


@router.post("/{tournament_id}/join", response_model=Tournament)
def join_tournament(tournament_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ATHLETE or not current_user.athlete_id:
        raise HTTPException(status_code=403, detail="Only athletes can join tournaments")

    t = storage.get_tournament(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if t.type != TournamentType.OPEN:
        raise HTTPException(status_code=400, detail="Only OPEN tournaments can be joined directly")
    if t.published:
        raise HTTPException(status_code=400, detail="This tournament has already been published")
    if current_user.athlete_id in t.athlete_ids:
        raise HTTPException(status_code=400, detail="You already joined this tournament")

    return storage.add_athlete_to_tournament(tournament_id, current_user.athlete_id)


@router.post("/{tournament_id}/generate-matches", response_model=list[Match])
def generate_matches(tournament_id: int):
    t = storage.get_tournament(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if len(t.athlete_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 athletes must be selected")

    chosen = [storage.get_athlete(aid) for aid in t.athlete_ids]

    if t.type == TournamentType.OPEN:
        pairs = generate_fair_pairs(chosen)
    else:
        padded = pad_to_power_of_two(chosen)
        real_athletes = [a for a in padded if a is not None]
        bay_count = len(padded) - len(real_athletes)
        pairs = generate_fair_pairs(real_athletes)
        for _ in range(bay_count):
            pairs.append({"a": pairs.pop()["a"], "b": None, "score": None}) if pairs else None

    storage.set_tournament_state(tournament_id, published=False, current_round=1)
    storage.delete_matches_by_tournament(tournament_id)

    return _save_pairs_as_matches(tournament_id, round_no=1, pairs=pairs)


@router.post("/{tournament_id}/publish", response_model=Tournament)
def publish(tournament_id: int):
    t = storage.set_tournament_state(tournament_id, published=True)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return t


@router.post("/{tournament_id}/matches/{match_id}/result", response_model=Match)
def submit_result(tournament_id: int, match_id: int, body: MatchResult):
    t = storage.get_tournament(tournament_id)
    match = storage.get_match(match_id)
    if not t or not match or match.tournament_id != tournament_id:
        raise HTTPException(status_code=404, detail="Tournament or match not found")
    if t.type != TournamentType.INVITATIONAL:
        raise HTTPException(status_code=400, detail="Submitting results is only valid for INVITATIONAL tournaments")
    if body.winner_id not in (match.athlete_a_id, match.athlete_b_id):
        raise HTTPException(status_code=400, detail="Winner must be one of the athletes in this match")

    match = storage.set_match_winner(match_id, body.winner_id)

    current_round_matches = storage.get_matches_by_tournament_and_round(tournament_id, t.current_round)
    all_decided = all(m.winner_id is not None or m.athlete_b_id is None for m in current_round_matches)

    if all_decided and len(current_round_matches) > 1:
        winners = []
        for m in current_round_matches:
            winner_id = m.winner_id if m.athlete_b_id else m.athlete_a_id
            winners.append(storage.get_athlete(winner_id))
        next_pairs = generate_next_round(winners)
        next_round = t.current_round + 1
        storage.set_tournament_state(tournament_id, current_round=next_round)
        _save_pairs_as_matches(tournament_id, round_no=next_round, pairs=next_pairs)

    return match
