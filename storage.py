import secrets

from db import SessionLocal, AthleteRow, TournamentRow, MatchRow, UserRow, TokenRow
from models import Athlete, Tournament, Match, User, TournamentType, UserRole


def _athlete_from_row(row: AthleteRow) -> Athlete:
    return Athlete(
        id=row.id,
        name=row.name,
        category=row.category,
        height_cm=row.height_cm,
        arm_length_cm=row.arm_length_cm,
        functional_arms=row.functional_arms,
    )


def _tournament_from_row(row: TournamentRow) -> Tournament:
    ids = [int(x) for x in row.athlete_ids.split(",") if x]
    return Tournament(
        id=row.id,
        name=row.name,
        type=TournamentType(row.type),
        description=row.description,
        athlete_ids=ids,
        published=row.published,
        current_round=row.current_round,
    )


def _match_from_row(row: MatchRow) -> Match:
    return Match(
        id=row.id,
        tournament_id=row.tournament_id,
        round=row.round,
        athlete_a_id=row.athlete_a_id,
        athlete_b_id=row.athlete_b_id,
        ebae_score=row.ebae_score,
        court=row.court,
        date=row.date,
        winner_id=row.winner_id,
    )


def _user_from_row(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        password=row.password,
        role=UserRole(row.role),
        athlete_id=row.athlete_id,
        org_name=row.org_name,
    )


