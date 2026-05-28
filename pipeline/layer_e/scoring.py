from __future__ import annotations

from pipeline.layer_e.contracts import GoldenThemeScore, StageSceneGate, StoryRoute, StorySellingScore


ACTION_TOKENS = {
    "adjust",
    "angle",
    "bag",
    "barefoot",
    "bring",
    "carry",
    "carries",
    "clutch",
    "cup",
    "cups",
    "date",
    "door",
    "doorway",
    "dress",
    "extends",
    "face",
    "fix",
    "frame",
    "give",
    "handoff",
    "hand",
    "hands",
    "hold",
    "holding",
    "holds",
    "kitchen",
    "kneel",
    "jokes",
    "lean",
    "light",
    "notices",
    "path",
    "phone",
    "plate",
    "pull",
    "return",
    "slide",
    "sliding",
    "shoe",
    "shoes",
    "slippers",
    "smile",
    "stack",
    "step",
    "steps",
    "take",
    "takes",
    "torch",
    "walk",
    "wait",
    "waits",
}

SILENCE_TOKENS = {"quiet", "quietly", "silent", "silently", "pause", "wait", "waits", "without", "no speech"}
READER_TOKENS = {"couples", "partner", "viewer", "viewers", "people", "anyone", "stranger", "relationship"}
SEND_TOKENS = {"send", "save", "tag", "dm", "comment", "partner", "this is us"}
OBSTACLE_TOKENS = {"risk", "risks", "unless", "without", "could", "pressure", "tension", "fear", "misread", "obstacle"}
GENERIC_MARKERS = {"generic romance", "soft feeling", "feels nice", "surface becomes meaning", "relationship truth"}


def _joined(route: StoryRoute) -> str:
    return " ".join(
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


def _contains_any(text: str, tokens: set[str]) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in tokens)


def _token_hits(text: str, tokens: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for token in tokens if token in lowered)


def _is_generic(text: str) -> bool:
    return _contains_any(text, GENERIC_MARKERS)


def stage_scene_gate_for_route(route: StoryRoute) -> StageSceneGate:
    proof = route.proof_engine.strip()
    proof_hits = _token_hits(proof, ACTION_TOKENS)
    has_sequence = proof.count("->") >= 2 or proof_hits >= 3
    blockers: list[str] = []
    if not proof:
        blockers.append("stage-scene gate has no drawable action/reaction proof")
    elif not has_sequence:
        blockers.append("stage-scene gate has no drawable action/reaction proof")
    if not route.emotional_reversal.strip() or _is_generic(route.emotional_reversal):
        blockers.append("stage-scene gate has no earned reaction or reversal")
    if not route.zuv_active_role.strip():
        blockers.append("stage-scene gate has no active partner behavior")
    if route.zuv_active_role and not _contains_any(route.zuv_active_role, ACTION_TOKENS | {"notices", "sees", "watches"}):
        blockers.append("stage-scene gate has no visible active partner action")
    if route.distribution_reason and "nice" in route.distribution_reason.lower() and not _contains_any(route.distribution_reason, {"partner", "this is us", "tag"}):
        blockers.append("stage-scene gate has weak send/save consequence")

    status = "GO" if not blockers else "REPAIR"
    return StageSceneGate(
        status=status,
        action=proof if proof and has_sequence else "",
        reaction=route.emotional_reversal if route.emotional_reversal and not _is_generic(route.emotional_reversal) else "",
        eye_line_or_attention=route.zuv_active_role if route.zuv_active_role else "",
        hands_or_object_movement=proof if proof_hits >= 2 else "",
        silence_or_pause=proof if _contains_any(proof, SILENCE_TOKENS) else "",
        consequence=route.distribution_reason if route.distribution_reason else "",
        reversal_or_payoff=route.payoff if route.payoff and not _is_generic(route.payoff) else "",
        blockers=blockers,
    )


def detect_hard_fails(route: StoryRoute) -> list[str]:
    hard_fails: list[str] = []
    joined = _joined(route)
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
    stage_gate = stage_scene_gate_for_route(route)
    hard_fails.extend(stage_gate.blockers)
    return hard_fails


def _reader_score(route: StoryRoute) -> float:
    text = f"{route.reader_mirror} {route.distribution_reason}".lower()
    if not route.reader_mirror.strip():
        return 1
    if "this is us" in text or (_contains_any(text, READER_TOKENS) and _contains_any(text, SEND_TOKENS)):
        return 5
    if _contains_any(text, READER_TOKENS):
        return 4 if not _is_generic(text) else 3
    return 2


def _conflict_score(route: StoryRoute) -> float:
    obstacle = route.emotional_obstacle.strip()
    if not obstacle:
        return 1
    if _is_generic(obstacle):
        return 3
    if len(obstacle) >= 45 and _contains_any(obstacle, OBSTACLE_TOKENS):
        return 5
    if len(obstacle) >= 30:
        return 4
    return 3


def _proof_score(route: StoryRoute) -> float:
    proof = route.proof_engine.strip()
    if not proof:
        return 1
    hits = _token_hits(proof, ACTION_TOKENS)
    if proof.count("->") >= 2 and hits >= 2:
        return 5
    if hits >= 3:
        return 4
    if hits >= 1:
        return 3
    return 2


def _reversal_score(route: StoryRoute) -> float:
    text = f"{route.emotional_reversal} {route.payoff}".strip()
    if not route.emotional_reversal.strip():
        return 1
    if _is_generic(text):
        return 3
    if len(text) >= 70:
        return 5
    return 4


def _visual_score(route: StoryRoute) -> float:
    gate = stage_scene_gate_for_route(route)
    if gate.status == "GO":
        return 5
    if len(gate.blockers) <= 1:
        return 3
    return 1


def _online_score(route: StoryRoute) -> float:
    text = route.distribution_reason.lower()
    if not text:
        return 1
    if _contains_any(text, {"this is us", "tag", "send", "dm"}) and "partner" in text:
        return 5
    if _contains_any(text, SEND_TOKENS) and not "nice" in text:
        return 4
    if "save" in text:
        return 3
    return 2


def score_route(route: StoryRoute) -> StorySellingScore:
    hard_fails = detect_hard_fails(route)
    reader = _reader_score(route)
    conflict = _conflict_score(route)
    proof = _proof_score(route)
    reversal = _reversal_score(route)
    visual = _visual_score(route)
    online = _online_score(route)
    if hard_fails:
        penalty = min(3, len(set(hard_fails)))
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


def score_golden_theme(route: StoryRoute) -> GoldenThemeScore:
    joined = _joined(route)
    universal = _reader_score(route)
    specificity = 5 if ("aachu" in joined or "she" in joined) and ("zuv" in joined or "he" in joined) else 2
    proof = _proof_score(route)
    zuv_role = 5 if route.zuv_active_role and not any(item in detect_hard_fails(route) for item in ["zuv has no active emotional role", "stage-scene gate has no visible active partner action"]) else 2
    tender = _reversal_score(route)
    share = _online_score(route)
    total = universal + specificity + proof + zuv_role + tender + share
    return GoldenThemeScore(
        universal_hook=universal,
        aachu_zuv_specificity=specificity,
        concrete_proof=proof,
        zuv_emotional_role=zuv_role,
        tender_thesis=tender,
        share_send_potential=share,
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
