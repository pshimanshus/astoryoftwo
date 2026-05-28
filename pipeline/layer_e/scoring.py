from __future__ import annotations

from pipeline.layer_e.contracts import StoryRoute, StorySellingScore


def detect_hard_fails(route: StoryRoute) -> list[str]:
    hard_fails: list[str] = []
    joined = " ".join(
        [
            route.story_lens,
            route.reader_mirror,
            route.emotional_obstacle,
            route.aachu_specific_spark,
            route.zuv_active_role,
            route.proof_engine,
            route.emotional_reversal,
            route.payoff,
            route.distribution_reason,
        ]
    ).lower()
    if not route.emotional_obstacle.strip():
        hard_fails.append("no emotional obstacle")
    if not route.zuv_active_role.strip():
        hard_fails.append("zuv has no active emotional role")
    if not route.proof_engine.strip():
        hard_fails.append("only a pretty moment")
    if not route.payoff.strip():
        hard_fails.append("ending is a quote, not an earned payoff")
    if "aachu" not in joined and "she" not in joined:
        hard_fails.append("generic couple dynamic")
    if not route.distribution_reason.strip():
        hard_fails.append("no reader send/save/comment reason")
    return hard_fails


def score_route(route: StoryRoute) -> StorySellingScore:
    hard_fails = detect_hard_fails(route)
    reader = 5 if route.reader_mirror else 1
    conflict = 5 if route.emotional_obstacle else 1
    proof = 5 if route.proof_engine else 1
    reversal = 5 if route.emotional_reversal else 1
    visual = 5 if route.proof_engine and route.zuv_active_role else 1
    online = 5 if route.distribution_reason else 1
    if hard_fails:
        penalty = min(3, len(hard_fails))
        conflict = max(0, conflict - penalty)
        visual = max(0, visual - penalty)
        online = max(0, online - penalty)
    total = reader + conflict + proof + reversal + visual + online
    return StorySellingScore(
        reader_identity_mirror=reader,
        romantic_conflict_stakes=conflict,
        specificity_of_proof=proof,
        emotional_reversal=reversal,
        visual_scene_clarity=visual,
        online_share_save_sell_potential=online,
        total=total,
    )


def status_for(score: StorySellingScore, hard_fails: list[str]) -> str:
    if hard_fails and score.total < 18:
        return "STOP"
    if hard_fails:
        return "REPAIR"
    if score.total >= 28:
        return "GO"
    if score.total >= 24:
        return "REPAIR"
    return "REWORK"