def create_athlete(name: str, category: str, height_cm: int, arm_length_cm: int, functional_arms: int) -> Athlete:
    db = SessionLocal()
    try:
        row = AthleteRow(
            name=name, category=category, height_cm=height_cm,
            arm_length_cm=arm_length_cm, functional_arms=functional_arms,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _athlete_from_row(row)
    finally:
        db.close()


def get_athlete(athlete_id: int) -> Athlete | None:
    db = SessionLocal()
    try:
        row = db.get(AthleteRow, athlete_id)
        return _athlete_from_row(row) if row else None
    finally:
        db.close()


def list_athletes() -> list[Athlete]:
    db = SessionLocal()
    try:
        rows = db.query(AthleteRow).all()
        return [_athlete_from_row(r) for r in rows]
    finally:
        db.close()


def create_tournament(name: str, type: TournamentType, description: str | None) -> Tournament:
    db = SessionLocal()
    try:
        row = TournamentRow(name=name, type=type.value, description=description, athlete_ids="", published=False, current_round=1)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _tournament_from_row(row)
    finally:
        db.close()


def get_tournament(tournament_id: int) -> Tournament | None:
    db = SessionLocal()
    try:
        row = db.get(TournamentRow, tournament_id)
        return _tournament_from_row(row) if row else None
    finally:
        db.close()


def list_tournaments() -> list[Tournament]:
    db = SessionLocal()
    try:
        rows = db.query(TournamentRow).all()
        return [_tournament_from_row(r) for r in rows]
    finally:
        db.close()


def set_tournament_athletes(tournament_id: int, athlete_ids: list[int]) -> Tournament | None:
    db = SessionLocal()
    try:
        row = db.get(TournamentRow, tournament_id)
        if not row:
            return None
        row.athlete_ids = ",".join(str(x) for x in athlete_ids)
        db.commit()
        db.refresh(row)
        return _tournament_from_row(row)
    finally:
        db.close()


def add_athlete_to_tournament(tournament_id: int, athlete_id: int) -> Tournament | None:
    db = SessionLocal()
    try:
        row = db.get(TournamentRow, tournament_id)
        if not row:
            return None
        ids = [int(x) for x in row.athlete_ids.split(",") if x]
        if athlete_id not in ids:
            ids.append(athlete_id)
        row.athlete_ids = ",".join(str(x) for x in ids)
        db.commit()
        db.refresh(row)
        return _tournament_from_row(row)
    finally:
        db.close()


def set_tournament_state(tournament_id: int, published: bool | None = None, current_round: int | None = None) -> Tournament | None:
    db = SessionLocal()
    try:
        row = db.get(TournamentRow, tournament_id)
        if not row:
            return None
        if published is not None:
            row.published = published
        if current_round is not None:
            row.current_round = current_round
        db.commit()
        db.refresh(row)
        return _tournament_from_row(row)
    finally:
        db.close()


def create_match(tournament_id: int, round: int, athlete_a_id: int, athlete_b_id: int | None,
                  ebae_score: int | None, court: int | None, date: str | None) -> Match:
    db = SessionLocal()
    try:
        row = MatchRow(
            tournament_id=tournament_id, round=round,
            athlete_a_id=athlete_a_id, athlete_b_id=athlete_b_id,
            ebae_score=ebae_score, court=court, date=date,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _match_from_row(row)
    finally:
        db.close()


def get_match(match_id: int) -> Match | None:
    db = SessionLocal()
    try:
        row = db.get(MatchRow, match_id)
        return _match_from_row(row) if row else None
    finally:
        db.close()


def get_matches_by_tournament(tournament_id: int) -> list[Match]:
    db = SessionLocal()
    try:
        rows = db.query(MatchRow).filter(MatchRow.tournament_id == tournament_id).all()
        return [_match_from_row(r) for r in rows]
    finally:
        db.close()


def get_matches_by_tournament_and_round(tournament_id: int, round: int) -> list[Match]:
    db = SessionLocal()
    try:
        rows = db.query(MatchRow).filter(MatchRow.tournament_id == tournament_id, MatchRow.round == round).all()
        return [_match_from_row(r) for r in rows]
    finally:
        db.close()


def delete_matches_by_tournament(tournament_id: int):
    db = SessionLocal()
    try:
        db.query(MatchRow).filter(MatchRow.tournament_id == tournament_id).delete()
        db.commit()
    finally:
        db.close()


def set_match_winner(match_id: int, winner_id: int) -> Match | None:
    db = SessionLocal()
    try:
        row = db.get(MatchRow, match_id)
        if not row:
            return None
        row.winner_id = winner_id
        db.commit()
        db.refresh(row)
        return _match_from_row(row)
    finally:
        db.close()


def get_published_matches_by_athlete(athlete_id: int) -> list[Match]:
    db = SessionLocal()
    try:
        rows = (
            db.query(MatchRow)
            .join(TournamentRow, MatchRow.tournament_id == TournamentRow.id)
            .filter(TournamentRow.published == True)
            .filter((MatchRow.athlete_a_id == athlete_id) | (MatchRow.athlete_b_id == athlete_id))
            .all()
        )
        return [_match_from_row(r) for r in rows]
    finally:
        db.close()


def create_user(email: str, password: str, role: UserRole, athlete_id: int | None = None, org_name: str | None = None) -> User:
    db = SessionLocal()
    try:
        row = UserRow(email=email, password=password, role=role.value, athlete_id=athlete_id, org_name=org_name)
        db.add(row)
        db.commit()
        db.refresh(row)
        return _user_from_row(row)
    finally:
        db.close()


def get_user_by_email(email: str) -> User | None:
    db = SessionLocal()
    try:
        row = db.query(UserRow).filter(UserRow.email == email).first()
        return _user_from_row(row) if row else None
    finally:
        db.close()


def get_user(user_id: int) -> User | None:
    db = SessionLocal()
    try:
        row = db.get(UserRow, user_id)
        return _user_from_row(row) if row else None
    finally:
        db.close()


def email_exists(email: str) -> bool:
    return get_user_by_email(email) is not None


def issue_token(user_id: int) -> str:
    token = secrets.token_hex(16)
    db = SessionLocal()
    try:
        db.add(TokenRow(token=token, user_id=user_id))
        db.commit()
        return token
    finally:
        db.close()


def get_user_id_by_token(token: str) -> int | None:
    db = SessionLocal()
    try:
        row = db.get(TokenRow, token)
        return row.user_id if row else None
    finally:
        db.close()
