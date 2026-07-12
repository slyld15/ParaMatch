import math
from models import Athlete


def ebae_score(a: Athlete, b: Athlete) -> int:
    functional_penalty = abs(a.functional_arms - b.functional_arms) / 2
    arm_penalty = min(abs(a.arm_length_cm - b.arm_length_cm) / 30, 1)
    height_penalty = min(abs(a.height_cm - b.height_cm) / 40, 1)

    total_penalty = (
        functional_penalty * 0.45
        + arm_penalty * 0.30
        + height_penalty * 0.25
    )
    return max(0, round((1 - total_penalty) * 100))


def group_by_category(athletes: list[Athlete]) -> dict[str, list[Athlete]]:
    groups: dict[str, list[Athlete]] = {}
    for a in athletes:
        groups.setdefault(a.category, []).append(a)
    return groups


def _pair_within_group(athletes: list[Athlete]) -> list[dict]:
    pool = athletes.copy()
    pairs = []
    while len(pool) > 1:
        a = pool[0]
        best_idx, best_score = 1, -1
        for i in range(1, len(pool)):
            s = ebae_score(a, pool[i])
            if s > best_score:
                best_score, best_idx = s, i
        b = pool[best_idx]
        pairs.append({"a": a, "b": b, "score": best_score})
        pool = [x for j, x in enumerate(pool) if j not in (0, best_idx)]
    if len(pool) == 1:
        pairs.append({"a": pool[0], "b": None, "score": None})
    return pairs


def generate_fair_pairs(athletes: list[Athlete]) -> list[dict]:
    all_pairs = []
    for group in group_by_category(athletes).values():
        all_pairs.extend(_pair_within_group(group))
    return all_pairs


def pad_to_power_of_two(athletes: list[Athlete]) -> list[Athlete | None]:
    n = len(athletes)
    if n <= 1:
        return athletes.copy()
    target = 2 ** math.ceil(math.log2(n))
    padded = athletes.copy()
    while len(padded) < target:
        padded.append(None)
    return padded


def generate_next_round(previous_round_winners: list[Athlete]) -> list[dict]:
    pairs = []
    for group in group_by_category(previous_round_winners).values():
        for i in range(0, len(group), 2):
            a = group[i]
            b = group[i + 1] if i + 1 < len(group) else None
            pairs.append({"a": a, "b": b, "score": None})
    return pairs
