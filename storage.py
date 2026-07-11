from models import Athlete, Tournament, Match, User

athletes_db: dict[int, Athlete] = {}
tournaments_db: dict[int, Tournament] = {}
matches_db: dict[int, Match] = {}
users_db: dict[int, User] = {}
tokens_db: dict[str, int] = {}

_next_athlete_id = 1
_next_tournament_id = 1
_next_match_id = 1
_next_user_id = 1


def next_athlete_id() -> int:
    global _next_athlete_id
    val = _next_athlete_id
    _next_athlete_id += 1
    return val


def next_tournament_id() -> int:
    global _next_tournament_id
    val = _next_tournament_id
    _next_tournament_id += 1
    return val


def next_match_id() -> int:
    global _next_match_id
    val = _next_match_id
    _next_match_id += 1
    return val


def next_user_id() -> int:
    global _next_user_id
    val = _next_user_id
    _next_user_id += 1
    return val
