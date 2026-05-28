"""Story lane classification and slide planning for Codex-native carousels."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pipeline.stages.successful_carousel_standard import stage_scene_storytelling_issues

IDENTITY_IMAGE_DIR = "identity_images"
SUPPORTED_IDENTITY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IDENTITY_REFERENCE_BUNDLE = 4
FALLBACK_COMPACT_STYLE_PROMPT = (
    "premium hand-drawn romantic watercolor-and-ink illustration on warm ivory paper, fine ink/pencil "
    "linework, soft watercolor wash, muted vintage palette, recurring Aachu/Zuv faces, "
    "model-native handwritten text, tiny @a.storyof.two brandmark"
)
IDENTITY_REFERENCE_RULE = (
    "Do not dump every identity image into a carousel prompt. Treat identity_images/ "
    "as a candidate library, then use a small curated bundle for each run."
)
MORNING_PERSON_TOKENS = ["morning person", "5 more minutes", "five more minutes", "questions later"]
WATERFALL_LANTERN_TOKENS = ["waterfall", "lantern"]
PHOTO_RITUAL_TOKENS = [
    "bas ek photo aur",
    "one more photo",
    "last one promise",
    "photo ritual",
    "memory maker",
    "haan baba",
]
KASHMIRI_LANGUAGE_TOKENS = [
    "learned the vibe",
    "learn the vibe",
    "meaning",
    "kashmiri words",
    "ursu",
    "patpahan",
    "namaskar mahara",
]
SUBTITLE_LANGUAGE_TOKENS = [
    "subtitles",
    "kuch nahi",
    "full paragraph",
    "translation",
    "translate",
]
MOOD_CHANGED_TOKENS = [
    "her mood changed",
    "his hand did not",
    "hand still reaches",
    "love keeps pace",
    "slows the world down",
    "moods change mid-walk",
]
WORKDAY_HOMECOMING_WORK_TOKENS = [
    "bad work day",
    "bad workday",
    "bad day at work",
    "work day",
    "workday",
    "office",
    "meeting",
    "meetings",
    "deadline",
    "deadlines",
]
WORKDAY_HOMECOMING_HOME_TOKENS = [
    "car",
    "parked car",
    "driving home",
    "drive home",
    "home",
    "waiting for him",
    "waiting at home",
    "ghar aa jao",
    "chai",
    "maybe chaos is also home",
]
HIGH_MAINTENANCE_CARE_TOKENS = [
    "high-maintenance",
    "high maintenance",
    "care without shrinking",
    "before she asked",
    "tiny discomfort",
    "green dress",
    "bare feet",
    "barefoot",
]
PAKKA_REASSURANCE_TOKENS = [
    "pakka",
    "softest hearts ask twice",
    "smallest doubt",
    "tiny overthink",
    "reassurance",
    "ask twice",
]
FIFTY_FIFTY_CARE_TOKENS = [
    "50-50",
    "fifty-fifty",
    "fifty fifty",
    "not always 50",
    "not splitting chores",
    "chores 50",
    "paani was never the point",
    "heavier half",
    "before counting",
    "not keeping score",
]
FOOD_DENIAL_TOKENS = [
    "not hungry",
    "mujhe kuch nahi chahiye",
    "bas ek bite",
    "one bite",
    "best bite",
    "orders extra",
    "order extra",
    "extra now",
    "plate",
]
WALLET_AUDIT_TOKENS = [
    "wallet audit",
    "audit wallet",
    "audit wallets",
    "finance minister",
    "bas 500",
    "backup pocket",
    "emergency cash",
    "nonsense has a budget",
    "budgeting for each other's nonsense",
]
TASTY_LIFE_TOKENS = [
    "55 se 70",
    "55 to 70",
    "55-70",
    "life zyada tasty",
    "life zyaada tasty",
    "tasty ho gayi",
    "tasty ho gyi",
    "zyada tasty ho gayi",
    "zyaada tasty ho gayi",
]
UNFILTERED_NONSENSE_TOKENS = [
    "joins your nonsense",
    "fluent in you",
    "fluent in your nonsense",
    "unfiltered version",
    "uncut version",
    "real-life version",
    "real life version",
    "five updates for one thought",
    "5 updates for 1 thought",
    "stories from the middle",
    "starts stories from the middle",
    "random commentary",
    "plot twist",
    "private logic",
]
PRIVATE_CAPTIONS_TOKENS = [
    "private captions",
    "some couples come with private captions",
    "paired labels",
    "paired label",
    "labels over shared scenes",
    "her: being dramatic",
    "him: taking it seriously",
    "listening first",
    "happy because she is",
    "already on her side",
    "knows he's soft",
    "favorite sound",
    "captions you kindly",
    "caption you kindly",
    "second caption",
]
SOFTNESS_UNDER_FIRE_TOKENS = [
    "softness under fire",
    "says everything gently",
    "be safe",
    "spicy attitude",
    "hurt underneath",
    "hurt she is",
    "physical affection",
    "holding his sleeve",
    "don't touch me",
    "dont touch me",
]
IMPERFECT_REPAIR_TOKENS = [
    "she was sorry",
    "sorry. bas style alag",
    "bas style alag",
    "apology with attitude",
    "apology's accent",
    "apologys accent",
    "apology language",
    "repair language",
    "delayed repair",
    "post-fight repair",
    "fixing your collar",
    "fixing his collar",
    "fixed his collar",
    "collar",
    "dupatta",
    "came back with attitude",
    "stood close again",
]
LONG_DISTANCE_ORDINARY_TOKENS = [
    "long distance",
    "ordinary tuesday",
    "boring things",
    "normal tuesday",
    "board games",
    "board game",
    "cab is late",
    "cab late",
    "cook together",
    "ruin dinner",
    "ruin food",
    "miss wasting time",
    "ordinary time",
    "same person",
]
SUITCASE_RELOCATION_TOKENS = [
    "suitcase relocation",
    "relocate the house",
    "relocated the house",
    "overpackers blaming the zip",
    "blamed the zip",
    "blame the zip",
    "only the zip",
    "packing chaos",
    "pack light",
    "forgot toothbrushes",
    "forgot the toothbrushes",
]
SUITCASE_RELOCATION_CONTINUITY_LOCK = (
    "Two-act visual continuity lock: slides 1-4 stay in the home bedroom packing room; slides "
    "5-7 move to the destination arrival room/bathroom corner after travel. Keep the same "
    "Aachu/Zuv faces, same watercolor-and-ink style, Aachu's same off-white oversized shirt "
    "and blue jeans, Zuv's same navy t-shirt and beige pants, same dark olive hard-shell "
    "suitcase with black zip, same cream toiletry pouch, charger pile, folded outfits, travel "
    "shoes, warm paper palette, and handwritten text system across both acts."
)
SUITCASE_RELOCATION_SHARED_VISUAL_LOCK = (
    "Keep the same Aachu/Zuv faces, same watercolor-and-ink style, Aachu's same off-white "
    "oversized shirt and blue jeans, Zuv's same navy t-shirt and beige pants, same dark olive "
    "hard-shell suitcase with black zip, same cream toiletry pouch, charger pile, folded "
    "outfits, travel shoes, warm paper palette, and handwritten text system."
)
SUITCASE_RELOCATION_HOME_VISUAL_LOCK = (
    "Two-act visual continuity lock: home bedroom packing room act. "
    f"{SUITCASE_RELOCATION_SHARED_VISUAL_LOCK}"
)
SUITCASE_RELOCATION_DESTINATION_VISUAL_LOCK = (
    "Two-act visual continuity lock: destination arrival act after travel. "
    f"{SUITCASE_RELOCATION_SHARED_VISUAL_LOCK}"
)
SUITCASE_RELOCATION_WARDROBE_LOCK = (
    "Aachu keeps the same off-white oversized shirt, blue jeans, and small gold earrings as "
    "travel-day continuity; Zuv keeps the same navy t-shirt, beige pants, and watch. Footwear "
    "may progress naturally from home slippers/socks during packing to travel shoes or shoes-off "
    "arrival comfort at the destination, but do not invent a new outfit."
)
SUITCASE_RELOCATION_PROP_LOCK = (
    "Use the same dark olive hard-shell suitcase with black zip as the central recurring object; "
    "carry the same cream toiletry pouch, charger pile, folded outfit stack, travel shoes, and "
    "overpacked clothes from the home-packing act into the destination-arrival act."
)
SUITCASE_RELOCATION_BACKGROUND_LOCK = (
    "Use a clear two-act background: slides 1-4 are the warm home bedroom packing room with wooden "
    "bed, potted plant, and suitcase on the floor; slides 5-7 are a simple destination hotel/Airbnb "
    "arrival room or bathroom corner with the same suitcase and pouch. The location change must be "
    "intentional and readable, not random drift."
)

STORY_SELLING_CONTRACT = {
    "skill": "config/skills/romance-story-selling-engine.md",
    "references": [
        "config/skills/carousel-story-director-persona.md",
        "config/references/story-selling-canon/source-policy.md",
        "config/references/story-selling-canon/a-story-of-two-adaptation.md",
        "config/references/story-selling-canon/concept-process-cards.md",
        "config/references/story-selling-canon/rubric.md",
        "config/references/story-selling-canon/story-selling-online.md",
    ],
    "minimum_score": 28,
    "rule": (
        "Begin concept thinking like an author: find the relationship obstacle, "
        "choose one process card, prove the feeling with Aachu/Zuv behavior, "
        "then score before writing slides or captions."
    ),
}

CAROUSEL_STORY_DIRECTOR_CONTRACT = {
    "skill": "config/skills/carousel-story-director-persona.md",
    "agent": "agents/carousel-story-director.md",
    "activation_order": [
        "project and creator memory",
        "Calm Enough For Your Chaos theme",
        "viral theme analysis",
        "carousel idea preference ledger",
        "Layer E story-selling engine",
        "golden-theme tournament",
        "carousel story director persona before writing/designing",
    ],
    "rule": (
        "Before any hook, slide copy, caption, visual direction, prompt, or image handoff, "
        "confirm hook, setup, proof, escalation, bridge, active Zuv role, earned ending, "
        "and send/save reason."
    ),
    "persists_until": [
        "concept.json",
        "slides.json",
        "visual-debate.json",
        "visual-plan-quality.json",
        "prompt-pack.json",
        "copy.json",
        "codex-image-prompts/",
        "final/",
        "final-reels-stories/",
        "visual-qa.md",
    ],
    "minimum_scores": {
        "hook": 8,
        "story": 8,
        "bridge": 8,
        "zuv_role": 8,
        "ending": 8,
        "send_save_potential": 8,
        "stage_scene": 8,
    },
}

STORY_PROCESS_BY_LANE = {
    "Golden Reassurance": ("Card 13 - The Way He Stays", 30),
    "Himanshu POV": ("Card 13 - The Way He Stays", 29),
    "Golden Private Captions": ("Card 05 - Banter To Belonging", 29.7),
    "Golden Care Without Shrinking": ("Card 07 - Anti-Ideal To Real Love", 29.5),
    "Golden Fairness Without Scorekeeping": ("Card 07 - Anti-Ideal To Real Love", 29.5),
    "Golden Food Denial": ("Card 05 - Banter To Belonging", 29.5),
    "Golden Wallet Audit Love": ("Card 05 - Banter To Belonging", 30),
    "Golden Tasty Life": ("Card 05 - Banter To Belonging", 29.7),
    "Golden Unfiltered Nonsense": ("Card 05 - Banter To Belonging", 29.5),
    "Golden Softness Under Fire": ("Card 02 - Misread To Tender Truth", 29.5),
    "Golden Imperfect Repair": ("Card 06 - Delay The Confession", 29.5),
    "Golden Long Distance Ordinary Time": ("Card 05 - Banter To Belonging", 29.5),
    "Golden Suitcase Relocation": ("Card 05 - Banter To Belonging", 30),
    "Golden Mood Steadiness": ("Card 11 - Visual Reversal", 29),
    "Tiny Rituals": ("Card 08 - Small Ritual, Large Promise", 28.5),
    "Kashmiri Wife x Non-Kashmiri Husband": ("Card 12 - The Thing She Brings", 28.5),
    "Chaotic Wife, Calm Husband": ("Card 19 - Almost Too Much, Exactly Enough", 29),
    "Wedding Origin Story": ("Card 06 - Delay The Confession", 28.5),
    "Soft Love Notes": ("Card 20 - Saveable Lesson From One Scene", 28),
}


def story_selling_scorecard(total: float) -> dict[str, float]:
    if total >= 30:
        parts = [5, 5, 5, 5, 5, 5]
    elif total >= 29.5:
        parts = [5, 5, 5, 5, 5, 4.5]
    elif total >= 29:
        parts = [5, 5, 5, 5, 4, 5]
    elif total >= 28.5:
        parts = [5, 5, 4.5, 5, 4, 5]
    else:
        parts = [5, 4, 5, 4, 5, 5]
    return {
        "reader_identity_mirror": parts[0],
        "romantic_conflict_stakes": parts[1],
        "specificity_of_proof": parts[2],
        "emotional_reversal": parts[3],
        "visual_scene_clarity": parts[4],
        "online_share_save_sell_potential": parts[5],
        "total": total,
    }


def build_story_director_gate(
    *,
    story: str,
    lane: str,
    slides: list[dict[str, Any]],
    human_truth: str,
    emotional_arc: str,
    concept_selection: dict[str, Any] | None,
) -> dict[str, Any]:
    slide_one = slides[0] if slides else {}
    final_slide = slides[-1] if slides else {}
    roles = [str(slide.get("role", "")).lower() for slide in slides]
    copies = [str(slide.get("copy", "")) for slide in slides]
    visuals = [str(slide.get("visual", "")) for slide in slides]

    has_hook = "hook" in str(slide_one.get("role", "")).lower() or "universal" in str(
        slide_one.get("role", "")
    ).lower()
    has_setup = len(slides) >= 4 and bool(human_truth)
    has_proof = any("proof" in role or "reveal" in role or "specific" in role for role in roles)
    has_escalation = any(
        token in " ".join([*roles, *copies]).lower()
        for token in ["proof", "turn", "escalation", "specific", "concrete", "then", "still"]
    )
    has_bridge = any("turn" in role or "bridge" in role or "zuv role" in role for role in roles) or "->" in emotional_arc
    has_zuv_role = any("zuv" in role or "zuv" in visual.lower() or "he " in visual.lower() for role, visual in zip(roles, visuals))
    has_ending = any(
        token in str(final_slide.get("role", "")).lower() or token in str(final_slide.get("copy", "")).lower()
        for token in ["payoff", "thesis", "save", "share", "maybe", "love"]
    )
    has_send_save = any(str(slide.get("cta_intent", "")).strip() for slide in slides)
    stage_scene_issues = stage_scene_storytelling_issues(slides)

    blocks: list[str] = []
    if not has_hook:
        blocks.append("Slide 1 is not clearly marked as a public hook.")
    if not has_setup:
        blocks.append("Story setup is not explicit enough before proof beats.")
    if not has_proof:
        blocks.append("No clear concrete proof or Aachu-specific reveal found.")
    if not has_bridge:
        blocks.append("Bridge from surface behavior to emotional meaning is missing.")
    if not has_zuv_role:
        blocks.append("Zuv's active role is not visible in the slide plan.")
    if not has_ending:
        blocks.append("Final slide is not an earned love thesis or save/share payoff.")
    if not has_send_save:
        blocks.append("Slides do not name a send/save/tag reason.")
    blocks.extend(stage_scene_issues)

    scores = {
        "hook": 9 if has_hook else 5,
        "story": 9 if has_setup and has_proof else 6,
        "bridge": 9 if has_bridge else 5,
        "zuv_role": 9 if has_zuv_role else 5,
        "ending": 9 if has_ending else 5,
        "send_save_potential": 9 if has_send_save else 5,
        "stage_scene": 9 if not stage_scene_issues else 5,
    }
    status = "PASS" if not blocks and all(value >= 8 for value in scores.values()) else "REPAIR"
    selected_hook = str(slide_one.get("copy", ""))
    return {
        "contract": CAROUSEL_STORY_DIRECTOR_CONTRACT,
        "status": status,
        "concept_diagnosis": {
            "public_hook": selected_hook,
            "reader_identity_mirror": human_truth,
            "emotional_obstacle": human_truth,
            "aachu_proof": next((slide.get("visual", "") for slide in slides if "zuv" not in str(slide.get("role", "")).lower()), ""),
            "zuv_active_role": next((slide.get("visual", "") for slide in slides if "zuv" in str(slide.get("role", "")).lower()), ""),
            "bridge": emotional_arc,
            "earned_ending": str(final_slide.get("copy", "")),
            "send_save_reason": next((slide.get("cta_intent", "") for slide in slides if slide.get("cta_intent")), ""),
        },
        "hook_bank": [
            {
                "hook": selected_hook,
                "score": scores["hook"],
                "why": "Current selected first-slide hook from deterministic builder.",
            },
            {
                "hook": human_truth.split(";")[0][:90],
                "score": 8,
                "why": "Universal relationship truth variant; should be sharpened by the next creative pass.",
            },
            {
                "hook": f"Some love stories start with {lane.lower()}.",
                "score": 7,
                "why": "Fallback lane hook; usually weaker than a behavior-specific line.",
            },
            {
                "hook": "The line is not the story yet.",
                "score": 8,
                "why": "Process reminder when a liked payoff is being mistaken for a deck.",
            },
            {
                "hook": "Make them send it before making it pretty.",
                "score": 8,
                "why": "Distribution test hook for internal review, not public copy.",
            },
        ],
        "selected_hook": selected_hook,
        "story_spine": [
            {"beat": "hook", "job": "Stop the scroll with a public relationship truth.", "must_show": selected_hook},
            {"beat": "setup", "job": "Define the pattern or situation.", "must_show": human_truth},
            {"beat": "proof", "job": "Show a concrete Aachu/Zuv behavior.", "must_show": "One visible action, not explanation."},
            {"beat": "escalation", "job": "Sharpen recognition or humor.", "must_show": "A more specific receipt."},
            {"beat": "bridge", "job": "Turn surface behavior into emotional meaning.", "must_show": emotional_arc},
            {"beat": "zuv_role", "job": "Make Zuv's calm active.", "must_show": "He notices, chooses, carries, protects, or softens."},
            {
                "beat": "stage_scene",
                "job": "Make the story understandable if poster text is hidden.",
                "must_show": "Action, reaction, hands, eye-line, distance, object movement, consequence, and payoff.",
            },
            {"beat": "ending", "job": "Land the earned save/share thesis.", "must_show": str(final_slide.get("copy", ""))},
        ],
        "structural_audit": scores,
        "verdict": (
            "PASS: persona spine is loaded and present in package artifacts."
            if status == "PASS"
            else "REPAIR: fix blocks before image generation or final copy."
        ),
        "blocks": blocks,
        "concept_selection_used": bool(concept_selection),
        "source_story": story,
    }


def build_story_selling_decision(
    *,
    lane: str,
    story: str,
    human_truth: str,
    emotional_arc: str,
    concept_selection: dict[str, Any] | None,
) -> dict[str, Any]:
    selected_card, total = STORY_PROCESS_BY_LANE.get(
        lane,
        ("Card 20 - Saveable Lesson From One Scene", 28),
    )
    if concept_selection:
        total = max(float(total), float(concept_selection.get("winner_score", total)))

    score = story_selling_scorecard(total)
    candidates = [
        {
            "name": "Obstacle First",
            "concept_process_card": "Card 01 - Obstacle To Care",
            "story_selling_score": 27,
            "verdict": "REPAIR: useful care lens, but less native to this moment.",
        },
        {
            "name": "Proof Before Poetry",
            "concept_process_card": "Card 15 - Proof Before Poetry",
            "story_selling_score": 28,
            "verdict": "GO: keeps the writing grounded in behavior.",
        },
        {
            "name": "Selected Authorial Spine",
            "concept_process_card": selected_card,
            "story_selling_score": total,
            "verdict": "GO: strongest fit for the story's emotional machine.",
        },
        {
            "name": "Scene Before Summary",
            "concept_process_card": "Card 16 - Scene Before Summary",
            "story_selling_score": 27.5,
            "verdict": "REPAIR: strong visual discipline, weaker save/share thesis.",
        },
        {
            "name": "Saveable Lesson",
            "concept_process_card": "Card 20 - Saveable Lesson From One Scene",
            "story_selling_score": 28,
            "verdict": "GO: reliable fallback for article/caption expansion.",
        },
    ]
    if concept_selection:
        candidates.extend(
            {
                "name": candidate["name"],
                "concept_process_card": selected_card,
                "story_selling_score": min(30, float(candidate.get("total", total))),
                "verdict": "GO" if float(candidate.get("total", 0)) >= 28 else "REPAIR",
            }
            for candidate in concept_selection.get("candidates", [])[:5]
        )

    return {
        "contract": STORY_SELLING_CONTRACT,
        "selected_concept_process_card": selected_card,
        "score": score,
        "threshold": "28/30",
        "decision": "GO" if score["total"] >= STORY_SELLING_CONTRACT["minimum_score"] else "REPAIR",
        "hard_fails": [],
        "selector_verdict": (
            f"Begin with {selected_card}: the concept is approved because it starts from a "
            "relationship obstacle, proves the truth through Aachu/Zuv behavior, and lands a "
            "saveable love thesis before slide copy or caption language is written."
        ),
        "authorial_flow": {
            "relationship_obstacle": human_truth,
            "proof_engine": emotional_arc,
            "writer_rule": "No quote-pack thinking; every line must be earned by a scene, gesture, object, or choice.",
            "story_context": story,
        },
        "candidate_table": candidates[:10],
    }
MAIN_KAR_LUNGI_TOKENS = [
    "main kar lungi",
    "main kar loongi",
    "i will do it myself",
    "do it herself",
    "translation: don't go far",
    "care without making a scene",
    "without making a scene",
]


def slugify(value: str, fallback: str = "illustration-carousel") -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or fallback


def normalize_paths(image_paths: list[str | Path]) -> list[Path]:
    paths = [Path(path).expanduser() for path in image_paths]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing reference image(s): " + ", ".join(missing))
    return paths


def discover_identity_images(workspace_root: Path) -> list[Path]:
    identity_dir = workspace_root / IDENTITY_IMAGE_DIR
    if not identity_dir.exists():
        return []
    return sorted(
        path
        for path in identity_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IDENTITY_IMAGE_EXTENSIONS
    )


def select_identity_reference_bundle(candidate_paths: list[Path], *, explicit: bool) -> list[Path]:
    if explicit and len(candidate_paths) > MAX_IDENTITY_REFERENCE_BUNDLE:
        raise ValueError(
            f"Use at most {MAX_IDENTITY_REFERENCE_BUNDLE} curated identity references "
            "for one carousel. Pick a face anchor, body/posture anchor, and any "
            "story-relevant outfit/detail anchors instead of passing the whole library."
        )
    return candidate_paths[:MAX_IDENTITY_REFERENCE_BUNDLE]


def build_identity_reference_selection(
    *,
    candidate_paths: list[Path],
    selected_paths: list[Path],
    explicit: bool,
) -> dict[str, Any]:
    return {
        "mode": "explicit_cli_bundle" if explicit else "auto_discovered_candidate_library",
        "rule": IDENTITY_REFERENCE_RULE,
        "max_prompt_images": MAX_IDENTITY_REFERENCE_BUNDLE,
        "candidate_count": len(candidate_paths),
        "selected_count": len(selected_paths),
        "unselected_count": max(0, len(candidate_paths) - len(selected_paths)),
        "selected_roles": [
            "face anchor",
            "body/posture anchor",
            "story-relevant outfit or context anchor",
            "emotion/detail anchor",
        ][: len(selected_paths)],
        "guidance": (
            "For best results, pass 2-4 --identity-image paths that match the story. "
            "Auto-discovery is a fallback that keeps prompts small, not a promise that "
            "every image in identity_images/ will be attached."
        ),
    }


def infer_workspace_root(output_root: Path) -> Path:
    resolved = output_root.expanduser().resolve()
    if resolved.name == "carousels" and resolved.parent.name == "output":
        return resolved.parent.parent
    return resolved.parent


def infer_title(story: str, title: str | None) -> str:
    if title and title.strip():
        return title.strip()
    lower = story.lower()
    if any(token in lower for token in UNFILTERED_NONSENSE_TOKENS):
        return "Marry The One Who Joins Your Nonsense"
    if any(token in lower for token in LONG_DISTANCE_ORDINARY_TOKENS):
        return "Ordinary Time With You"
    if "ladakh" in lower and "first" in lower:
        return "From First Date To Ladakh"
    if "ladakh" in lower:
        return "Us In Ladakh"
    if "first date" in lower:
        return "The First Date"
    return "A Story Of Two"


def infer_place(story: str) -> str:
    lower = story.lower()
    if "ladakh" in lower:
        return "Ladakh"
    if "kashmir" in lower:
        return "Kashmir"
    return "the trip"


def infer_origin(story: str) -> str:
    lower = story.lower()
    if "cup" in lower or "starbucks" in lower:
        return "two names on cups"
    if "first date" in lower:
        return "one first date"
    return "one ordinary moment"


def classify_content_lane(story: str) -> str:
    lower = story.lower()
    if is_private_captions_story(story):
        return "Golden Private Captions"
    if is_unfiltered_nonsense_story(story):
        return "Golden Unfiltered Nonsense"
    if is_long_distance_ordinary_story(story):
        return "Golden Long Distance Ordinary Time"
    if is_suitcase_relocation_story(story):
        return "Golden Suitcase Relocation"
    if is_tasty_life_story(story):
        return "Golden Tasty Life"
    if is_wallet_audit_story(story):
        return "Golden Wallet Audit Love"
    if is_food_denial_story(story):
        return "Golden Food Denial"
    if is_fifty_fifty_care_story(story):
        return "Golden Fairness Without Scorekeeping"
    if is_main_kar_lungi_story(story):
        return "Golden Independent Care"
    if is_pakka_reassurance_story(story):
        return "Golden Reassurance"
    if is_softness_under_fire_story(story):
        return "Golden Softness Under Fire"
    if is_imperfect_repair_story(story):
        return "Golden Imperfect Repair"
    if is_workday_homecoming_story(story):
        return "Himanshu POV"
    if is_high_maintenance_care_story(story):
        return "Golden Care Without Shrinking"
    if any(token in lower for token in MOOD_CHANGED_TOKENS):
        return "Golden Mood Steadiness"
    if any(token in lower for token in SUBTITLE_LANGUAGE_TOKENS):
        return "Chaotic Wife, Calm Husband"
    if any(token in lower for token in PHOTO_RITUAL_TOKENS):
        return "Tiny Rituals"
    if any(token in lower for token in MORNING_PERSON_TOKENS):
        return "Chaotic Wife, Calm Husband"
    if any(token in lower for token in ["anklet", "shoe", "shoes", "sandal", "sandals", "chai", "gossip", "feeds me"]):
        return "Tiny Rituals"
    if any(token in lower for token in ["kashmir", "kashmiri", "noon chai", "wazwan"]):
        return "Kashmiri Wife x Non-Kashmiri Husband"
    if any(token in lower for token in ["chaos", "dramatic", "mood", "leaving", "peace"]):
        return "Chaotic Wife, Calm Husband"
    if any(token in lower for token in ["proposal", "shaadi", "wedding", "married", "marriage"]):
        return "Wedding Origin Story"
    return "Soft Love Notes"


def distribute_sources(paths: list[Path], slide_count: int) -> list[list[str]]:
    if not paths:
        return [[] for _ in range(slide_count)]

    groups: list[list[str]] = [[] for _ in range(slide_count)]
    for index, path in enumerate(paths):
        slide_index = min(slide_count - 1, round(index * (slide_count - 1) / max(1, len(paths) - 1)))
        groups[slide_index].append(str(path))
    for index, group in enumerate(groups):
        if not group:
            groups[index].append(str(paths[min(index, len(paths) - 1)]))
    return groups


def build_identity_continuity_for_slide(slide: dict[str, Any], identity_paths: list[str]) -> dict[str, Any]:
    emotion = slide.get("emotion", "the slide emotion")
    return {
        "slide": slide.get("slide"),
        "identity_references": identity_paths,
        "face_structure": (
            "Match the real face structure from the selected identity bundle for both people: "
            "recurring facial proportions, hairline, jaw/cheek shape, eyes, brows, nose, smile, "
            "and relative height/posture. Do not substitute generic Indian couple faces."
        ),
        "facial_expression": (
            f"Keep the facial expression specific to this beat ({emotion}) while preserving the "
            "same underlying face structure across all slides."
        ),
        "clothing": (
            "Use story-relevant clothes, dupatta/shawl/shirt colors, accessories, and body-language "
            "cues from the identity bundle when visible; keep outfit continuity intentional instead "
            "of inventing random wardrobe changes."
        ),
        "cross_slide_consistency": (
            "The illustrated couple must read as the same Anchal/Aachu and Himanshu/Zuv in every slide, "
            "with consistent faces, hair, body proportions, and relationship energy."
        ),
    }


def build_identity_continuity_prompt(slide: dict[str, Any], identity_paths: list[str]) -> str:
    continuity = build_identity_continuity_for_slide(slide, identity_paths)
    joined_identity_paths = "; ".join(identity_paths)
    return (
        "Identity continuity lock (non-negotiable): use the selected identity image bundle as actual visual "
        "reference input, not decoration. "
        f"References: {joined_identity_paths}. "
        f"{continuity['face_structure']} "
        f"{continuity['facial_expression']} "
        f"{continuity['clothing']} "
        f"{continuity['cross_slide_consistency']}"
    )


def build_identity_consistency_review(
    *,
    slides: list[dict[str, Any]],
    prompt_slides: list[dict[str, Any]],
    identity_paths: list[str],
) -> dict[str, Any]:
    issues: list[str] = []
    if not identity_paths:
        issues.append("No selected identity reference images; face consistency cannot be enforced.")

    prompt_by_slide = {int(prompt["slide"]): prompt for prompt in prompt_slides}
    slide_reviews: list[dict[str, Any]] = []
    for slide in slides:
        number = int(slide["slide"])
        continuity = slide.get("identity_continuity", {})
        prompt = prompt_by_slide.get(number, {}).get("prompt", "")
        checks = {
            "face_structure": bool(continuity.get("face_structure")) and "face structure" in prompt.lower(),
            "facial_expression": bool(continuity.get("facial_expression")) and "facial expression" in prompt.lower(),
            "clothing": bool(continuity.get("clothing")) and "clothes" in prompt.lower(),
            "cross_slide_consistency": bool(continuity.get("cross_slide_consistency"))
            and "same" in prompt.lower()
            and "every slide" in prompt.lower(),
            "identity_references_attached": all(path in prompt for path in identity_paths),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            issues.append(f"Slide {number} identity continuity missing: {', '.join(failed)}.")
        slide_reviews.append(
            {
                "slide": number,
                "copy": slide.get("copy", ""),
                "checks": checks,
                "identity_continuity": continuity,
            }
        )

    return {
        "agent": "C3.5-IdentityConsistency",
        "role": (
            "Runs after slide descriptions are generated and before image generation; blocks prompts "
            "that do not explicitly carry face structure, expression, clothing, and cross-slide identity continuity."
        ),
        "status": "PASS" if not issues else "NEEDS_FIXES",
        "identity_references": identity_paths,
        "slides": slide_reviews,
        "issues": issues,
    }


def build_tiny_ritual_anklet_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Before the ring, there was an anklet.",
        "He thought he was tying jewellery.",
        "Maybe love had already bent down.",
        "Now it's shoes. Sandals. Same boy.",
        "Some promises don't need new words.",
    ][:slide_count]
    visuals = [
        "Aachu sits in the mountain-window room while Zuv kneels and ties the anklet before proposing.",
        "Close-up of Zuv's hands tying the anklet around Aachu's foot, warm off-white background.",
        "Then-and-now visual rhyme: anklet before proposal, sandal after marriage, same kneeling posture.",
        "Aachu laughs on the balcony while Zuv fastens her golden sandal; playful married-life care.",
        "Minimal close-up of anklet and fastened sandal strap, with Zuv's hand leaving the frame.",
    ][:slide_count]
    roles = ["hook", "meaning reveal", "turn", "married-life proof", "payoff"][:slide_count]
    emotions = ["private", "tender", "realizing", "playful", "settled"][:slide_count]
    source_groups = distribute_sources(image_paths, slide_count)
    return [
        {
            "slide": index,
            "copy": copy,
            "role": roles[index - 1],
            "visual": visuals[index - 1],
            "emotion": emotions[index - 1],
            "cta_intent": "make couples send this as a tiny-ritual love-language moment",
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]


def build_chaotic_wife_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He didn't marry peace.",
        "\"Mujhe kuch nahi hua\" means something definitely happened.",
        "She packed 14 outfits for one plan.",
        "She had 10 moods before lunch.",
        "Maybe love is not less chaos. Maybe it is safer chaos.",
    ][:slide_count]
    visuals = [
        "Zuv stands calmly in a simple kurta with chai and keys, looking lovingly confused beside Aachu's tiny storm of dupatta and emotion.",
        "Aachu looks away dramatically with one tear while insisting she is fine; Zuv quietly offers tissues and water.",
        "Aachu sits on an overflowing suitcase with clothes, bangles, and one sandal visible; Zuv patiently tries to zip it closed.",
        "Three tiny Aachu mood beats around one snack plate: upset, hungry, suddenly cute; Zuv offers food with a steady smile.",
        "Aachu and Zuv walk out hand in hand, her little trail of chaos behind them, his posture calm and chosen.",
    ][:slide_count]
    roles = ["universal hook", "special revelation", "proof beat", "emotional turn", "save/share thesis"][:slide_count]
    emotions = ["playful rupture", "soft drama", "comic specificity", "affectionate recognition", "tender acceptance"][:slide_count]
    source_groups = distribute_sources(image_paths, slide_count)
    return [
        {
            "slide": index,
            "copy": copy,
            "role": roles[index - 1],
            "visual": visuals[index - 1],
            "emotion": emotions[index - 1],
            "cta_intent": "make partners send this as affectionate recognition of lovable chaos",
            "text_layout": {
                "primary_position": "top_center" if index in {1, 4, 5} else "bottom_center",
                "speech_bubble": "mujhe kuch\nnahi hua" if index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]


def build_mood_changed_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some moods change mid-walk.",
        "She feels everything fully.",
        "Her hand still reaches.",
        "He slows the world down.",
        "Love keeps pace.",
    ]
    visuals = [
        "Aachu and Zuv walking side by side on a simple warm paper path; her expression shifts mid-step from bright to suddenly quiet while his hand stays calmly open beside her.",
        "Aachu shown in three tiny emotional beats around the same walking moment: bright, overwhelmed, soft again; Zuv remains nearby without making her feelings smaller.",
        "Close focus on their hands: Aachu's hand reaches back even while her face looks away, and Zuv's hand is steady, patient, and easy to find.",
        "Zuv gently slows his stride and turns toward Aachu, making the busy world around them fade into simple lines while she has room to feel everything.",
        "Aachu and Zuv continue walking hand in hand at the same pace, the mood behind them becoming a small soft trail rather than a storm.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "expressive tenderness", "quiet proof", "steady care", "soft landing"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners save or send this as a tender proof of steady love during changing moods",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_workday_homecoming_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some days make him want silence.",
        "Then he remembers her waiting.",
        "Chai. Drama. One long story.",
        "And he smiles before home.",
        "Maybe chaos is also home.",
    ]
    visuals = [
        "Zuv sits in a parked car after a bad workday, office bag and laptop beside him, shoulders tired, city/office lines fading behind the windshield.",
        "His phone lights up with Aachu's warm message: ghar aa jao? The car is still, but the air starts changing around him.",
        "Aachu waiting at home with chai, expressive face, cozy lived-in little chaos, and one long story already loaded before he enters.",
        "Back in the parked car, Zuv's tired face softens into a small smile before he starts driving home, choosing the noise that makes him feel alive again.",
        "A warm doorway-home frame: keys, chai, her lively little chaos, his calm smile, and the feeling that the safest place is not always the quietest one.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["drained recognition", "soft anticipation", "affectionate chaos", "quiet choosing", "tender landing"]
    selected = [0, 2, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners save or send this as a tender proof that home can be a person and their lovable chaos",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "ghar aa jao?" if source_index == 1 else "sun na..." if source_index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_high_maintenance_care_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "She was not high-maintenance.",
        "She was just fully alive.",
        "Bare feet. Green dress. Tiny crisis.",
        "He noticed before she asked.",
        "Maybe love is care without shrinking.",
    ]
    visuals = [
        "A universal relationship hook on the Ayatana balcony: Aachu in her green dress, barefoot and expressive, looking fully alive rather than difficult.",
        "Aachu moving through the balcony in green, hair and posture carrying soft main-character energy; the tiny practical chaos is loved, not judged.",
        "Concrete proof beat: bare feet near the chair, green dress gathered carefully, a small shoe/sandal detail visible as the tiny crisis without making the shoe the whole premise.",
        "Zuv notices the tiny discomfort and kneels with calm warmth to help with the footwear before Aachu has to turn it into a request; his posture is attentive, not performative.",
        "Aachu and Zuv standing close after the moment is handled, the balcony soft behind them, with the feeling that care made her more herself, not smaller.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "alive softness", "playful tiny crisis", "active care", "tender acceptance"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as a tender proof that little needs do not make someone hard to love",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_main_kar_lungi_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Main kar lungi.",
        "Translation: don't go far.",
        "She wanted to do it herself.",
        "He helped like it was nothing.",
        "Maybe love is care without making a scene.",
    ]
    visuals = [
        "Outdoor public threshold after a walk: Aachu steps ahead with chin-up independence and a confident hand gesture, while Zuv stays half a pace behind, attentive but not hovering.",
        "A simple public pathway scene where Aachu's body language says she can handle it, but her glance back says stay close; Zuv keeps the exact respectful distance.",
        "Busy outdoor old-city market lane at golden hour: Aachu leads through the crowd with chin-up pride, managing the moment herself while Zuv stays half a step behind and slightly to the traffic side, matching her pace without touching or hovering.",
        "Same public crowd pressure, but Zuv quietly creates private clearance: he steps diagonally toward the traffic side and subtly holds space with one calm hand gesture so Aachu can pass first and keep the win.",
        "Open courtyard at dusk: they walk together after the moment, her independence intact and his care invisible enough to feel natural.",
    ]
    roles = ["universal hook", "translation reveal", "aachu-specific proof", "zuv role", "save/share thesis"]
    emotions = ["playful pride", "hidden request", "determined softness", "quiet care", "tender landing"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as a tender proof that help can preserve pride",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "main kar lungi" if source_index == 0 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_pakka_reassurance_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "The softest hearts ask twice.",
        "\"Pakka?\" even after the hug.",
        "Then again, after one tiny overthink.",
        "He says \"haan baba\" like it's the first time.",
        "Maybe love is patience with your smallest doubt.",
    ]
    visuals = [
        "A simple warm room hook: Aachu and Zuv close together after a hug, with Aachu's face soft but still needing one more bit of reassurance; the scene feels universal, not private.",
        "Aachu tucked into the hug and looking up with a tiny vulnerable expression; a small speech bubble says 'pakka?' while Zuv's posture stays warm and fully present.",
        "A tiny overthink visualized as two or three soft paper thought loops around Aachu while she holds onto Zuv's sleeve; the doubt is tender, not dramatic or mocked.",
        "Zuv answers with the same calm warmth, one hand around her shoulder, a small speech bubble saying 'haan baba'; he looks like patience is part of the promise.",
        "A quiet final frame of them sitting close, the thought loops faded, his hand still there, her face finally resting; the relationship feels like a safe place for small doubts.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "vulnerable softness", "tiny overthink", "active reassurance", "tender landing"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as reassurance for the person who needs to hear love twice",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "pakka?" if source_index == 1 else "haan baba" if source_index == 3 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_softness_under_fire_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He didn't marry someone who says everything gently.",
        "\"Don't touch me\" still held his sleeve.",
        "\"Be safe\" came out like a warning.",
        "So he heard the hurt underneath.",
        "Maybe love is softness under fire.",
    ]
    visuals = [
        "Same warm restaurant/cafe evening: Aachu is expressive and slightly turned away at the table, arms half-crossed and not cruel, while Zuv sits beside her angled toward her with calm patience; framed wall art, table glasses, and wood panels stay as quiet evidence, not the premise.",
        "Close proof beat at the same table: Aachu's face says don't touch me, but her hand is still holding Zuv's sleeve; Zuv keeps his hand open nearby and stays reachable instead of pulling away.",
        "Same location, later beat near the table or cafe doorway: Zuv reaches for his keys or phone while Aachu says be safe like a warning, brows tense and body leaning toward him; Zuv receives it as worry wearing attitude, not scolding.",
        "Same warm scene after the sharp words: Aachu looks away but stays close, her hand still near his sleeve; Zuv gently steps back into her space, lowers himself to her eye level, and offers an open hand or water, showing he heard the hurt underneath instead of arguing with the tone.",
        "Same evening resolved, in or just outside the cafe/restaurant threshold: Zuv stands close, warm and steady; Aachu leans into him or smiles despite herself, still a little dramatic, while the earlier fire becomes warm light around them.",
    ]
    roles = ["universal hook", "aachu-specific proof", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "contradictory softness", "protective worry", "active understanding", "tender acceptance"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as affectionate recognition that hurt can sound sharp while still asking for closeness",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 4} else "bottom_center",
                "speech_bubble": "be safe" if source_index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_imperfect_repair_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some people don't say sorry.",
        "They come back with attitude.",
        "Still angry, fixing your collar.",
        "And he knows not to laugh.",
        "Love learns the apology's accent.",
    ]
    visuals = [
        "A spacious warm-paper relationship hook: Aachu stands a little turned away after a tiny fight, expressive but soft, while Zuv stands nearby with calm open posture; the background is almost empty, just one simple doorway line and lots of breathing room.",
        "Aachu comes back into the frame with chin-up attitude and one hand adjusting her dupatta or sleeve, clearly returning without saying the perfect word; Zuv stays still and receptive, giving the moment space.",
        "Close, simple proof beat with only their upper bodies: Aachu is still pretending to be annoyed while gently fixing Zuv's collar with careful fingers; Zuv keeps a soft face and does not tease her.",
        "Zuv looks down with the smallest controlled smile, choosing not to laugh because he understands this is her repair language; Aachu's body is close but proud, the scene uncluttered and tender.",
        "Final airy couple frame: the distance between them has closed, one small collar/dupatta detail remains as the receipt, and the warm off-white space around them carries the quiet apology.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "proud softness", "visible repair", "active restraint", "tender fluency"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as affectionate recognition of imperfect apology and repair language",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_fifty_fifty_care_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Love is not always 50-50.",
        "\"Rehne do\" can mean tired.",
        "Paani was never the point.",
        "He notices before counting.",
        "Love carries the heavier half.",
    ]
    visuals = [
        "Warm kitchen/dining corner with a tiny half-erased 50/50 chore chart on the fridge; Aachu and Zuv look at it with tired amusement, making the chart evidence rather than the hero.",
        "Aachu near a small domestic mess: an empty water bottle, one cup, and a soft laundry edge in the background; she is expressive and dramatic-but-soft, with a small speech bubble saying rehne do.",
        "Close domestic proof beat: the empty bottle/glass sits between them, but Aachu's face shows the real feeling is wanting to be noticed before she has to ask again.",
        "Zuv quietly fills the bottle or starts the small task with sleeves rolled, warm face, no speech, and no scorekeeping energy; Aachu watches, half-protesting and half-softened.",
        "Night, warm lamp, imperfect lived-in home, one unfinished basket still nearby; Aachu and Zuv sit shoulder-to-shoulder, showing that the chores are not perfectly done but nobody is alone.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["recognition", "dramatic tiredness", "hidden request", "quiet care", "tender reciprocity"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as a tender proof that love notices when someone's half is heavier",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "rehne do" if source_index == 1 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_food_denial_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He married \"I'm not hungry.\"",
        "Then she took one bite.",
        "Then the best bite.",
        "So he orders extra now.",
        "Love knows your order anyway.",
    ]
    visuals = [
        "A warm desi cafe or dining-table scene: Aachu playfully pushes the menu away with expressive not-hungry confidence while Zuv watches with a soft knowing smile; food is present as evidence, not the premise.",
        "Aachu reaches across for one small bite from Zuv's plate with dramatic innocence; Zuv slides the plate closer instead of guarding it, amused and fully used to this pattern.",
        "Close comic proof beat: Aachu's fork takes the best bite from Zuv's plate while a tiny speech bubble says bas ek bite; her face is caught between mischief and softness.",
        "Zuv quietly orders an extra plate or side before she has to admit anything, calm hand raised to the waiter/counter, while Aachu looks half-protesting and half-loved.",
        "Both sit close with two plates between them, one bite already shared, the table messy-warm and human; the final feeling is that being known is more romantic than keeping score.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["instant recognition", "playful denial", "comic proof", "quiet knowing care", "tender belonging"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners tag the person who says they are not hungry and then eats the best bite",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "bas ek bite" if source_index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_wallet_audit_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some wives don't ask. They audit wallets.",
        "She said, \"bas 500.\"",
        "Then checked the backup pocket.",
        "He saw. He pretended to sleep.",
        "By morning, he kept extra there.",
        "Love is when your nonsense has a budget.",
    ]
    visuals = [
        "Warm ordinary bedroom or couch scene in open daylight: Aachu/Nancho enters the frame with mock-official audit energy while Zuv/Himanshu rests nearby with wallet visible; the mood is affectionate, bright, mutually understood, and playful.",
        "Aachu/Nancho holds one small note with innocent bas-500 expression; Zuv/Himanshu is visible in the background with one eye open, amused and aware.",
        "Close comic proof beat: the wallet opens wider and Aachu/Nancho checks one backup pocket with exaggerated household-auditor seriousness; keep the cash amount tiny, no money-flex pile.",
        "Zuv/Himanshu clearly notices and chooses to participate: he gently closes his eye again with an amused half-smile and subtly points toward the real backup pocket, fully in on the bit.",
        "Morning domestic frame: Zuv/Himanshu has quietly placed a little extra cash in the wallet or drawer; Aachu/Nancho notices with a tiny victorious smile and soft surprise.",
        "Both together in an airy warm-paper frame: Aachu/Nancho holds the tiny household budget like an official file while Zuv/Himanshu looks fondly defeated and amused; the thesis lands as shared couple language, not money drama.",
    ]
    roles = [
        "universal hook",
        "aachu-specific reveal",
        "comic escalation",
        "zuv active role",
        "emotional reversal",
        "save/share thesis",
    ]
    emotions = [
        "instant comic recognition",
        "mischievous innocence",
        "playful escalation",
        "active fond complicity",
        "quiet care",
        "taggable tenderness",
    ]
    if slide_count == 4:
        selected = [0, 2, 3, 5]
    elif slide_count == 5:
        selected = [0, 1, 3, 4, 5]
    else:
        selected = list(range(min(slide_count, len(copies))))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners tag the person whose tiny nonsense has become part of the household budget",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 5} else "bottom_center",
                "speech_bubble": "bas 500" if source_index == 1 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_suitcase_relocation_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some couples don't pack. They relocate the house.",
        "She packed \"just options.\"",
        "He packed every charger except the one they needed.",
        "They sat on the suitcase.",
        "Still forgot toothbrushes.",
        "Nobody blamed each other. Only the zip.",
        "Maybe love is two overpackers blaming the zip.",
    ]
    visuals = [
        "Home bedroom packing room act, wide opening frame: Aachu and Zuv stand on opposite sides of the open suitcase, both proudly surrounded by absurd but believable trip piles; folded clothes, pouch, cables, shoes, and toiletries are visible while both look convinced this is normal.",
        "Home bedroom packing room act: Aachu kneels beside the suitcase holding three outfit options against herself, with the same folded outfit stack and scarf nearby; Zuv watches from the floor with an amused side-eye, hands paused over his own packing pile.",
        "Home bedroom packing room act: Zuv sits seriously with a tangle of real phone chargers, adapters, earphones, and a power bank, looking confident; Aachu leans in with a judging look while the one needed phone cable is clearly missing from the pile.",
        "Home bedroom packing room act: both Aachu and Zuv sit on top of the bulging suitcase together, knees up and hands gripping the edges, trying to zip it with full teamwork while the suitcase pushes back.",
        "Destination arrival bathroom corner: Aachu and Zuv, still in the same travel-day outfits, stand beside the open dark olive suitcase and stare at the cream toiletry pouch and empty toothbrush cup; the empty toothbrush slots are clearly visible after arrival.",
        "Destination arrival room: both point at the stubborn suitcase zip with offended innocent faces, standing shoulder to shoulder beside the same open suitcase so the blame lands on the zip instead of either person.",
        "Destination arrival room, soft final floor scene: Aachu and Zuv sit beside the half-closed suitcase, tired and laughing, one hand from each still resting near the zip; the mess feels shared, affectionate, and chosen.",
    ]
    roles = [
        "universal hook",
        "aachu-specific proof",
        "zuv-specific proof",
        "comic escalation",
        "reversal",
        "bridge",
        "save/share thesis",
    ]
    emotions = [
        "instant recognition",
        "playful denial",
        "mutual judgment",
        "physical comedy",
        "silent realization",
        "shared delusion",
        "tender laughter",
    ]
    if slide_count == 4:
        selected = [0, 2, 3, 6]
    elif slide_count == 5:
        selected = [0, 1, 2, 3, 6]
    else:
        selected = list(range(min(slide_count, len(copies))))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": (
                f"{SUITCASE_RELOCATION_HOME_VISUAL_LOCK if source_index < 4 else SUITCASE_RELOCATION_DESTINATION_VISUAL_LOCK} "
                f"{visuals[source_index]}"
            ),
            "emotion": emotions[source_index],
            "cta_intent": "make partners tag the person who overpacks with them and still blames the suitcase zip",
            "continuity_lock": SUITCASE_RELOCATION_CONTINUITY_LOCK,
            "wardrobe": SUITCASE_RELOCATION_WARDROBE_LOCK,
            "props": SUITCASE_RELOCATION_PROP_LOCK,
            "background": SUITCASE_RELOCATION_BACKGROUND_LOCK,
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 2, 6} else "bottom_center",
                "speech_bubble": "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_tasty_life_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Woh bas \"khaya?\" nahi poochta.",
        "Woh \"aur logi?\" bolta hai.",
        "The second serving wasn't just food.",
        "No comments. Just comfort.",
        "Wanting started feeling safe.",
        "55 se 70 nahi.\nBas life zyada tasty ho gayi.",
    ]
    visuals = [
        "Warm home threshold between living room and kitchen: Aachu looks a little guarded while Zuv quietly sets two plates without making food a topic; no scale, no body joke, home only.",
        "Kitchen counter or couch table: Zuv gently offers a normal second serving with an 'aur logi?' energy; Aachu chooses it with a small smile, never pressured.",
        "Shared plate in warm home light: the second serving becomes a relaxed laugh and easy closeness, food visible as emotional evidence rather than quantity.",
        "Comfort proof scene: Zuv moves clutter aside, brings blanket or water with the plate, and sits beside Aachu; no teasing, no body focus, no counting.",
        "Aachu relaxes into the home, reaching comfortably and laughing without guarded posture while Zuv stays present and gentle; wanting feels safe.",
        "Wide warm home payoff: kitchen glow, two plates, soft lived-in mess, shared laughter, relaxed bodies; the number lands as life becoming tastier, not body comparison.",
    ]
    roles = ["universal hook", "food bridge", "proof escalation", "active care", "emotional turn", "save/share thesis"]
    emotions = [
        "recognition",
        "warm offer",
        "bridge",
        "active acceptance",
        "safe wanting",
        "affectionate payoff",
    ]
    if slide_count == 4:
        selected = [0, 2, 4, 5]
    elif slide_count == 5:
        selected = [0, 1, 2, 3, 5]
    else:
        selected = list(range(min(slide_count, len(copies))))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this to the person who made food feel like comfort, not calculation",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_morning_person_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He didn't marry a morning person.",
        "\"5 more minutes\" is not a time. It's a boundary.",
        "Grumpy. Hungry. Suddenly cute.",
        "So he learned: chai first, questions later.",
        "Maybe love is knowing when not to talk.",
    ][:slide_count]
    visuals = [
        "Aachu wrapped in a blanket, hair messy, refusing the morning light while Zuv opens the curtain very gently.",
        "Aachu half-hidden under the blanket with the phone alarm face-down; Zuv stands nearby holding chai like a peace offering.",
        "Three tiny Aachu morning moods around one breakfast plate: grumpy, hungry, suddenly soft; Zuv waits with a calm smile.",
        "Zuv quietly places chai beside Aachu before saying anything; her face starts softening in warm morning light.",
        "Aachu leans on Zuv with two chai cups nearby, both sitting in calm morning silence after the storm has passed.",
    ][:slide_count]
    roles = ["universal hook", "special revelation", "proof beat", "emotional turn", "save/share thesis"][:slide_count]
    emotions = ["sleepy rupture", "comic recognition", "affectionate chaos", "quiet care", "tender acceptance"][:slide_count]
    source_groups = distribute_sources(image_paths, slide_count)
    return [
        {
            "slide": index,
            "copy": copy,
            "role": roles[index - 1],
            "visual": visuals[index - 1],
            "emotion": emotions[index - 1],
            "cta_intent": "make couples send this as affectionate recognition of morning chaos",
            "text_layout": {
                "primary_position": "top_center",
                "speech_bubble": "5 more\nminutes" if index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]


def build_waterfall_lantern_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some days become a whole chapter.",
        "First, the world went big.",
        "Then the night came closer.",
        "Same two people. Different kind of magic.",
        "Maybe home is whoever makes every place feel like us.",
    ][:slide_count]
    visuals = [
        "Aachu and Zuv stand together in front of the tan rock waterfall, keeping the pale shirts, denim, grey trousers, red bag, red shoes, and easy smiles from the daylight reference photo.",
        "A wide illustrated waterfall frame where the rocks and thin streams feel huge around them, with Aachu's red bag and shoes as tiny bright anchors.",
        "A close lantern-night frame from the bamboo hut selfie: warm woven pendant lamps overhead, blue evening glow, Zuv tucked behind Aachu, both smiling softly in white shirts.",
        "A split-memory composition that rhymes the two references: waterfall daylight on one side, bamboo lantern night on the other, with Aachu and Zuv drawn as the same recurring couple.",
        "A quiet final frame with the couple small together under warm lantern light, a faint waterfall motif in the background, and the place fading behind the feeling of being together.",
    ][:slide_count]
    roles = ["cover hook", "scale proof", "private turn", "memory bridge", "saveable thesis"][:slide_count]
    emotions = ["archive wonder", "bright joy", "soft closeness", "recognition", "tender settledness"][:slide_count]
    source_groups = distribute_sources(image_paths, slide_count)
    if image_paths:
        source_groups = []
        for index in range(1, slide_count + 1):
            if index in {1, 2}:
                source_groups.append([str(image_paths[-1])])
            elif index == 3:
                source_groups.append([str(image_paths[0])])
            else:
                source_groups.append([str(path) for path in image_paths])
    return [
        {
            "slide": index,
            "copy": copy,
            "role": roles[index - 1],
            "visual": visuals[index - 1],
            "emotion": emotions[index - 1],
            "cta_intent": "make couples save or send this as a place-to-memory love note",
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]


def build_photo_ritual_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        'Har trip mein ek "bas ek photo aur" person hota hai.',
        "Humare mein, obviously Aachu.",
        "Zuv? Full patience mode: haan baba.",
        "Waterfall ho ya lantern light, ritual same.",
        "Pyaar shayad wahi hai: memories ko ours bana dena.",
    ]
    visuals = [
        "A wide warm illustrated trip scene with tan waterfall rocks, pale shirts, red bag, and red shoes from the references; Aachu is already looking for one more frame while a small thought bubble says 'last one, promise' and Zuv smiles patiently.",
        "Aachu as the memory-maker, leaning in with red bag and red shoes, checking the angle with playful certainty; a small thought bubble says 'yeh angle cute hai' while Zuv stands close and amused.",
        "Zuv in calm patience mode, standing ready for one more photo with relaxed shoulders and a warm smile; Aachu points toward the frame and his tiny speech bubble says 'haan baba'.",
        "A split-memory composition: daylight waterfall on one side, warm lantern selfie on the other, same couple, same white shirts, red accents, and easy closeness; tiny thought bubbles say 'ek aur?' and 'always'.",
        "A quiet final frame under warm lantern light: Aachu and Zuv close together, phone lowered, the place fading into warm paper; one tiny shared bubble says 'apna moment'.",
    ]
    roles = ["universal hook", "specific revelation", "proof beat", "emotional turn", "save/share thesis"]
    emotions = ["playful recognition", "specific sparkle", "patient proof", "soft pattern recognition", "tender thesis"]
    if slide_count == 4:
        selected = [0, 1, 2, 4]
    else:
        selected = list(range(slide_count))

    if image_paths:
        source_groups = []
        for source_index in selected:
            if source_index in {0, 1, 2}:
                source_groups.append([str(image_paths[0])])
            elif source_index == 3:
                source_groups.append([str(path) for path in image_paths])
            else:
                source_groups.append([str(image_paths[-1])])
    else:
        source_groups = [[] for _ in selected]

    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make couples send this as an affectionate memory-making ritual",
            "text_layout": {
                "primary_position": "top_center" if index in {1, 2, 5} else "bottom_center",
                "speech_bubble": {
                    0: "last one, promise",
                    1: "yeh angle cute hai",
                    2: "haan baba",
                    3: "ek aur? always",
                    4: "apna moment",
                }[source_index],
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_kashmiri_language_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some people become the inside joke.",
        "Aachu brought the Kashmiri tone.",
        "Zuv learned the vibe first.",
        "Same funny tone. Parents included.",
        "Love is trying to belong.",
    ]
    visuals = [
        "A universal family-room hook: Aachu and her parents laughing warmly while Zuv stands in the room with a calm, slightly proud smile, clearly becoming the affectionate inside joke rather than an outsider.",
        "Aachu saying a Kashmiri word with expressive eyebrows, hand gesture, and amused drama; her words feel like tone, face, family warmth, and home around her.",
        "Zuv collecting the phrases like family passwords: one or two tiny playful speech bubbles such as Ursu ursu and Namaskar mahara, kept secondary rather than text-heavy; he repeats them in the same funny tone with gentle confidence.",
        "Zuv using the phrase with Aachu's parents, committed and respectful despite the questionable accent, clearly trying to join the room; Aachu is laughing with a please-stop-but-don't-stop expression.",
        "A tender final family-table moment where her people laugh warmly, Aachu looks soft and proud, and Zuv's calm effort makes her world feel chosen.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["playful recognition", "warm cultural spark", "comic proof", "belonging effort", "tender family acceptance"]
    selected = [0, 1, 2, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as a funny but tender proof of trying to belong in someone's world",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "same funny tone" if source_index == 3 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_subtitle_language_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Some people come with subtitles.",
        "Aachu's face says everything first.",
        'Her mouth says: "kuch nahi."',
        "Zuv knows the translation.",
        "Maybe love is learning the subtitles.",
    ]
    visuals = [
        "A universal relationship hook: Aachu stands with arms crossed, lovingly dramatic and clearly not fine, while tiny airy handwritten subtitle fragments float near her expression.",
        "Aachu's expressive face carries the full paragraph before she says a word; tiny floating subtitles read hungry, sleepy, offended, missing you, wants chai, kept secondary and readable.",
        "Aachu turns slightly away with one tiny tear, phone or dupatta held like an emotion prop, while a small speech bubble says kuch nahi.",
        "Zuv quietly arrives with chai, snack, tissue, and water, smiling like he already understood the whole mood translation without making a scene.",
        "Aachu and Zuv sit close together after the mood has softened; the tiny subtitles fade into one warm shared language between them.",
    ]
    roles = ["universal hook", "aachu-specific reveal", "concrete proof", "zuv role", "save/share thesis"]
    emotions = ["playful recognition", "expressive specificity", "soft drama", "quiet care", "tender acceptance"]
    selected = [0, 1, 3, 4] if slide_count == 4 else list(range(slide_count))
    source_groups = distribute_sources(image_paths, len(selected)) if image_paths else [[] for _ in selected]
    return [
        {
            "slide": index,
            "copy": copies[source_index],
            "role": roles[source_index],
            "visual": visuals[source_index],
            "emotion": emotions[source_index],
            "cta_intent": "make partners send this as affectionate recognition of learning each other's unspoken moods",
            "text_layout": {
                "primary_position": "top_center" if source_index in {0, 1, 4} else "bottom_center",
                "speech_bubble": "kuch nahi" if source_index == 2 else "",
            },
            "source_images": source_groups[index - 1],
        }
        for index, source_index in enumerate(selected, start=1)
    ]


def build_workday_homecoming_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Maybe Chaos Is Also Home",
            "universal_truth": "After a draining day, the right person is not always quiet; sometimes their lovable chaos is the safe landing.",
            "aachu_specific_spark": "Aachu waiting with chai, drama, and one long story.",
            "concrete_proof": "Zuv in the parked car, phone lighting up with ghar aa jao?, and his face softening before he drives.",
            "zuv_role": "He chooses the warm noise instead of escaping into silence.",
            "tender_thesis": "Maybe chaos is also home.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "Some Days Need Her Noise",
            "universal_truth": "The day makes him crave quiet, but love has taught him which noise heals him.",
            "aachu_specific_spark": "Her voice note, chai, and running commentary become the reward at the end of work.",
            "concrete_proof": "Tired car seat, phone notification, voice note bubble, soft smile.",
            "zuv_role": "His smile is the active choice to return to her world.",
            "tender_thesis": "Some noise brings you back to yourself.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4,
                "zuv_emotional_role": 4,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 28,
        },
        {
            "name": "His Smile Started Before Home",
            "universal_truth": "Sometimes love begins helping before you even reach the door.",
            "aachu_specific_spark": "Aachu's tiny text and waiting-at-home warmth reach him inside the car.",
            "concrete_proof": "The smile arrives before the drive starts.",
            "zuv_role": "He lets himself be softened by the thought of her.",
            "tender_thesis": "Home can start in the heart before the house.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 28,
        },
        {
            "name": "The Phone Changed The Car",
            "universal_truth": "One message can make the whole day feel survivable.",
            "aachu_specific_spark": "Aachu's ghar aa jao? carries care, impatience, and soft drama.",
            "concrete_proof": "Phone glow in a parked car after office.",
            "zuv_role": "He receives the care and decides to go home lighter.",
            "tender_thesis": "The smallest message can become a doorway.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 27,
        },
        {
            "name": "Chai Before The Debrief",
            "universal_truth": "Some people know how to receive your tiredness before asking for the story.",
            "aachu_specific_spark": "Aachu has chai ready and still has her own full story waiting.",
            "concrete_proof": "Doorway, two cups, his office bag, her expressive waiting face.",
            "zuv_role": "He lets home hold him without needing to explain everything first.",
            "tender_thesis": "Love is knowing where the day can finally exhale.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 5,
                "share_send_potential": 4,
            },
            "total": 27,
        },
        {
            "name": "Bad Day, Good Door",
            "universal_truth": "A bad day feels smaller when the right door is waiting.",
            "aachu_specific_spark": "Aachu is behind the door with warmth, chai, and small chaos.",
            "concrete_proof": "Office bag at the threshold, keys, slippers, two cups.",
            "zuv_role": "He returns to the place where he can stop performing.",
            "tender_thesis": "The right door is a person.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 4,
                "zuv_emotional_role": 4,
                "tender_thesis": 4,
                "share_send_potential": 4,
            },
            "total": 24,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Maybe Chaos Is Also Home",
        "winner_score": 29,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the gold carousel machine while shifting into Himanshu POV: "
            "the universal tension is wanting silence after work, the Aachu proof is chai/drama/one long story, "
            "the Zuv role is his active smile and choice to return to that warm chaos, and the thesis is sendable."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the first-principles insight that Aachu's expressive energy becomes lovable because "
            "Zuv treats it as safety instead of noise."
        ),
        "final_public_slide_copy_direction": [
            "Some days make him want silence.",
            "Then he remembers her waiting.",
            "Chai. Drama. One long story.",
            "And he smiles before home.",
            "Maybe chaos is also home.",
        ],
        "candidates": candidates,
    }


def build_high_maintenance_care_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "She Was Not High-Maintenance",
            "universal_truth": "The right person does not make your little needs feel like a burden.",
            "aachu_specific_spark": "Aachu fully alive in a green dress, barefoot, soft, and slightly impractical.",
            "concrete_proof": "Zuv kneeling on the Ayatana balcony to help with footwear before she asks.",
            "zuv_role": "He notices the tiny discomfort early and turns it into gentle care.",
            "tender_thesis": "Love is care without asking someone to shrink.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29.5,
        },
        {
            "name": "Main Character, Little Details",
            "universal_truth": "Some people bring the whole scene; some love handles the details that keep it soft.",
            "aachu_specific_spark": "Green-dress main-character entrance on the balcony.",
            "concrete_proof": "Footwear help, steady posture, soft smile.",
            "zuv_role": "Zuv becomes the quiet detail person without making her smaller.",
            "tender_thesis": "Love is not dimming the scene; it is making it easier to live inside.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "He Noticed Before She Asked",
            "universal_truth": "The safest love notices small discomforts early.",
            "aachu_specific_spark": "Barefoot, soft, slightly impractical balcony moment.",
            "concrete_proof": "Zuv kneels, adjusts footwear, and stays close.",
            "zuv_role": "He acts before the need becomes a complaint.",
            "tender_thesis": "Maybe attention is also romance.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "She Did Not Need Less Drama",
            "universal_truth": "Expressive people do not need less feeling; they need softer care.",
            "aachu_specific_spark": "Tiny dramatic barefoot moment in a green outfit.",
            "concrete_proof": "Shoe/sandal assistance as visual proof.",
            "zuv_role": "Zuv makes the drama feel handled, not embarrassing.",
            "tender_thesis": "Love is not less chaos; it is gentler hands.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Soft Logistics",
            "universal_truth": "Romance is often the unglamorous detail that protects the beautiful moment.",
            "aachu_specific_spark": "Dressed-up balcony softness.",
            "concrete_proof": "Shoes as the practical object.",
            "zuv_role": "Zuv handles the practical detail.",
            "tender_thesis": "Love is the logistics nobody claps for.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 27,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "She Was Not High-Maintenance",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner starts from the universal shame of being called high-maintenance, "
            "uses Aachu's green-dress barefoot balcony moment as proof, keeps Zuv's care active, "
            "and preserves the gold theme by making the small need safe instead of burdensome."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the first-principles machine: universal anti-ideal -> expressive Aachu proof -> "
            "Zuv's active steady care -> tender acceptance thesis."
        ),
        "final_public_slide_copy_direction": [
            "She was not high-maintenance.",
            "She was just fully alive.",
            "Bare feet. Green dress. Tiny crisis.",
            "He noticed before she asked.",
            "Maybe love is care without shrinking.",
        ],
        "candidates": candidates,
    }


def build_main_kar_lungi_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Main Kar Lungi",
            "universal_truth": "Some independent people are not saying leave me alone; they are saying help me without making me feel small.",
            "aachu_specific_spark": "Aachu's full-pride 'main kar lungi' carries a hidden please stay close.",
            "concrete_proof": "An outdoor public threshold, her determined posture, and Zuv helping so quietly the moment stays hers.",
            "zuv_role": "He reads the translation and offers care without turning it into a scene.",
            "tender_thesis": "Maybe love is care without making a scene.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29.5,
        },
        {
            "name": "Help Without Shrinking",
            "universal_truth": "The right help does not reduce someone's independence.",
            "aachu_specific_spark": "Aachu wants to do the moment herself, but wants Zuv near.",
            "concrete_proof": "He opens the path, steadies one small thing, and lets her lead.",
            "zuv_role": "His care protects her pride instead of correcting her.",
            "tender_thesis": "Maybe love is help that leaves your pride whole.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Don't Go Far",
            "universal_truth": "Sometimes independence is not distance; it is trust that someone will stay close.",
            "aachu_specific_spark": "Her sentence says I can do it, but the rhythm says stay here.",
            "concrete_proof": "A glance back on an outdoor path, Zuv close enough without crowding her.",
            "zuv_role": "He respects both messages at once.",
            "tender_thesis": "Love knows when close is enough.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 28.5,
        },
        {
            "name": "The Quiet Hand",
            "universal_truth": "Care lands deepest when it does not announce itself.",
            "aachu_specific_spark": "Aachu keeps her main-character pride while Zuv quietly solves the tiny practical edge.",
            "concrete_proof": "One easy hand at the gate or bag, then both keep walking.",
            "zuv_role": "He helps without taking over the scene.",
            "tender_thesis": "Maybe attention is love before it becomes a request.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "Pride Stayed Whole",
            "universal_truth": "Being loved well can make independence feel safer, not threatened.",
            "aachu_specific_spark": "Her determined softness remains the center of the moment.",
            "concrete_proof": "Outdoor movement, respectful distance, and one tiny assist.",
            "zuv_role": "He makes the help feel like partnership, not rescue.",
            "tender_thesis": "Maybe love is being helped and still feeling like yourself.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 4,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 27.5,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles and Layer E story-selling cards.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Main Kar Lungi",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the spine the creator chose while correcting the visual failure: "
            "the premise is the universal double-message of independent love, Aachu's proof is "
            "the proud 'main kar lungi', Zuv's role is active but quiet care, and the visuals stay outdoors."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold carousel machine: expressive Aachu anti-ideal -> concrete pride proof -> "
            "Zuv's calm active care -> tender acceptance thesis."
        ),
        "story_selling_card": "Card 13 - The Way He Stays",
        "final_public_slide_copy_direction": [
            "Main kar lungi.",
            "Translation: don't go far.",
            "She wanted to do it herself.",
            "He helped like it was nothing.",
            "Maybe love is care without making a scene.",
        ],
        "candidates": candidates,
    }


def build_fifty_fifty_care_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "The Heavier Half",
            "universal_truth": "Love is not perfect accounting; it is noticing when someone's half has become heavier today.",
            "aachu_specific_spark": "Aachu's small rehne-do irritation carries the tiredness of having to notice everything first.",
            "concrete_proof": "The empty water bottle becomes the receipt, but not the premise.",
            "zuv_role": "Zuv does not debate whose turn it was; he notices and acts before the moment becomes a case.",
            "tender_thesis": "Love carries the heavier half.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29.5,
        },
        {
            "name": "Noticed Before Asked",
            "universal_truth": "Fifty-fifty sounds fair until someone has to ask for the same small thing twice.",
            "aachu_specific_spark": "Aachu's visible annoyance is the softer wish to be noticed sooner.",
            "concrete_proof": "The bottle stays empty again, turning a small task into a recognizable couple scene.",
            "zuv_role": "He fills it without speeches or scorekeeping.",
            "tender_thesis": "Love notices before being asked.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 29,
        },
        {
            "name": "She Did Not Want Help",
            "universal_truth": "Sometimes help is not the need; being seen before asking is the need.",
            "aachu_specific_spark": "Aachu says rehne do, but the feeling underneath is please notice the room with me.",
            "concrete_proof": "A small domestic mess, an empty bottle, and her expressive face create the proof.",
            "zuv_role": "He reads the hidden request and starts quietly.",
            "tender_thesis": "He did not help because she asked; he helped because he saw.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29,
        },
        {
            "name": "The Invisible List",
            "universal_truth": "Not every half feels fair when one person is carrying the list nobody sees.",
            "aachu_specific_spark": "Aachu remembers sab kuch: bottle, socks, salt, tiny plans, tiny resets.",
            "concrete_proof": "A few simple home details show the invisible load without becoming a chore inventory.",
            "zuv_role": "He starts learning the invisible list instead of waiting to be assigned.",
            "tender_thesis": "Fairness begins with noticing.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 27.5,
        },
        {
            "name": "No Ledger Love",
            "universal_truth": "Marriage is not a ledger when love is trying to protect softness, not win math.",
            "aachu_specific_spark": "Aachu turns one tiny imbalance into affectionate courtroom energy.",
            "concrete_proof": "One sock or one glass becomes Exhibit A.",
            "zuv_role": "He does the tiny thing smiling instead of arguing the score.",
            "tender_thesis": "Love returns effort softly.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 26.5,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles and Layer E story-selling cards.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "The Heavier Half",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the creator-preferred 50-50 thought while repairing the advice risk: "
            "the premise is fairness versus felt care, Aachu's proof is a tiny domestic irritation "
            "that reveals the hidden wish to be noticed, Zuv's role is active noticing before counting, "
            "and the final thesis is tender enough to send."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold carousel machine: universal anti-ideal -> expressive Aachu proof -> "
            "Zuv's calm active care -> tender acceptance thesis, while rotating away from repeated chaos/home language."
        ),
        "story_selling_card": "Card 07 - Anti-Ideal To Real Love",
        "final_public_slide_copy_direction": [
            "Love is not always 50-50.",
            "\"Rehne do\" can mean tired.",
            "Paani was never the point.",
            "He notices before counting.",
            "Love carries the heavier half.",
        ],
        "candidates": candidates,
    }


def build_wallet_audit_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Wallet Audit Love",
            "universal_truth": "The best couples do not only tolerate each other's nonsense; they quietly budget for it.",
            "aachu_specific_spark": "Aachu/Nancho treats a tiny wallet raid like household finance ministry work.",
            "concrete_proof": "Bas 500, the backup pocket, the caught-but-not-stopped moment, and the extra cash by morning.",
            "zuv_role": "Zuv/Himanshu sees everything, pretends to sleep, points to the backup pocket, and prepares for her next bit.",
            "tender_thesis": "Love is when your nonsense has a budget.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 30,
        },
        {
            "name": "Finance Minister At Home",
            "universal_truth": "Every couple has one finance minister and one person pretending not to notice.",
            "aachu_specific_spark": "Aachu/Nancho audits pockets with affectionate authority.",
            "concrete_proof": "One note becomes a backup-pocket inspection.",
            "zuv_role": "Zuv/Himanshu turns the audit into a shared ritual by enabling it without speeches.",
            "tender_thesis": "Love makes room for tiny household nonsense.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "He Pretended To Sleep",
            "universal_truth": "Sometimes love is not stopping the bit; it is joining quietly.",
            "aachu_specific_spark": "Aachu/Nancho thinks the wallet moment is hers, but her expression gives the whole game away.",
            "concrete_proof": "Zuv/Himanshu opens one eye, closes it again, and points to the pocket.",
            "zuv_role": "He chooses fond complicity over correction.",
            "tender_thesis": "Love is becoming the alibi.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against the reach-recovery brief and Layer E story-selling card.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Wallet Audit Love",
        "winner_score": 30,
        "decision": "GO",
        "selector_verdict": (
            "Winner starts from a public couple truth, proves it with concrete Aachu/Nancho behavior, "
            "makes Zuv/Himanshu actively complicit, and keeps the money as a tiny proof object rather "
            "than the premise."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold carousel machine: universal anti-ideal -> expressive Aachu proof -> "
            "Zuv's calm active joining -> tender acceptance thesis."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "final_public_slide_copy_direction": [
            "Some wives don't ask. They audit wallets.",
            "\"Bas 500.\"",
            "Then the backup pocket.",
            "He saw and still joined the bit.",
            "By morning, extra was waiting.",
            "Love is when your nonsense has a budget.",
        ],
        "candidates": candidates,
    }


def build_suitcase_relocation_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Blame The Zip, Not Each Other",
            "universal_truth": "Some couples do not pack light; they create the mess together and choose a harmless villain instead of blaming each other.",
            "aachu_specific_spark": "Aachu packs 'just options' with full confidence because every possible version of the trip needs a look.",
            "concrete_proof": "The outfit pile, the cable pile with the needed charger missing, both sitting on the suitcase, forgotten toothbrushes, and the zip getting blamed.",
            "zuv_role": "Zuv is equally guilty: he overprepares the tech pile, joins the suitcase wrestling, and stands with her against the zip instead of correcting her.",
            "tender_thesis": "Love is shared ridiculousness without shame: blame the zip, not each other.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 30,
        },
        {
            "name": "Two People Carry Their What-Ifs",
            "universal_truth": "Some couples overpack because they are really packing every tiny what-if.",
            "aachu_specific_spark": "Aachu carries outfit options for moods, weather, photos, and emergency confidence.",
            "concrete_proof": "Multiple outfits, medicine pouch, extra scarf, charger mess, and the missing toothbrush reversal.",
            "zuv_role": "Zuv makes room for her what-ifs while bringing his own, so the suitcase becomes mutual comfort instead of one-person chaos.",
            "tender_thesis": "Love is making room for each other's just-in-case.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 30,
        },
        {
            "name": "Packing Light Was A Lie",
            "universal_truth": "Every trip starts with 'we will pack light' and ends with a suitcase negotiation.",
            "aachu_specific_spark": "Aachu's options make the suitcase dramatic before the trip even starts.",
            "concrete_proof": "Outfit options, adapters, sitting on the bag, forgotten toothbrushes.",
            "zuv_role": "Zuv participates in the lie and the negotiation instead of becoming the sensible outside observer.",
            "tender_thesis": "Love is committing to the same little lie together.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 28.5,
        },
    ]
    return {
        "source": "Golden Theme variant tournament and post-review repair for Suitcase Relocation.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Blame The Zip, Not Each Other",
        "winner_score": 30,
        "decision": "GO",
        "selector_verdict": (
            "Winner preserves the creator's both-guilty reset: both people make the packing mess, "
            "both participate in the physical suitcase proof, and the emotional choice is blaming the zip "
            "instead of each other. The rejected stale gadget joke is banned."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold-machine lesson while intentionally avoiding the perfect-husband engine: "
            "universal couple mess -> Aachu options proof -> Zuv's equally real overpacking proof -> "
            "shared physical comedy -> harmless-villain tenderness."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "screenplay_pattern": (
            "packing-room pride -> mutual overpacking receipts -> suitcase wrestling -> forgotten essentials -> "
            "zip blame -> shared ridiculousness payoff"
        ),
        "final_public_slide_copy_direction": [
            "Some couples don't pack. They relocate the house.",
            "She packed \"just options.\"",
            "He packed every charger except the one they needed.",
            "They sat on the suitcase.",
            "Still forgot toothbrushes.",
            "Nobody blamed each other. Only the zip.",
            "Maybe love is two overpackers blaming the zip.",
        ],
        "candidates": candidates,
    }


def build_food_denial_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "He Married I'm Not Hungry",
            "universal_truth": "Some people say they do not want food, then become very committed to the best bite.",
            "aachu_specific_spark": "Aachu's not-hungry face lasts exactly until Zuv's plate arrives.",
            "concrete_proof": "One bite, then the best bite, then half the plate quietly becoming hers.",
            "zuv_role": "Zuv does not tease her into admitting it; he orders extra like he already knows the ending.",
            "tender_thesis": "Love knows your order anyway.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29.5,
        },
        {
            "name": "Bas Ek Bite",
            "universal_truth": "Bas ek bite is rarely one bite in love.",
            "aachu_specific_spark": "Aachu says the smallest possible request with the most obvious food-interest face.",
            "concrete_proof": "The fork travels from one polite bite to the best part of Zuv's plate.",
            "zuv_role": "He slides the plate closer without making her perform the whole confession.",
            "tender_thesis": "Love leaves room on the plate.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "The Extra Plate",
            "universal_truth": "The right person starts ordering for the version of you that will be hungry in five minutes.",
            "aachu_specific_spark": "Aachu's no-thank-you softens the moment the food appears.",
            "concrete_proof": "Two plates on the table even though only one person claimed hunger.",
            "zuv_role": "He quietly creates abundance before she has to reverse her answer.",
            "tender_thesis": "Love makes space for the maybe.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "Not Hungry Until Yours Arrives",
            "universal_truth": "Some people are not hungry until your plate looks better than their decision.",
            "aachu_specific_spark": "Aachu's denial becomes mischief as soon as Zuv starts eating.",
            "concrete_proof": "Her fork entering the frame while his hand pauses mid-bite.",
            "zuv_role": "He laughs softly and lets the bite become a ritual instead of a fight.",
            "tender_thesis": "Love shares the better bite.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4,
                "share_send_potential": 5,
            },
            "total": 28,
        },
        {
            "name": "Plate Scorekeeping",
            "universal_truth": "Food math is not real math when love is involved.",
            "aachu_specific_spark": "Aachu insists it was only one bite with deeply unconvincing innocence.",
            "concrete_proof": "The plate has visibly changed sides while the couple is still pretending it did not.",
            "zuv_role": "Zuv lets the joke stay affectionate, not prosecutorial.",
            "tender_thesis": "Some scores are better lost.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 4,
                "tender_thesis": 4,
                "share_send_potential": 4,
            },
            "total": 25,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles and creator shareability feedback.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "He Married I'm Not Hungry",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner is deliberately partner-tag first: the hook names a universal couple behavior, "
            "Aachu's proof is the not-hungry to best-bite switch, Zuv's role is active knowing care, "
            "and the final line is sendable without private context."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold carousel machine: universal anti-ideal -> expressive Aachu proof -> "
            "Zuv's calm active care -> tender acceptance thesis, while using food as a behavioral receipt."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "final_public_slide_copy_direction": [
            "He married \"I'm not hungry.\"",
            "Then she took one bite.",
            "Then the best bite.",
            "So he orders extra now.",
            "Love knows your order anyway.",
        ],
        "candidates": candidates,
    }


def build_tasty_life_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "The Second Serving Was Never Just Food",
            "universal_truth": "The right love turns wanting into comfort instead of calculation.",
            "aachu_specific_spark": "Aachu's guarded food language softens when home makes one more bite feel normal, playful, and safe.",
            "concrete_proof": "A warm kitchen, an 'aur logi?' offer, a second serving, and no comments.",
            "zuv_role": "Zuv offers comfort without watching, counting, teasing, or turning appetite into a body topic.",
            "tender_thesis": "55 se 70 nahi. Bas life zyada tasty ho gayi.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.7,
            },
            "total": 29.7,
        },
        {
            "name": "Home Never Counted Her Bites",
            "universal_truth": "The right love turns food from calculation into comfort, so enjoying life stops feeling like something to negotiate.",
            "aachu_specific_spark": "Aachu stops guarding every bite with 'bas thoda sa' and lets her appetite become playful, visible, and loved.",
            "concrete_proof": "A home kitchen counter, a shared couch plate, and Zuv saving the best bite for her before she asks.",
            "zuv_role": "Zuv makes comfort active by never counting, never teasing the number, and quietly keeping the best bite for her.",
            "tender_thesis": "55 se 70 nahi. Bas life zyada tasty ho gayi.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29.5,
        },
        {
            "name": "The Best Bite Was A Promise",
            "universal_truth": "Sometimes care is the person who saves the best part for you without making you ask.",
            "aachu_specific_spark": "Aachu's 'bas thoda sa' begins as guardedness and turns into comfortable mischief.",
            "concrete_proof": "The best bite stays on Zuv's side of the plate only until he slides it toward her.",
            "zuv_role": "Zuv protects the softness by making her wanting more feel normal.",
            "tender_thesis": "Love makes one more bite feel safe.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Food Became Comfort, Not Calculation",
            "universal_truth": "The softest home is the one where appetite is not audited.",
            "aachu_specific_spark": "Aachu stops making every bite sound small and starts letting the room see her ease.",
            "concrete_proof": "Kitchen snacks, couch laughter, and one shared plate with no invisible scorecard.",
            "zuv_role": "Zuv removes the calculation by responding with care instead of commentary.",
            "tender_thesis": "Maybe love is a home that does not count.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "She Stopped Eating Carefully",
            "universal_truth": "Some love does not change your body first; it changes how carefully you feel you have to live.",
            "aachu_specific_spark": "Aachu's guarded 'bas thoda sa' softens into laughter, extra bites, and more room to exist.",
            "concrete_proof": "The same home table moves from tiny portion to shared snack spread.",
            "zuv_role": "Zuv makes the shift safe by offering, saving, and sharing without making it a topic.",
            "tender_thesis": "The life got bigger because the love got safer.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Bas Thoda Sa Was A Shield",
            "universal_truth": "Sometimes 'just a little' is not appetite; it is a person trying not to be watched.",
            "aachu_specific_spark": "Aachu's small phrase reveals the guardedness that home slowly dissolves.",
            "concrete_proof": "A half portion, a shared plate, and the best bite placed gently in front of her.",
            "zuv_role": "Zuv gives her privacy inside love: no counting, no public teasing, no correction.",
            "tender_thesis": "Love lets guardedness become comfort.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
    ]
    return {
        "source": "Golden Theme variant tournament repaired from creator-selected payoff line.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "The Second Serving Was Never Just Food",
        "winner_score": 29.7,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the creator-liked payoff but repairs the structure with the missing food/appetite bridge: "
            "the hook starts from home-food banter, the proof moves through a second serving and no-comment comfort, "
            "Zuv's role is active non-counting care, and the final line lands as an affectionate receipt instead of a body joke."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold machine by making Aachu's guarded appetite safe through Zuv's active care, "
            "then landing a sendable Hinglish thesis about life getting tastier."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "final_public_slide_copy_direction": [
            "Woh bas \"khaya?\" nahi poochta.",
            "Woh \"aur logi?\" bolta hai.",
            "The second serving wasn't just food.",
            "No comments. Just comfort.",
            "Wanting started feeling safe.",
            "55 se 70 nahi.\nBas life zyada tasty ho gayi.",
        ],
        "candidates": candidates,
    }


def build_pakka_reassurance_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Pakka?",
            "universal_truth": "The softest hearts need reassurance twice.",
            "aachu_specific_spark": "Aachu asks pakka even after she has already been hugged and chosen.",
            "concrete_proof": "A hug, one tiny overthink, and the same question coming back softer.",
            "zuv_role": "Zuv answers with the same warm haan baba like patience is not running out.",
            "tender_thesis": "Love is patience with your smallest doubt.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 30,
        },
        {
            "name": "Stay Before Solving",
            "universal_truth": "Some moods do not need fixing first.",
            "aachu_specific_spark": "Aachu goes quiet before she knows how to explain the feeling.",
            "concrete_proof": "A couch corner, chai, and Zuv sitting closer instead of asking too much.",
            "zuv_role": "He stays before solving, making her quiet feel safe.",
            "tender_thesis": "Maybe love is presence before advice.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29,
        },
        {
            "name": "No Questions Yet",
            "universal_truth": "Sometimes silence means come closer, not leave me alone.",
            "aachu_specific_spark": "Aachu says nothing, but the face and body language say the whole thing.",
            "concrete_proof": "A quiet lean-in, one untouched phone, and Zuv's shoulder becoming the answer.",
            "zuv_role": "He understands the request before she has to turn it into words.",
            "tender_thesis": "Maybe love is knowing when not to interrogate the feeling.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "The Snack Before The Sorry",
            "universal_truth": "Some fights are hunger wearing emotions.",
            "aachu_specific_spark": "Aachu is dramatic-angry until the plate arrives.",
            "concrete_proof": "One sulky face, one snack plate, and the mood changing before the apology.",
            "zuv_role": "Zuv reads the hunger underneath the drama and brings care first.",
            "tender_thesis": "Maybe love is feeding the feeling before arguing with it.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "One More Photo Was Never About The Photo",
            "universal_truth": "Some people turn ordinary days into proof that they mattered.",
            "aachu_specific_spark": "Aachu asks for one more photo because the moment already feels precious.",
            "concrete_proof": "Phone raised again, Aachu adjusting the angle, Zuv waiting with haan baba patience.",
            "zuv_role": "He makes room for her memory-making instead of rushing it.",
            "tender_thesis": "Maybe the ritual was being waited for.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4,
            },
            "total": 28,
        },
        {
            "name": "The Weather Report",
            "universal_truth": "Loving someone means learning their emotional weather.",
            "aachu_specific_spark": "Aachu has rain, sun, and drama before the day has properly started.",
            "concrete_proof": "Tiny weather icons around breakfast while Zuv calmly tracks the forecast.",
            "zuv_role": "He does not shame the weather; he learns how to stand in it.",
            "tender_thesis": "Maybe love is not changing the weather, just staying gentle through it.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "She Wasn't Too Much. She Was Unedited.",
            "universal_truth": "The right person does not ask you to shrink the alive parts.",
            "aachu_specific_spark": "Aachu is full-volume feeling, expressive face, sudden softness, and no filter.",
            "concrete_proof": "Three expressive mini-beats around one calm Zuv smile.",
            "zuv_role": "He loves the unedited version instead of waiting for a quieter one.",
            "tender_thesis": "Maybe love is being kept whole.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "The Backup Outfit Was A Feeling",
            "universal_truth": "Overplanning is sometimes just wanting the moment to matter.",
            "aachu_specific_spark": "Aachu packs too much because the memory already feels important.",
            "concrete_proof": "Backup outfit, small bag chaos, and Zuv carrying it without a lecture.",
            "zuv_role": "He protects the feeling underneath the overplanning.",
            "tender_thesis": "Maybe love is carrying what matters to them.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 27,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Pakka?",
        "winner_score": 30,
        "decision": "GO",
        "selector_verdict": (
            "Winner opens a fresh reassurance lane while preserving the gold carousel machine: "
            "the universal tension is needing to hear love twice, Aachu's proof is the tiny "
            "pakka overthink after closeness, Zuv's role is active repeated reassurance, and "
            "the final line is highly sendable."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the first-principles insight that Aachu's expressive inner weather becomes safe "
            "because Zuv responds with chosen steadiness instead of impatience."
        ),
        "final_public_slide_copy_direction": [
            "The softest hearts ask twice.",
            "\"Pakka?\" even after the hug.",
            "Then again, after one tiny overthink.",
            "He says \"haan baba\" like it's the first time.",
            "Maybe love is patience with your smallest doubt.",
        ],
        "candidates": candidates,
    }


def build_softness_under_fire_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Softness Under Fire",
            "universal_truth": "Some people do not say love gently when they are hurt.",
            "aachu_specific_spark": "Aachu's spice, be-safe warnings, and sudden need for closeness are all softness trying not to look soft.",
            "concrete_proof": "She says don't touch me while still holding his sleeve, and be safe lands like a warning because it is love.",
            "zuv_role": "Zuv hears the hurt underneath and comes closer gently instead of arguing with the tone.",
            "tender_thesis": "Maybe love is softness under fire.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29.5,
        },
        {
            "name": "The Warning Was Love",
            "universal_truth": "A be-safe message can carry more feeling than a full love letter.",
            "aachu_specific_spark": "Aachu says be safe with protective intensity instead of soft wording.",
            "concrete_proof": "Phone glow, short message, and Zuv reading the worry behind the warning.",
            "zuv_role": "He receives the worry as care, not control.",
            "tender_thesis": "Maybe love is hearing the care inside the warning.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "The Attitude Was A Bandage",
            "universal_truth": "Sometimes attitude is the cover a soft heart uses when it is hurt.",
            "aachu_specific_spark": "Aachu's spicy tone is a shield for wanting to be understood.",
            "concrete_proof": "Turned-away face, hand still reaching, and Zuv stepping closer without a lecture.",
            "zuv_role": "He treats the tone as a clue, not the whole truth.",
            "tender_thesis": "Maybe love is not reacting to the shield.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Don't Touch Me, Stay Close",
            "universal_truth": "Some people ask for space while their hand asks for closeness.",
            "aachu_specific_spark": "Aachu's contradiction is visible: dramatic words, soft body language.",
            "concrete_proof": "One sleeve held, one face turned away, one patient hand waiting.",
            "zuv_role": "Zuv reads the body-language request and does not make her explain the contradiction.",
            "tender_thesis": "Maybe love is understanding the almost-said thing.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "Soft Hearts Sound Spicy",
            "universal_truth": "The softest people are not always soft-spoken.",
            "aachu_specific_spark": "Aachu's lover-girl heart arrives with a spicy little attitude.",
            "concrete_proof": "A dramatic look, a protective be-safe line, and the hand that still wants contact.",
            "zuv_role": "Zuv loves the softness without asking her to remove the spice.",
            "tender_thesis": "Maybe love is keeping both parts.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "She Loves Loudly",
            "universal_truth": "Some love is not calm, but it is deeply sincere.",
            "aachu_specific_spark": "Aachu loves through affection, worry, and the occasional dramatic warning.",
            "concrete_proof": "Cuddling, be safe, and missing her become one emotional pattern.",
            "zuv_role": "Zuv accepts the volume as part of the love.",
            "tender_thesis": "Maybe love is learning someone's volume.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 26.5,
        },
    ]
    return {
        "source": "Golden Theme variant tournament against Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Softness Under Fire",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner converts the screenshot from a generic girl-trait list into a gold-theme love story: "
            "the universal tension is not saying love gently when hurt, Aachu's proof is be-safe intensity "
            "and contradictory closeness, Zuv's role is hearing the hurt underneath, and the payoff is "
            "specific enough to save or send."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold machine by turning Aachu's expressive edge into lovable softness only because "
            "Zuv responds with active patience instead of reacting to the surface tone."
        ),
        "final_public_slide_copy_direction": [
            "He didn't marry someone who says everything gently.",
            "\"Don't touch me\" still held his sleeve.",
            "\"Be safe\" came out like a warning.",
            "So he heard the hurt underneath.",
            "Maybe love is softness under fire.",
        ],
        "candidates": candidates,
    }


def build_imperfect_repair_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "She Was Sorry. Bas Style Alag Tha.",
            "universal_truth": "Some people do not apologize in perfect words; they repair by coming closer again.",
            "aachu_specific_spark": "Aachu returns with pride, attitude, and a tiny care action instead of a polished sorry.",
            "concrete_proof": "She is still angry while fixing Zuv's collar or adjusting one small detail on him.",
            "zuv_role": "Zuv understands the repair and chooses not to tease, correct, or demand a better performance.",
            "tender_thesis": "Love learns the apology's accent.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29.5,
        },
        {
            "name": "The Collar Was The Sorry",
            "universal_truth": "Sometimes the apology is not a sentence; it is the hand that comes back gentle.",
            "aachu_specific_spark": "Aachu's pride stays visible while her care leaks through the collar fix.",
            "concrete_proof": "Turned-away face, careful fingers, one corrected collar.",
            "zuv_role": "He receives the gesture without turning it into a joke.",
            "tender_thesis": "Love recognizes repair before it becomes words.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29,
        },
        {
            "name": "Still Angry, Still Close",
            "universal_truth": "A fight is not over only when someone says sorry; sometimes it ends when distance gets smaller.",
            "aachu_specific_spark": "Aachu remains proudly offended while quietly choosing closeness again.",
            "concrete_proof": "She stands close enough to adjust his sleeve/collar after pretending not to care.",
            "zuv_role": "Zuv lets the closeness count and does not interrogate the mood.",
            "tender_thesis": "Love lets repair arrive in its own body language.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "No Perfect Sorry Needed",
            "universal_truth": "The right person does not need your apology to be cinema-perfect before they understand your heart.",
            "aachu_specific_spark": "Aachu's repair comes out as a practical question, a tiny adjustment, and a proud face.",
            "concrete_proof": "One ordinary care gesture after one tiny fight.",
            "zuv_role": "He accepts the language she can offer in that moment.",
            "tender_thesis": "Love is being fluent in each other's repair.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28,
        },
        {
            "name": "The Treaty Was Silent",
            "universal_truth": "Couples often sign peace treaties without announcing them.",
            "aachu_specific_spark": "Aachu signs hers with a proud face and one small act of care.",
            "concrete_proof": "She returns to the same frame, fixes the detail, and stays.",
            "zuv_role": "Zuv lets the silence be enough.",
            "tender_thesis": "Love knows when the treaty has been signed.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 27,
        },
    ]
    return {
        "source": "Layer E screenplay-pattern jam plus Golden Theme tournament against Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "She Was Sorry. Bas Style Alag Tha.",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the gold machine while rotating into a fresh repair lane: "
            "the universal tension is imperfect apology, Aachu's proof is proud return plus collar care, "
            "Zuv's role is active restraint and understanding, and the final thesis is sendable without private context."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the first-principles insight that Aachu's expressive edge becomes safe because "
            "Zuv treats the hidden softness as real, while avoiding the already-packaged sharp-words lane."
        ),
        "story_selling_card": "Card 06 - Delay The Confession",
        "screenplay_pattern": (
            "visible want -> emotional/social obstacle -> hidden feeling unsaid -> "
            "small action reveals truth -> visible behavior payoff"
        ),
        "final_public_slide_copy_direction": [
            "Some people don't say sorry.",
            "They come back with attitude.",
            "Still angry, fixing your collar.",
            "And he knows not to laugh.",
            "Love learns the apology's accent.",
        ],
        "candidates": candidates,
    }


def build_long_distance_ordinary_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Ordinary Time With You",
            "universal_truth": "If there were no long distance, the romance would be the tiny normal things they finally get to waste together.",
            "aachu_specific_spark": "Aachu turns imaginary plans into pure private-text banter: cooking badly, board games, and being happy that the cab is late.",
            "concrete_proof": "The message thread keeps cutting to tiny imagined scenes they cannot do in the same room yet, with the emotion hidden under teasing replies.",
            "zuv_role": "Zuv answers every small plan like it matters and lets the boring thing become a love language.",
            "tender_thesis": "Maybe I just miss wasting normal time with you.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29.5,
        },
        {
            "name": "We Don't Miss Dates. We Miss Tuesdays.",
            "universal_truth": "The ache of distance is not always missing special plans; it is missing the tiny unspecial rituals.",
            "aachu_specific_spark": "Aachu names small plans with dramatic seriousness.",
            "concrete_proof": "Cooking, board-game competitiveness, and delayed-cab relief.",
            "zuv_role": "Zuv joins the silly future tense instead of dismissing it.",
            "tender_thesis": "Love is wanting the same boring day.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 28.5,
        },
        {
            "name": "The Plans Were Tiny",
            "universal_truth": "When two people are apart, tiny plans become proof that the relationship still has a room to live in.",
            "aachu_specific_spark": "Aachu collects tiny plans like future receipts.",
            "concrete_proof": "The phone thread becomes a kitchen, a game board, and a rainy cab wait.",
            "zuv_role": "Zuv keeps the imaginary room open by replying with warmth.",
            "tender_thesis": "The smallest plans can hold the biggest missing.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 28.5,
        },
        {
            "name": "The Cab Can Be Late",
            "universal_truth": "Sometimes the most romantic thing is not arriving fast; it is getting a few extra minutes together.",
            "aachu_specific_spark": "Aachu secretly hopes the cab is late because leaving hurts.",
            "concrete_proof": "Rain, umbrella, phone glow, and both people quietly glad about the delay.",
            "zuv_role": "Zuv admits the same soft wish instead of playing practical.",
            "tender_thesis": "Some delays are just love buying time.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4.5,
                "share_send_potential": 4.5,
            },
            "total": 27.5,
        },
        {
            "name": "Board Games Across A Phone",
            "universal_truth": "Couples in distance still fight, tease, and keep score over ordinary things they cannot do yet.",
            "aachu_specific_spark": "Aachu's competitive softness turns a board game into a future scene.",
            "concrete_proof": "A board-game table imagined underneath the chat bubbles.",
            "zuv_role": "Zuv teases her gently while keeping the shared future alive.",
            "tender_thesis": "Missing someone can look like planning a fight you want to have.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4,
                "tender_thesis": 4,
                "share_send_potential": 4.5,
            },
            "total": 26.5,
        },
    ]
    return {
        "source": "Layer E plus Golden Theme variant tournament against the long-distance reference format and Calm Enough For Your Chaos first principles.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Ordinary Time With You",
        "winner_score": 29.5,
        "decision": "GO",
        "selector_verdict": (
            "Winner keeps the chat-bubble reference mechanic but deepens it into a relationship truth: "
            "long distance hurts most in the boring, ordinary life they cannot waste together. "
            "The proof beats are small, drawable, and sendable; Zuv's role is active because he replies, joins, "
            "and lets each tiny plan matter."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold-machine lesson by starting with a universal ache, proving it through playful "
            "Aachu/Zuv behavior, showing Zuv joining the ordinary future instead of treating it as silly, "
            "and landing a tender acceptance thesis."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "screenplay_pattern": (
            "distance ache -> tiny future plans -> banter receipts -> shared wish underneath -> ordinary-time payoff"
        ),
        "final_public_slide_copy_direction": [
            "If there was no long distance...",
            "\"We should cook together.\"\n\"That's a terrible idea.\"\n\"Exactly.\"",
            "\"Board game night?\"\n\"Only if you don't invent rules after losing.\"",
            "\"Cab is 12 minutes late.\"\n\"Best news all day.\"",
            "\"Maybe I don't miss big dates.\"\n\"Maybe I just miss wasting normal time with you.\"",
        ],
        "candidates": candidates,
    }


def is_long_distance_ordinary_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in LONG_DISTANCE_ORDINARY_TOKENS)


def is_suitcase_relocation_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in SUITCASE_RELOCATION_TOKENS)


def is_pakka_reassurance_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in PAKKA_REASSURANCE_TOKENS)


def is_softness_under_fire_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in SOFTNESS_UNDER_FIRE_TOKENS)


def is_imperfect_repair_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in IMPERFECT_REPAIR_TOKENS)


def is_fifty_fifty_care_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in FIFTY_FIFTY_CARE_TOKENS)


def is_food_denial_story(story: str) -> bool:
    lower = story.lower()
    denial_signal = any(token in lower for token in ["not hungry", "mujhe kuch nahi chahiye"])
    proof_signal = any(token in lower for token in FOOD_DENIAL_TOKENS)
    return denial_signal and proof_signal


def is_wallet_audit_story(story: str) -> bool:
    lower = story.lower()
    explicit_signal = any(token in lower for token in WALLET_AUDIT_TOKENS)
    wallet_signal = "wallet" in lower and any(
        token in lower for token in ["cash", "pocket", "budget", "500", "audit"]
    )
    couple_signal = any(token in lower for token in ["aachu", "nancho", "zuv", "himanshu", "wife"])
    return explicit_signal or (wallet_signal and couple_signal)


def is_tasty_life_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in TASTY_LIFE_TOKENS)


def is_private_captions_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in PRIVATE_CAPTIONS_TOKENS)


def is_unfiltered_nonsense_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in UNFILTERED_NONSENSE_TOKENS)


def is_main_kar_lungi_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in MAIN_KAR_LUNGI_TOKENS)


def is_waterfall_lantern_story(story: str) -> bool:
    lower = story.lower()
    return all(token in lower for token in WATERFALL_LANTERN_TOKENS)


def is_photo_ritual_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in PHOTO_RITUAL_TOKENS)


def is_kashmiri_language_story(story: str) -> bool:
    lower = story.lower()
    return "kashmiri" in lower and any(token in lower for token in KASHMIRI_LANGUAGE_TOKENS)


def is_subtitle_language_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in SUBTITLE_LANGUAGE_TOKENS)


def is_mood_changed_story(story: str) -> bool:
    lower = story.lower()
    return any(token in lower for token in MOOD_CHANGED_TOKENS)


def is_workday_homecoming_story(story: str) -> bool:
    lower = story.lower()
    if "maybe chaos is also home" in lower:
        return True
    work_signal = any(token in lower for token in WORKDAY_HOMECOMING_WORK_TOKENS)
    home_signal = any(token in lower for token in WORKDAY_HOMECOMING_HOME_TOKENS)
    return work_signal and home_signal


def is_high_maintenance_care_story(story: str) -> bool:
    lower = story.lower()
    if "she was not high-maintenance" in lower or "she was not high maintenance" in lower:
        return True
    return any(token in lower for token in HIGH_MAINTENANCE_CARE_TOKENS) and (
        "before she asked" in lower or "care without shrinking" in lower or "tiny discomfort" in lower
    )


def build_long_distance_ordinary_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    full = [
        {
            "copy": "If there was no long distance...",
            "role": "universal hook",
            "visual": (
                "Aachu and Zuv are apart in two soft phone-lit corners, each holding a phone, with tiny imagined "
                "ordinary scenes beginning to appear between them; distance is the obstacle, not the aesthetic."
            ),
            "emotion": "recognition ache",
            "cta_intent": "make long-distance couples send this as a recognition of missing ordinary life together",
            "text_layout": {"primary_position": "top_center", "speech_bubble": ""},
        },
        {
            "copy": "\"We should cook together.\"\n\"That's a terrible idea.\"\n\"Exactly.\"",
            "role": "aachu-specific playful proof",
            "visual": (
                "Inside the imagined shared room from the chat, Aachu and Zuv stand at a tiny kitchen counter with "
                "flour, a messy pot, and two phones nearby; Aachu is animated about the plan and Zuv joins the bad idea with a warm amused reply."
            ),
            "emotion": "playful future-tense",
            "cta_intent": "make viewers tag the person they want to ruin dinner with",
            "text_layout": {"primary_position": "top_center", "speech_bubble": "exactly"},
        },
        {
            "copy": "\"Board game night?\"\n\"Only if you don't invent rules after losing.\"",
            "role": "comic escalation",
            "visual": (
                "Aachu and Zuv sit across an imagined board-game table with dice, tiny colored tokens, and exaggerated competitive faces; "
                "Zuv teases gently about her invented rules while still clearly wanting the whole scene with her."
            ),
            "emotion": "affectionate teasing",
            "cta_intent": "make partners send this as the funny fight they miss having in person",
            "text_layout": {"primary_position": "top_center", "speech_bubble": "invent rules after losing"},
        },
        {
            "copy": "\"Cab is 12 minutes late.\"\n\"Best news all day.\"",
            "role": "zuv role and emotional bridge",
            "visual": (
                "Rainy imagined pickup scene: Aachu and Zuv wait under one umbrella beside a small cab-app phone screen; "
                "instead of frustration, both look quietly relieved, and Zuv's reply admits he wants the extra minutes too."
            ),
            "emotion": "soft admission",
            "cta_intent": "make viewers save the moment where delay becomes closeness",
            "text_layout": {"primary_position": "top_center", "speech_bubble": "best news all day"},
        },
        {
            "copy": "\"Maybe I don't miss big dates.\"\n\"Maybe I just miss wasting normal time with you.\"",
            "role": "save/share thesis",
            "visual": (
                "Final warm-paper room where the earlier kitchen, board-game, and cab icons soften into one ordinary shared evening; "
                "Aachu and Zuv sit close with phones lowered, proving the point is not the plans but wanting normal time together."
            ),
            "emotion": "tender landing",
            "cta_intent": "make long-distance couples save or send the ordinary-time thesis",
            "text_layout": {"primary_position": "top_center", "speech_bubble": ""},
        },
    ]
    if slide_count == 4:
        selected_indexes = [0, 1, 3, 4]
    else:
        selected_indexes = list(range(min(slide_count, len(full))))
    source_groups = distribute_sources(image_paths, len(selected_indexes)) if image_paths else [[] for _ in selected_indexes]
    slides: list[dict[str, Any]] = []
    for index, source_index in enumerate(selected_indexes, start=1):
        item = full[source_index]
        slides.append(
            {
                "slide": index,
                "copy": item["copy"],
                "role": item["role"],
                "visual": item["visual"],
                "emotion": item["emotion"],
                "cta_intent": item["cta_intent"],
                "text_layout": item["text_layout"],
                "source_images": source_groups[index - 1],
            }
        )
    return slides


def build_private_captions_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    full = [
        {
            "copy": "some couples come with private captions",
            "role": "universal hook",
            "visual": (
                "Aachu and Zuv in one warm ordinary shared frame with paired private labels beginning to appear "
                "near each person; the labels are evidence, not a quote-card panel."
            ),
            "emotion": "instant recognition",
            "cta_intent": "make viewers tag the person who privately reads them kindly",
        },
        {
            "copy": "her: being dramatic\nhim: taking it seriously",
            "role": "aachu-specific proof / zuv role",
            "visual": (
                "Aachu expressive with hands mid-air in a small home moment while Zuv leans forward with sincere focus; "
                "paired private labels near each person prove that her drama is being received as real."
            ),
            "emotion": "funny but protected",
            "cta_intent": "turn the meme grammar into a recognizable partner receipt",
        },
        {
            "copy": "her: stressed\nhim: listening first",
            "role": "concrete proof / zuv listens",
            "visual": (
                "Aachu tense beside a phone, list, or tiny messy everyday cue while Zuv puts his phone down and angles "
                "his body toward her; labels near each person show stress becoming attention."
            ),
            "emotion": "safe attention",
            "cta_intent": "send to the person who listens before fixing",
        },
        {
            "copy": "her: excited about a tiny thing\nhim: happy because she is",
            "role": "joy proof / zuv mirrors joy",
            "visual": (
                "Aachu sparkling over one tiny object or message while Zuv watches her joy with a proud soft smile; "
                "paired private labels near each person make her tiny excitement become his reason to be happy."
            ),
            "emotion": "borrowed joy",
            "cta_intent": "make viewers recognize being loved through their smallest excitement",
        },
        {
            "copy": "her: doesn't like it\nhim: already on her side",
            "role": "alliance proof / relationship side-taking",
            "visual": (
                "Aachu gives a small unmistakable side-eye at an ordinary thing while Zuv has already shifted beside her, "
                "quietly on the same side; paired private labels near each person show affectionate alliance."
            ),
            "emotion": "playful loyalty",
            "cta_intent": "tag the person who joins your side without a whole explanation",
        },
        {
            "copy": "him: acting tough\nher: knows he's soft",
            "role": "zuv-specific proof / aachu sees softness",
            "visual": (
                "Zuv mock-tough with folded arms and an obviously soft face while Aachu looks up with a knowing smile; "
                "paired private labels near each person prove she captions him kindly too."
            ),
            "emotion": "mutual tenderness",
            "cta_intent": "show the dynamic is mutual, not one person being decoded",
        },
        {
            "copy": "him: bad joke\nher: favorite sound",
            "role": "mutual proof / favorite sound",
            "visual": (
                "Zuv laughing at his own terrible joke while Aachu laughs because it is him; paired private labels near "
                "each person keep the scene original, affectionate, and not copied from any sitcom frame."
            ),
            "emotion": "beloved silliness",
            "cta_intent": "make the carousel saveable for couples with private humor",
        },
        {
            "copy": "her: quiet\nhim: staying close",
            "role": "quiet bridge / steady closeness",
            "visual": (
                "Aachu quieter than usual on one side of the frame while Zuv stays close without crowding her; "
                "paired private labels near each person show care continuing when the mood changes."
            ),
            "emotion": "gentle steadiness",
            "cta_intent": "prove the caption grammar works beyond only comic moments",
        },
        {
            "copy": "him: overthinking\nher: making it gentle",
            "role": "mutual bridge / aachu active softness",
            "visual": (
                "Zuv with a tiny overthinking crease while Aachu softens the moment with one hand or warm glance; "
                "paired private labels near each person show Aachu actively captions him kindly as well."
            ),
            "emotion": "reciprocal care",
            "cta_intent": "keep Aachu's emotional role active and reciprocal",
        },
        {
            "copy": "the right person captions you kindly",
            "role": "save/share thesis",
            "visual": (
                "Aachu and Zuv in one quiet final shared frame as the paired private labels soften into the warm paper "
                "around them; the relationship stays visible and the ending is not a standalone quote card."
            ),
            "emotion": "tender knownness",
            "cta_intent": "send to the person who gives you the kinder caption",
        },
    ]
    if slide_count == 4:
        selected_indexes = [0, 1, 2, 9]
    elif slide_count == 5:
        selected_indexes = [0, 1, 2, 6, 9]
    elif slide_count == 6:
        selected_indexes = [0, 1, 2, 3, 6, 9]
    elif slide_count == 7:
        selected_indexes = [0, 1, 2, 3, 4, 6, 9]
    elif slide_count == 8:
        selected_indexes = [0, 1, 2, 3, 4, 5, 6, 9]
    else:
        selected_indexes = list(range(min(slide_count - 1, len(full) - 1))) + [len(full) - 1]

    source_groups = distribute_sources(image_paths, len(selected_indexes))
    slides: list[dict[str, Any]] = []
    for index, source_index in enumerate(selected_indexes, start=1):
        item = full[source_index]
        slides.append(
            {
                "slide": index,
                **item,
                "source_images": source_groups[index - 1],
            }
        )
    return slides


def build_private_captions_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Some Couples Come With Private Captions",
            "universal_truth": (
                "The right relationship is not only being seen from the outside; it is being captioned kindly "
                "by the person who knows what your surface behavior really means."
            ),
            "aachu_specific_spark": (
                "Aachu's expressive drama, stress, tiny excitement, and dislike become softer when Zuv privately reads "
                "the feeling underneath instead of mocking the surface."
            ),
            "concrete_proof": (
                "Paired labels over shared original Aachu/Zuv scenes: drama/seriousness, stress/listening, tiny joy/shared joy, "
                "side-eye/alliance, mock toughness/softness, bad joke/favorite sound."
            ),
            "zuv_role": (
                "Zuv actively takes Aachu seriously, listens first, becomes happy because she is, and joins her side before she has to build a case."
            ),
            "tender_thesis": "The right person captions you kindly.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.7,
                "share_send_potential": 5,
            },
            "total": 29.7,
        },
        {
            "name": "Same Scene, Two Inner Worlds",
            "universal_truth": "Every couple has moments where the outside scene is ordinary but the private reading changes everything.",
            "aachu_specific_spark": "Aachu's big expressions and Zuv's quiet readings create a clear two-caption frame.",
            "concrete_proof": "Shared rooms, glances, side-eyes, laughter, listening posture, and labels near each person.",
            "zuv_role": "He reads the generous meaning underneath the visible behavior.",
            "tender_thesis": "Love is the second caption.",
            "scores": {
                "universal_hook": 4.8,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 4.8,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 29.1,
        },
        {
            "name": "The Kinder Caption Wins",
            "universal_truth": "The person who loves you best gives your behavior the most generous interpretation.",
            "aachu_specific_spark": "Aachu's dramatic, stressed, and delighted beats can all be recaptioned kindly.",
            "concrete_proof": "Caption pairs show how an outside label becomes a private love reading.",
            "zuv_role": "Zuv chooses the kinder reading first.",
            "tender_thesis": "Choose the person who captions you gently.",
            "scores": {
                "universal_hook": 4.6,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 4.7,
                "zuv_emotional_role": 4.7,
                "tender_thesis": 4.6,
                "share_send_potential": 4.8,
            },
            "total": 27.9,
        },
        {
            "name": "Right Person Reads The Subtext",
            "universal_truth": "Love is understanding the subtext before the person has to explain themselves.",
            "aachu_specific_spark": "Useful for Aachu/Zuv, but too close to the existing subtitles/mood-translation lane.",
            "concrete_proof": "Expression reads, quiet listening, and one or two label pairs.",
            "zuv_role": "Zuv translates feeling into care.",
            "tender_thesis": "The right person reads the subtext.",
            "scores": {
                "universal_hook": 4.4,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 4.2,
                "zuv_emotional_role": 4.7,
                "tender_thesis": 4.3,
                "share_send_potential": 4.4,
            },
            "total": 26,
        },
        {
            "name": "Generic Compatibility Labels",
            "universal_truth": "One person is one way, the other balances them.",
            "aachu_specific_spark": "Weak because it becomes category matching instead of lived Aachu/Zuv proof.",
            "concrete_proof": "Could become static compatibility cards.",
            "zuv_role": "Too passive; risks 'handler' framing.",
            "tender_thesis": "Opposites fit.",
            "scores": {
                "universal_hook": 3.5,
                "aachu_zuv_specificity": 3,
                "concrete_proof": 3,
                "zuv_emotional_role": 3,
                "tender_thesis": 3,
                "share_send_potential": 3.5,
            },
            "total": 19,
        },
    ]
    return {
        "source": "Four-agent creative-room repair after creator clarified that the reference concept is paired private captions over shared scenes, not generic reactions.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Some Couples Come With Private Captions",
        "winner_score": 29.7,
        "decision": "GO",
        "selector_verdict": (
            "Winner preserves the visual grammar the creator liked: lowercase paired labels inside a shared scene, "
            "with the emotional turn that love is a kinder private interpretation, not merely matching energies."
        ),
        "calm_enough_for_chaos_alignment": (
            "Starts from a universal relationship truth, proves it with specific Aachu/Zuv behaviors, keeps Zuv active, "
            "and lands an earned sendable thesis rather than a quote-card ending."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "final_public_slide_copy_direction": [
            "some couples come with private captions",
            "her: being dramatic / him: taking it seriously",
            "her: stressed / him: listening first",
            "her: excited about a tiny thing / him: happy because she is",
            "her: doesn't like it / him: already on her side",
            "him: acting tough / her: knows he's soft",
            "him: bad joke / her: favorite sound",
            "the right person captions you kindly",
        ],
        "candidates": candidates,
    }


def build_unfiltered_nonsense_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    full = [
        {
            "copy": "Marry the one who joins your nonsense.",
            "role": "universal hook",
            "visual": (
                "Aachu mid-story with animated hands and a bright expressive face while Zuv leans in, "
                "already smiling like he knows this private language; soft blank space for the hook."
            ),
            "emotion": "playful recognition",
            "cta_intent": "tag the person who joins the bit instead of judging it",
        },
        {
            "copy": "You send 5 updates for 1 thought.",
            "role": "concrete proof beat",
            "visual": (
                "A phone screen with five warm handwritten message bubbles from Aachu about one tiny event, "
                "with her expressive little portrait in the corner and Zuv reading with amused focus."
            ),
            "emotion": "affectionate over-explaining",
            "cta_intent": "make viewers recognize their own message-thread chaos",
        },
        {
            "copy": "They reply to every plot twist.",
            "role": "Zuv role proof",
            "visual": (
                "Zuv typing thoughtful, playful replies to each message bubble rather than muting the thread; "
                "small reaction marks show he is entering the story, not merely tolerating it."
            ),
            "emotion": "active participation",
            "cta_intent": "tag the partner who treats tiny updates like real plot",
        },
        {
            "copy": "You start stories from the middle.",
            "role": "escalation proof",
            "visual": (
                "Aachu in a hallway or parked-car scene reenacting a dramatic story from the middle, "
                "with little arrows and tiny side-quest doodles around her as Zuv follows the thread."
            ),
            "emotion": "comic specificity",
            "cta_intent": "push the swipe with a familiar, memeable receipt",
        },
        {
            "copy": "They ask like they were there.",
            "role": "Zuv role / emotional reversal",
            "visual": (
                "Zuv asking a fully invested follow-up question, one hand raised like a courtroom witness, "
                "while Aachu lights up because he has joined her private logic."
            ),
            "emotion": "seen and delighted",
            "cta_intent": "show that the love is participation, not patience",
        },
        {
            "copy": "Maybe it was never nonsense.",
            "role": "bridge to tenderness",
            "visual": (
                "Both of them laughing inside the same small thought bubble world: message bubbles, "
                "tiny fake-drama props, and shared expressions now belong to both of them."
            ),
            "emotion": "soft turn",
            "cta_intent": "turn the joke into a saveable relationship truth",
        },
        {
            "copy": "Maybe love is finding someone fluent in you.",
            "role": "save/share thesis",
            "visual": (
                "A quiet final frame of Aachu and Zuv side by side, surrounded by a few tiny shared-language "
                "symbols from prior slides, both looking warm and unedited; generous whitespace for the thesis."
            ),
            "emotion": "tender acceptance",
            "cta_intent": "send to the person fluent in your private language",
        },
    ]
    selected_indexes = list(range(len(full)))
    if slide_count == 4:
        selected_indexes = [0, 1, 4, 6]
    elif slide_count == 5:
        selected_indexes = [0, 1, 3, 4, 6]
    elif slide_count == 6:
        selected_indexes = [0, 1, 2, 3, 4, 6]
    else:
        selected_indexes = list(range(min(slide_count, len(full))))

    source_groups = distribute_sources(image_paths, len(selected_indexes))
    slides: list[dict[str, Any]] = []
    for index, source_index in enumerate(selected_indexes, start=1):
        item = full[source_index]
        slides.append(
            {
                "slide": index,
                **item,
                "source_images": source_groups[index - 1],
            }
        )
    return slides


def build_unfiltered_nonsense_concept_selection() -> dict[str, Any]:
    candidates = [
        {
            "name": "Marry The One Who Joins Your Nonsense",
            "universal_truth": (
                "The most taggable love is not being tolerated at your strangest; "
                "it is finding someone who enters the strange little logic with you."
            ),
            "aachu_specific_spark": (
                "Aachu's full-signal version arrives as five updates, mid-story starts, "
                "tiny dramatic reenactments, and private logic that does not need editing."
            ),
            "concrete_proof": (
                "Message bubbles, a car/hallway monologue, a story starting from the middle, "
                "and Zuv asking follow-up questions like he was there."
            ),
            "zuv_role": (
                "Zuv does not handle or mute the nonsense; he joins the bit, asks the next question, "
                "and lets the full version stay wanted."
            ),
            "tender_thesis": "Maybe love is finding someone fluent in you.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 30,
        },
        {
            "name": "Marry The One Who Likes Your Unfiltered Version",
            "universal_truth": (
                "Every couple has an unfiltered version that would be too much for a casual audience "
                "but feels normal with the right person."
            ),
            "aachu_specific_spark": "Aachu's unedited version includes rapid updates, random commentary, and full-body storytelling.",
            "concrete_proof": "The five updates, the story with no beginning, and the partner adding to the scene.",
            "zuv_role": "Zuv enjoys the unfiltered version instead of reducing it to noise.",
            "tender_thesis": "Maybe love is being wanted at full volume.",
            "scores": {
                "universal_hook": 5,
                "aachu_zuv_specificity": 4.5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 5,
            },
            "total": 29.5,
        },
        {
            "name": "Marry The One Who Enjoys The Uncut Version",
            "universal_truth": "Love works when the rough cut is not treated as embarrassing extra footage.",
            "aachu_specific_spark": "Aachu tells the whole thing with side quests, restarts, faces, and extra context.",
            "concrete_proof": "A walking monologue, a phone follow-up, and both people laughing mid-explanation.",
            "zuv_role": "Zuv adds commentary instead of asking her to shorten herself.",
            "tender_thesis": "Love is not being tolerated; it is being enjoyed in full.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 5,
                "zuv_emotional_role": 5,
                "tender_thesis": 5,
                "share_send_potential": 4.5,
            },
            "total": 29,
        },
        {
            "name": "The Person Fluent In Your Nonsense",
            "universal_truth": "Private couple language becomes love when someone understands what the outside world would call nonsense.",
            "aachu_specific_spark": "Aachu's small plot twists and fake drama become a language rather than a problem.",
            "concrete_proof": "Inside jokes, message threads, and one partner continuing the fake drama without missing the beat.",
            "zuv_role": "Zuv becomes fluent by joining the rhythm, not translating it into something smaller.",
            "tender_thesis": "The right person speaks you back to yourself.",
            "scores": {
                "universal_hook": 4.5,
                "aachu_zuv_specificity": 5,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 5,
                "tender_thesis": 4.5,
                "share_send_potential": 5,
            },
            "total": 28.5,
        },
        {
            "name": "Annoying But Mine",
            "universal_truth": "The annoying version is only lovable when the joke stays affectionate and mutual.",
            "aachu_specific_spark": "Aachu has repeated updates and random side quests.",
            "concrete_proof": "A message thread and one over-explained story.",
            "zuv_role": "Zuv smiles and replies instead of muting the thread.",
            "tender_thesis": "Maybe love is liking the extra version.",
            "scores": {
                "universal_hook": 4,
                "aachu_zuv_specificity": 4,
                "concrete_proof": 4.5,
                "zuv_emotional_role": 4.5,
                "tender_thesis": 4,
                "share_send_potential": 4.5,
            },
            "total": 25.5,
        },
    ]
    return {
        "source": "Broad pure-insight parallel creative-room exchange after creator rejected the public-spark lane as too niche.",
        "rubric": [
            "universal_hook",
            "aachu_zuv_specificity",
            "concrete_proof",
            "zuv_emotional_role",
            "tender_thesis",
            "share_send_potential",
        ],
        "minimum_go_score": 28,
        "winner": "Marry The One Who Joins Your Nonsense",
        "winner_score": 30,
        "decision": "GO",
        "selector_verdict": (
            "Winner has the broadest everyday partner-tag mirror: every couple has private nonsense, "
            "but the right love joins it instead of tolerating or muting it. The repair removes mean "
            "'annoying' framing and makes the dynamic mutual, playful, and visually drawable."
        ),
        "calm_enough_for_chaos_alignment": (
            "Preserves the gold carousel machine as viral story architecture: universal anti-ideal -> "
            "recognizable unfiltered receipts -> active partner participation -> tender acceptance thesis."
        ),
        "story_selling_card": "Card 05 - Banter To Belonging",
        "final_public_slide_copy_direction": [
            "Marry the one who joins your nonsense.",
            "You send 5 updates for 1 thought.",
            "They reply to every plot twist.",
            "You start stories from the middle.",
            "They ask questions like they were there.",
            "Maybe it was never nonsense.",
            "Maybe love is finding someone fluent in you.",
        ],
        "candidates": candidates,
    }


def build_slides(story: str, image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    lane = classify_content_lane(story)
    if is_private_captions_story(story):
        return build_private_captions_slides(image_paths, slide_count)
    if is_unfiltered_nonsense_story(story):
        return build_unfiltered_nonsense_slides(image_paths, slide_count)
    if is_long_distance_ordinary_story(story):
        return build_long_distance_ordinary_slides(image_paths, slide_count)
    if is_suitcase_relocation_story(story):
        return build_suitcase_relocation_slides(image_paths, slide_count)
    if is_tasty_life_story(story):
        return build_tasty_life_slides(image_paths, slide_count)
    if is_wallet_audit_story(story):
        return build_wallet_audit_slides(image_paths, slide_count)
    if is_food_denial_story(story):
        return build_food_denial_slides(image_paths, slide_count)
    if is_fifty_fifty_care_story(story):
        return build_fifty_fifty_care_slides(image_paths, slide_count)
    if is_main_kar_lungi_story(story):
        return build_main_kar_lungi_slides(image_paths, slide_count)
    if is_pakka_reassurance_story(story):
        return build_pakka_reassurance_slides(image_paths, slide_count)
    if is_softness_under_fire_story(story):
        return build_softness_under_fire_slides(image_paths, slide_count)
    if is_imperfect_repair_story(story):
        return build_imperfect_repair_slides(image_paths, slide_count)
    if is_workday_homecoming_story(story):
        return build_workday_homecoming_slides(image_paths, slide_count)
    if is_high_maintenance_care_story(story):
        return build_high_maintenance_care_slides(image_paths, slide_count)
    if is_mood_changed_story(story):
        return build_mood_changed_slides(image_paths, slide_count)
    if is_kashmiri_language_story(story):
        return build_kashmiri_language_slides(image_paths, slide_count)
    if is_subtitle_language_story(story):
        return build_subtitle_language_slides(image_paths, slide_count)
    if is_photo_ritual_story(story):
        return build_photo_ritual_slides(image_paths, slide_count)
    if is_waterfall_lantern_story(story):
        return build_waterfall_lantern_slides(image_paths, slide_count)
    if lane == "Tiny Rituals" and any(token in story.lower() for token in ["anklet", "shoe", "shoes", "sandal", "sandals"]):
        return build_tiny_ritual_anklet_slides(image_paths, slide_count)
    is_morning_person_story = any(token in story.lower() for token in MORNING_PERSON_TOKENS)
    if lane == "Chaotic Wife, Calm Husband" and is_morning_person_story:
        return build_morning_person_slides(image_paths, slide_count)
    if lane == "Chaotic Wife, Calm Husband":
        return build_chaotic_wife_slides(image_paths, slide_count)

    place = infer_place(story)
    origin = infer_origin(story)
    source_groups = distribute_sources(image_paths, slide_count)

    if slide_count == 4:
        copies = [
            f"It started with {origin}.",
            "Then the small things became our language.",
            f"{place} made the story feel huge.",
            "But the point was still us.",
        ]
        roles = ["hook", "proof", "expansion", "payoff"]
    else:
        copies = [
            f"It started with {origin}.",
            "By the second date, we were already a little unserious.",
            "Then somehow, a date became a trip.",
            f"{place} made the story feel huge.",
            "But the point was still us.",
        ]
        roles = ["hook", "playful proof", "transition", "expansion", "payoff"]

    visuals = [
        "A close, specific origin frame rooted in the earliest supplied image: food, cups, table, names, or another tiny beginning detail.",
        "A playful early-memory frame that preserves the supplied second-date expressions, poses, outfit cues, and awkward-funny comfort.",
        "A transition frame using a candid room, phone, road, doorway, suitcase, or other image cue that makes the next chapter feel like it is calling.",
        f"A wide {place} frame with the couple, landscape scale, sky, mountains, river, or travel cues from the supplied photos.",
        "A quiet final frame with the couple small together in a big place, making the relationship the center rather than the location.",
    ]
    if slide_count == 4:
        visuals = [visuals[0], visuals[1], visuals[3], visuals[4]]

    emotions = ["soft nostalgia", "playful comfort", "anticipation", "wonder", "tender settledness"]
    if slide_count == 4:
        emotions = [emotions[0], emotions[1], emotions[3], emotions[4]]

    slides = []
    for index, copy in enumerate(copies, start=1):
        slides.append(
            {
                "slide": index,
                "copy": copy,
                "role": roles[index - 1],
                "visual": visuals[index - 1],
                "emotion": emotions[index - 1],
                "cta_intent": "make the memory feel specific enough to save or send",
                "source_images": source_groups[index - 1],
            }
        )
    return slides
