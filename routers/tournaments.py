from fastapi import APIRouter, HTTPException
from models import (
    Tournament, TournamentCreate, TournamentType,
    AddAthletesRequest, Match, MatchResult,
)
from matching import generate_fair_pairs, pad_to_power_of_two, generate_next_round
import storage

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

COURTS = [1, 2, 3, 4]


def _assign_court(index: int) -> int:
    return COURTS[index % len(COURTS)]


def _save_pairs_as_matches(tournament_id: int, round_no: int, pairs: list[dict]) -> list[Match]:
    saved = []
    for i, p in enumerate(pairs):
        match = Match(
            id=storage.next_match_id(),
            tournament_id=tournament_id,
            round=round_no,
            athlete_a_id=p["a"].id,
            athlete_b_id=p["b"].id if p["b"] else None,
            ebae_score=p["score"],
            court=_assign_court(i) if p["b"] else None,
            date="Tomorrow 2:00 PM" if p["b"] else None,
        )
        storage.matches_db[match.id] = match
        saved.append(match)
    return saved


@router.post("", response_model=Tournament)
def create_tournament(body: TournamentCreate):
    tournament = Tournament(id=storage.next_tournament_id(), **body.model_dump())
    storage.tournaments_db[tournament.id] = tournament
    return tournament


@router.get("", response_model=list[Tournament])
def list_tournaments():
    return list(storage.tournaments_db.values())


@router.get("/{tournament_id}", response_model=Tournament)
def get_tournament(tournament_id: int):
    t = storage.tournaments_db.get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return t


@router.get("/{tournament_id}/matches", response_model=list[Match])
def get_tournament_matches(tournament_id: int):
    return [m for m in storage.matches_db.values() if m.tournament_id == tournament_id]


@router.post("/{tournament_id}/athletes", response_model=Tournament)
def add_athletes(tournament_id: int, body: AddAthletesRequest):
    t = storage.tournaments_db.get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    for aid in body.athlete_ids:
        if aid not in storage.athletes_db:
            raise HTTPException(status_code=400, detail=f"Athlete {aid} does not exist")
    t.athlete_ids = body.athlete_ids
    return t


@router.post("/{tournament_id}/generate-matches", response_model=list[Match])
def generate_matches(tournament_id: int):
    t = storage.tournaments_db.get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if len(t.athlete_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 athletes must be selected")

    chosen = [storage.athletes_db[aid] for aid in t.athlete_ids]

    if t.type == TournamentType.OPEN:
        pairs = generate_fair_pairs(chosen)
    else:
        padded = pad_to_power_of_two(chosen)
        real_athletes = [a for a in padded if a is not None]
        bay_count = len(padded) - len(real_athletes)
        pairs = generate_fair_pairs(real_athletes)
        for _ in range(bay_count):
            pairs.append({"a": pairs.pop()["a"], "b": None, "score": None}) if pairs else None

    t.current_round = 1
    t.published = False
    for mid in [m.id for m in storage.matches_db.values() if m.tournament_id == tournament_id]:
        del storage.matches_db[mid]

    return _save_pairs_as_matches(tournament_id, round_no=1, pairs=pairs)


@router.post("/{tournament_id}/publish", response_model=Tournament)
def publish(tournament_id: int):
    t = storage.tournaments_db.get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    t.published = True
    return t


@router.post("/{tournament_id}/matches/{match_id}/result", response_model=Match)
def submit_result(tournament_id: int, match_id: int, body: MatchResult):
    t = storage.tournaments_db.get(tournament_id)
    match = storage.matches_db.get(match_id)
    if not t or not match or match.tournament_id != tournament_id:
        raise HTTPException(status_code=404, detail="Tournament or match not found")
    if t.type != TournamentType.OLYMPIC:
        raise HTTPException(status_code=400, detail="Submitting results is only valid for OLYMPIC tournaments")
    if body.winner_id not in (match.athlete_a_id, match.athlete_b_id):
        raise HTTPException(status_code=400, detail="Winner must be one of the athletes in this match")

    match.winner_id = body.winner_id

    current_round_matches = [
        m for m in storage.matches_db.values()
        if m.tournament_id == tournament_id and m.round == t.current_round
    ]
    all_decided = all(m.winner_id is not None or m.athlete_b_id is None for m in current_round_matches)

    if all_decided and len(current_round_matches) > 1:
        winners = []
        for m in current_round_matches:
            winner_id = m.winner_id if m.athlete_b_id else m.athlete_a_id
            winners.append(storage.athletes_db[winner_id])
        next_pairs = generate_next_round(winners)
        t.current_round += 1
        _save_pairs_as_matches(tournament_id, round_no=t.current_round, pairs=next_pairs)

    return match