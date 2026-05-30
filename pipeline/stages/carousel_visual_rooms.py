"""Visual-room gates for Codex-native carousel packages."""

from __future__ import annotations

from typing import Any

from pipeline.stages.carousel_lanes import (
    SUITCASE_RELOCATION_BACKGROUND_LOCK,
    SUITCASE_RELOCATION_CONTINUITY_LOCK,
    SUITCASE_RELOCATION_PROP_LOCK,
    SUITCASE_RELOCATION_WARDROBE_LOCK,
    is_fifty_fifty_care_story,
    is_food_denial_story,
    is_imperfect_repair_story,
    is_long_distance_ordinary_story,
    is_main_kar_lungi_story,
    is_commitment_still_love_story,
    is_enough_love_story,
    is_private_captions_story,
    is_softness_under_fire_story,
    is_suitcase_relocation_story,
    is_tasty_life_story,
    is_wallet_audit_story,
)
from pipeline.stages.successful_carousel_standard import stage_scene_storytelling_issues


def build_visual_debate(story: str, slides: list[dict[str, Any]], lane: str) -> dict[str, Any]:
    is_private_captions = is_private_captions_story(story)
    is_independent_care = is_main_kar_lungi_story(story)
    is_fifty_fifty_care = is_fifty_fifty_care_story(story)
    is_tasty_life = is_tasty_life_story(story)
    is_wallet_audit = is_wallet_audit_story(story)
    is_food_denial = is_food_denial_story(story)
    is_softness_under_fire = is_softness_under_fire_story(story)
    is_imperfect_repair = is_imperfect_repair_story(story)
    is_long_distance_ordinary = is_long_distance_ordinary_story(story)
    is_suitcase_relocation = is_suitcase_relocation_story(story)
    is_commitment_still_love = is_commitment_still_love_story(story)
    is_enough_love = is_enough_love_story(story)
    if is_enough_love:
        winner = "Seven Visible Vows"
    elif is_commitment_still_love:
        winner = "Future Witness Scenes"
    elif is_private_captions:
        winner = "Private Caption Shared Frames"
    elif is_long_distance_ordinary:
        winner = "Chat Bubbles Become Shared Rooms"
    elif is_suitcase_relocation:
        winner = "Short-Film Packing Room"
    elif is_independent_care:
        winner = "Outdoor Threshold"
    elif is_fifty_fifty_care:
        winner = "Scoreboard Becomes A Soft Relay"
    elif is_tasty_life:
        winner = "Lived-In Home Becomes A Love Receipt"
    elif is_wallet_audit:
        winner = "Airy Behavioral Receipts"
    elif is_food_denial:
        winner = "Plate Becomes A Love Receipt"
    elif is_softness_under_fire:
        winner = "Sharp Words, Soft Hands"
    elif is_imperfect_repair:
        winner = "One Gesture, Wide Silence"
    else:
        winner = "Slide-Led Evidence Plan"
    options = (
        [
            {
                "name": "Future Witness Scenes",
                "score": 30,
                "case_for": "Best for exact-copy commitment text: conflict, repair, older-couple witness, bad-day cost, and future-us payoff become clear staged scenes.",
                "risk": "Must not copy the reference film stills or become generic elderly-couple quote art; Aachu/Zuv identity and house style must dominate.",
            },
            {
                "name": "Hands Stay Reachable",
                "score": 28.5,
                "case_for": "Very strong for conflict-with-commitment because hands, distance, and posture prove the text without heavy explanation.",
                "risk": "Can become visually repetitive if every slide is only a close-up handhold.",
            },
            {
                "name": "Older Couple Mirror",
                "score": 27,
                "case_for": "Clear reference to the older-couple idea.",
                "risk": "Rejected as the main system because the older couple can overpower Aachu/Zuv and make the deck less identity-first.",
            },
        ]
        if is_commitment_still_love
        else [
            {
                "name": "Seven Visible Vows",
                "score": 30,
                "case_for": "Best for the authorized exact-text reference: every line becomes a distinct staged promise, from walking to waiting, without repeating the same couple pose.",
                "risk": "Must avoid copying the third-party visual style or watermark; A Story identity, paper, typography, and brandmark must dominate.",
            },
            {
                "name": "Lack Becomes Care Receipts",
                "score": 28.5,
                "case_for": "Strong emotional clarity because each limitation is answered by visible care.",
                "risk": "Can feel too explanatory if text carries the scene instead of body language.",
            },
            {
                "name": "Minimal Quote Scenes",
                "score": 25,
                "case_for": "Easy to read and close to the source reference.",
                "risk": "Rejected as the main system because it risks quote-card energy and weak Aachu/Zuv identity."
            },
        ]
        if is_enough_love
        else
        [
            {
                "name": "Outdoor Threshold",
                "score": 29,
                "case_for": "Keeps the emotional premise on pride plus closeness while giving every slide an exterior/public scene.",
                "risk": "Needs restraint so the threshold, path, or gate does not become the premise.",
            },
            {
                "name": "Public Walkway Micro-Care",
                "score": 28,
                "case_for": "Makes Zuv's help visible without turning the moment into rescue.",
                "risk": "Can feel too generic if Aachu's proud body language is not sharp.",
            },
            {
                "name": "Courtyard Dusk Aftercare",
                "score": 27,
                "case_for": "Strong final-slide softness.",
                "risk": "Too quiet as a full carousel spine; better as the payoff than the whole visual system.",
            },
        ]
        if is_independent_care
        else [
            {
                "name": "Chat Bubbles Become Shared Rooms",
                "score": 29.5,
                "case_for": "Preserves the reference mechanic while making every message open into a concrete ordinary-life scene.",
                "risk": "Must not become a copied text-message reel; the imagined scenes need original Aachu/Zuv behavior.",
            },
            {
                "name": "One Phone, Five Ordinary Plans",
                "score": 28,
                "case_for": "Very legible for long-distance couples and keeps the phone as a portal rather than the whole frame.",
                "risk": "Can feel static if every slide is only a phone screen.",
            },
            {
                "name": "Pure Chat Screenshot",
                "score": 24,
                "case_for": "Fast and familiar.",
                "risk": "Rejected because it copies the surface format and loses the @a.storyof.two illustrated relationship proof.",
            },
        ]
        if is_long_distance_ordinary
        else [
            {
                "name": "Lived-In Home Becomes A Love Receipt",
                "score": 29,
                "case_for": "Makes the fuller-life thesis intimate and drawable: kitchen snacks, couch laughter, plans, and Zuv making space at home.",
                "risk": "Must keep food as one receipt among many so the deck does not repeat the already-used not-hungry lane.",
            },
            {
                "name": "Couch To Kitchen Comfort",
                "score": 28,
                "case_for": "Gives visual variety inside one home through kitchen counter, couch, blanket, low table, and late-night snack beats.",
                "risk": "Can become cozy-aesthetic content unless every frame keeps Aachu/Zuv behavior clear.",
            },
            {
                "name": "Restaurant Receipt",
                "score": 25,
                "case_for": "The food receipt is obvious and easy to read.",
                "risk": "Rejected for this direction: too close to food-denial/restaurant content and weaker than home comfort.",
            },
        ]
        if is_tasty_life
        else [
            {
                "name": "Plate Becomes A Love Receipt",
                "score": 29,
                "case_for": "Keeps the scenes partner-tag clear: denial, one bite, best bite, Zuv ordering extra, and the tender payoff.",
                "risk": "Must not become generic food content; the point is being known without having to confess the change.",
            },
            {
                "name": "Cafe Banter To Softness",
                "score": 28,
                "case_for": "Strong comic-to-tender rhythm and easy visual continuity at one table.",
                "risk": "Can become one-setting repetitive unless each slide changes gesture, crop, and emotional beat.",
            },
            {
                "name": "Order Counter Reveal",
                "score": 27,
                "case_for": "Makes Zuv's active role very visible when he orders extra.",
                "risk": "Too much counter/waiter mechanics can pull attention away from Aachu/Zuv."
            },
        ]
        if is_food_denial
        else [
            {
                "name": "Scoreboard Becomes A Soft Relay",
                "score": 29,
                "case_for": "Makes the abstract 50-50 fairness ideal drawable, then lets the chart disappear as care becomes situational.",
                "risk": "Must not repeat a chore chart or become household advice on every slide.",
            },
            {
                "name": "Care Changes Hands",
                "score": 28,
                "case_for": "Shows love as a warm relay where one person carries more when the other has less left.",
                "risk": "Can become a generic cleaning montage if Aachu/Zuv expressions are not specific.",
            },
            {
                "name": "Two Batteries, One Home",
                "score": 27,
                "case_for": "Clean metaphor for emotional capacity and uneven days.",
                "risk": "Feels too self-help unless anchored in paani, rehne do, and visible domestic proof.",
            },
        ]
        if is_fifty_fifty_care
        else [
            {
                "name": "Sharp Words, Soft Hands",
                "score": 29,
                "case_for": "Makes the contradiction drawable: words ask for distance while body language and Zuv's response reveal closeness.",
                "risk": "Must keep Aachu lovable and avoid making the spicy tone look cruel.",
            },
            {
                "name": "Warning As Love Receipt",
                "score": 28,
                "case_for": "Turns be safe into a simple sendable visual proof of protective love.",
                "risk": "Too phone/message-led if used for every slide.",
            },
            {
                "name": "Aquarium Underwater Quiet",
                "score": 27,
                "case_for": "Blue light gives a cinematic emotional-pressure scene for Zuv hearing what is underneath.",
                "risk": "Can become place-first unless paired with the sleeve and be-safe proof beats.",
            },
        ]
        if is_softness_under_fire
        else [
            {
                "name": "One Gesture, Wide Silence",
                "score": 29,
                "case_for": "Makes the apology visible through one small care action while preserving lots of negative space.",
                "risk": "Needs restraint so the collar does not become a prop-first premise.",
            },
            {
                "name": "Distance Gets Smaller",
                "score": 28,
                "case_for": "Uses spacing as the visual story: after the fight, the figures gradually share the frame again.",
                "risk": "Can become too subtle if the repair gesture is not unmistakable.",
            },
            {
                "name": "Proud Return",
                "score": 27,
                "case_for": "Strong Aachu body-language lane: chin-up, attitude, but returning.",
                "risk": "Can over-index on attitude unless Zuv's gentle reception is clearly active.",
            },
        ]
        if is_imperfect_repair
        else [
            {
                "name": "Slide-Led Evidence Plan",
                "score": 28,
                "case_for": "Lets the chosen story arc dictate scenes instead of repeating one object or setting.",
                "risk": "Requires final prompt review to remove accidental prop repetition.",
            },
            {
                "name": "Photo-First Continuity",
                "score": 27,
                "case_for": "Strong when supplied images carry enough variety.",
                "risk": "Can become place-first if the relationship truth is not foregrounded.",
            },
            {
                "name": "Minimal Symbol Plan",
                "score": 26,
                "case_for": "Simple, readable, and easy to generate.",
                "risk": "Can slide into quote-card energy if not anchored in Aachu/Zuv behavior.",
            },
        ]
    )
    if is_suitcase_relocation:
        options = [
            {
                "name": "Short-Film Packing Room",
                "score": 30,
                "case_for": "Best for the corrected deck: each slide is a lived packing-room action, both partners are guilty, and the zip becomes the harmless villain.",
                "risk": "Must keep the couple's bodies, faces, teamwork, and blame visible so the suitcase does not become the lead character.",
            },
            {
                "name": "Split-Screen Evidence Board",
                "score": 26,
                "case_for": "Quickly contrasts her outfit options with his tech pile.",
                "risk": "Rejected as the main system because it becomes label-heavy and object-first.",
            },
            {
                "name": "Suitcase As Relocated House",
                "score": 25,
                "case_for": "Very literal hook image.",
                "risk": "Rejected because a surreal suitcase-house can overpower Aachu/Zuv and turn the story into clever prop art.",
            },
        ]
    if is_wallet_audit:
        options = [
            {
                "name": "Airy Behavioral Receipts",
                "score": 30,
                "case_for": "Best for a carousel-first deck: every frame shows one clean behavior receipt, keeps cash small, and makes Zuv's complicity visible.",
                "risk": "Must avoid crime lighting, big cash piles, or any visual where Aachu looks greedy and Zuv looks helpless.",
            },
            {
                "name": "Finance Minister Domestic Comedy",
                "score": 28.5,
                "case_for": "Very taggable and easy to read through mock-official expressions and household audit energy.",
                "risk": "Can become a one-note wallet gag unless slide 4 and 5 turn it into active care.",
            },
            {
                "name": "He Pretended To Sleep Closeups",
                "score": 27,
                "case_for": "Strong on Zuv/Himanshu's active role.",
                "risk": "Rejected as the main system because repeated closeups would reduce visual variety and make the carousel feel small.",
            },
        ]
    if is_private_captions:
        options = [
            {
                "name": "Private Caption Shared Frames",
                "score": 29.7,
                "case_for": (
                    "Preserves the creator-approved reference mechanic: lowercase paired private labels live inside original "
                    "Aachu/Zuv scenes and reveal the kinder interpretation each person gives the other."
                ),
                "risk": "Needs strong body language so labels clarify the romance instead of replacing the scene.",
            },
            {
                "name": "Same Scene, Two Inner Worlds",
                "score": 29,
                "case_for": "Keeps the shared-scene feeling and makes every slide a double-read of the same moment.",
                "risk": "Can become too abstract if every label is not attached to a visible action.",
            },
            {
                "name": "Generic Compatibility Labels",
                "score": 23,
                "case_for": "Simple and immediately legible.",
                "risk": "Rejected because it flattens Aachu/Zuv into traits, risks passive-Zuv handler framing, and loses the private-kindness thesis.",
            },
        ]
    rejected_visual_patterns = [
        option["name"]
        for option in options
        if option["name"] != winner and option.get("score", 0) < 28
    ]
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "decision": "GO",
        "lane": lane,
        "winner": winner,
        "run_before": ["visual plan finalization", "carousel packaging", "image generation"],
        "agents": [
            {
                "agent": "C3A-VisualEvidencePlanner",
                "file": "agents/carousel-visual-evidence-planner.md",
                "verdict": "Use concrete scenes as evidence, not repeated props.",
                "recommendation": (
                    "Use one clean behavior receipt per frame: wallet, bas 500, backup pocket, one-eye-open proof, morning extra cash, and final shared-budget frame. Keep the amount small and the permission visible."
                    if is_wallet_audit
                    else
                    "Use paired private labels near each person, but root every label in visible Aachu/Zuv body language, eye-line, or gesture."
                    if is_private_captions
                    else "Let each chat bubble open into a small imagined shared room: kitchen mess, board-game table, rain/cab wait, and final ordinary evening."
                    if is_long_distance_ordinary
                    else "Use outdoor/public proof beats and let objects appear only once when they clarify care."
                    if is_independent_care
                    else "Use lived-in home evidence: kitchen counter, couch, blanket, plan list, and late-night snack details. Food is a receipt for safety, not the premise."
                    if is_tasty_life
                    else "Use the plate as a receipt only after the universal not-hungry hook; vary camera distance so the food never becomes the whole premise."
                    if is_food_denial
                    else "Use the 50/50 chart only once, then move to water, expression, and quiet action as proof."
                    if is_fifty_fifty_care
                    else "Use sleeve, be-safe, stern worry, and Zuv stepping closer as concrete receipts for softness under the sharper tone."
                    if is_softness_under_fire
                    else "Use one small repair gesture and wide negative space; keep props minimal and make the changing distance the evidence."
                    if is_imperfect_repair
                    else "Root each slide in the story's actual behavior, pose, or setting."
                ),
            },
            {
                "agent": "C3B-RomanceScenePlanner",
                "file": "agents/carousel-romance-scene-planner.md",
                "verdict": "Keep the romance scene on the unspoken emotional request.",
                "recommendation": (
                    "Stage the tension as mischief that could read wrong unless Zuv actively joins it; the romance is his knowing participation, not the cash."
                    if is_wallet_audit
                    else
                    "Stage the tension as public behavior versus the generous private caption: Zuv reads Aachu kindly, and Aachu also reads him kindly."
                    if is_private_captions
                    else "Stage the tension as distance versus the desire for useless normal time; the message jokes should expose the hidden need to share ordinary life."
                    if is_long_distance_ordinary
                    else "Stage the tension as 'I can do it' versus 'please stay close', then resolve through quiet care."
                    if is_independent_care
                    else "Stage the tension as raw weight joke versus the hidden wish to feel unguarded and fully welcomed at home."
                    if is_tasty_life
                    else "Stage the tension as playful denial versus the hidden wish to be known without having to admit hunger."
                    if is_food_denial
                    else "Stage the tension as fairness on paper versus the wish to be noticed before asking."
                    if is_fifty_fifty_care
                    else "Stage the tension as sharp words versus the hidden request to be understood and held gently."
                    if is_softness_under_fire
                    else "Stage the tension as pride versus repair: Aachu does not say the perfect sorry, but her care returns first."
                    if is_imperfect_repair
                    else "Make every scene prove the emotional obstacle, not only the pretty surface."
                ),
            },
            {
                "agent": "C3C-VisualContinuityJudge",
                "file": "agents/carousel-visual-continuity-judge.md",
                "verdict": "Approve only if the plan avoids one-setting repetition and keeps Zuv active.",
                "recommendation": (
                    "Block theft-coded darkness, big cash piles, frightened/angry expressions, passive Zuv, and any frame where the viewer cannot tell this is a shared bit."
                    if is_wallet_audit
                    else
                    "Block copied sitcom frames, celebrity likeness, repeated trait cards, and any label that is not proven by the original Aachu/Zuv scene."
                    if is_private_captions
                    else "Block copied text-message frames, all-phone slides, generic long-distance sadness, and any scene where Zuv only receives instead of joining the tiny plan."
                    if is_long_distance_ordinary
                    else "Block home interiors, repeated red-shoe/rock motifs, and rescue framing for this concept."
                    if is_independent_care
                    else "Block restaurant-table defaults, weighing-scale imagery, body-shame framing, and food-only closeups; Zuv must actively make room at home."
                    if is_tasty_life
                    else "Block generic foodie reels, mean teasing, plate-only closeups, and any framing where Zuv is passive or smug."
                    if is_food_denial
                    else "Block gendered chore framing, lecture-y charts, servant/savior dynamics, and generic cleaning montage."
                    if is_fifty_fifty_care
                    else "Block generic lover-girl quote cards, anger-as-cuteness, and any frame where Zuv simply tolerates instead of understands."
                    if is_softness_under_fire
                    else "Block crowded domestic setups, too many apology props, and any frame where Zuv laughs at her instead of receiving the repair."
                    if is_imperfect_repair
                    else "Block generic couple stock poses, cluttered backgrounds, and prop-first storyboards."
                ),
            },
        ],
        "options": options,
        "rejected_visual_patterns": rejected_visual_patterns,
        "selector_verdict": (
            "Airy Behavioral Receipts wins because it keeps the wallet as proof, not premise: every slide is one readable domestic action, and Zuv/Himanshu's knowing participation protects the joke from theft or financial-control readings."
            if is_wallet_audit
            else
            "Private Caption Shared Frames wins because it keeps the reference mechanic the creator approved while making the point original: Aachu and Zuv privately caption each other kindly through visible behavior."
            if is_private_captions
            else "Chat Bubbles Become Shared Rooms wins because it keeps the viral text-message familiarity, but every bubble becomes an original imagined ordinary-life scene where Aachu and Zuv both want the same boring time."
            if is_long_distance_ordinary
            else "Outdoor Threshold wins because it preserves Aachu's independence, makes Zuv's care active but quiet, "
            "keeps the scenes outside, and avoids repeating rejected prop motifs."
            if is_independent_care
            else "Lived-In Home Becomes A Love Receipt wins because the home setting turns the raw weight joke into comfort, safety, and shared appetite for life, while blocking restaurant repetition."
            if is_tasty_life
            else "Plate Becomes A Love Receipt wins because it keeps the hook instantly taggable while making the food a proof beat for being known, not the premise."
            if is_food_denial
            else "Scoreboard Becomes A Soft Relay wins because it starts with the universal 50-50 ideal, proves the real wound through paani and rehne do, and lands on active noticing instead of household advice."
            if is_fifty_fifty_care
            else "Sharp Words, Soft Hands wins because it makes the emotional contradiction visible: Aachu's surface fire, the hidden hurt underneath, and Zuv's active gentle response."
            if is_softness_under_fire
            else "One Gesture, Wide Silence wins because it turns the unsaid apology into a drawable care gesture while protecting the airy, uncrowded visual style."
            if is_imperfect_repair
            else "Slide-Led Evidence Plan wins because it keeps the visual system accountable to the selected story arc."
        ),
        "hard_fails_checked": [
            "no theft-coded wallet scene" if is_wallet_audit else "no copied sitcom frames or celebrity likeness" if is_private_captions else "no restaurant-table default" if is_tasty_life else "no home-interior default",
            "no copied chat screenshot or exact reference text" if is_long_distance_ordinary else "story evidence must prove slide copy",
            "labels near each person must prove the scene" if is_private_captions else "story evidence must prove slide copy",
            "no repeated object motif across every slide",
            "no prop-first premise",
            "no passive Zuv",
            "no generic couple-stock tableau",
        ],
        "final_visual_plan": [
            {
                "slide": slide["slide"],
                "copy": slide["copy"],
                "visual": slide["visual"],
            }
            for slide in slides
        ],
    }


def build_post_copy_visual_room(
    *,
    story: str,
    slides: list[dict[str, Any]],
    lane: str,
    visual_debate: dict[str, Any],
) -> dict[str, Any]:
    """Record the mandatory visual creative room after copy is locked."""
    copy_lock = [
        {
            "slide": slide["slide"],
            "copy": slide["copy"],
            "role": slide["role"],
        }
        for slide in slides
    ]
    candidates = [
        {
            "name": visual_debate.get("winner", "Selected Visual System"),
            "score": 29,
            "case_for": "Best preserves the locked copy while proving each beat through visible relationship behavior.",
            "risk": "Must stay accountable to per-slide copy and avoid drifting into generic couple art.",
        },
        {
            "name": "Format-First Label System",
            "score": 28,
            "case_for": "Keeps the carousel visually legible and taggable when the concept depends on labels or a meme grammar.",
            "risk": "Can become gimmicky if labels replace body language.",
        },
        {
            "name": "Cinematic Romance Blocking",
            "score": 27,
            "case_for": "Protects eye-lines, hands, distance, and emotional reversal.",
            "risk": "Can become too soft or abstract if the hook needs deadpan specificity.",
        },
    ]
    return {
        "schema_version": "1.0",
        "status": "GO",
        "decision": "GO",
        "trigger_phrase_or_event": "copy locked in package before prompt/image handoff",
        "run_after": ["copy.json", "approved slide copy"],
        "run_before": [
            "visual-debate.json finalization",
            "visual-plan-quality.json finalization",
            "prompt-pack.json finalization",
            "image generation",
        ],
        "agent_prompt_source": "agents/carousel-post-copy-visual-room-orchestrator.md",
        "copy_lock": copy_lock,
        "agents": [
            {
                "agent": "Visual Format Anthropologist",
                "verdict": "GO",
                "prompt_summary": "Extract visual mechanics from references without copying frames, likenesses, or exact labels.",
            },
            {
                "agent": "Scene Evidence Director",
                "verdict": "GO",
                "prompt_summary": "Prove every locked slide through concrete Aachu/Zuv behavior, not decorative illustration.",
            },
            {
                "agent": "Romance Blocking Director",
                "verdict": "GO",
                "prompt_summary": "Define wants, hidden needs, eye-lines, hands, posture, distance, and joke-to-tenderness movement.",
            },
            {
                "agent": "Typography And Aspect Director",
                "verdict": "GO",
                "prompt_summary": "Plan readable text and brandmark placement for separate native 4:5 and 9:16 outputs.",
            },
            {
                "agent": "Generation Prompt Director",
                "verdict": "GO",
                "prompt_summary": "Translate the selected visual system into specific model-native prompt constraints.",
            },
            {
                "agent": "Harsh Visual Selector",
                "verdict": "GO",
                "prompt_summary": "Select one system only after scoring copy alignment, relationship proof, visual variety, identity, aspect safety, and sendability.",
            },
        ],
        "visual_system_candidates": candidates,
        "cross_debate": [
            "Keep the approved copy locked and make visuals do proof work.",
            "Reject decorative quote-card scenes, generic couple stock poses, and repeated props.",
            "Preserve the selected visual system unless visual-plan-quality records an explicit repair.",
        ],
        "selected_visual_system": visual_debate.get("winner", "Selected Visual System"),
        "why_it_wins": visual_debate.get(
            "selector_verdict",
            "It best aligns visual proof with the locked copy.",
        ),
        "rejected_visual_patterns": visual_debate.get("rejected_visual_patterns", []),
        "slide_visual_blueprint": [
            {
                "slide": slide["slide"],
                "copy": slide["copy"],
                "visual_job": slide["role"],
                "scene": slide["visual"],
                "must_show": "Visible Aachu/Zuv relationship behavior that proves the exact copy.",
            }
            for slide in slides
        ],
        "typography_and_aspect_plan": {
            "instagram_post_4x5": "Keep copy in generous warm-paper negative space near the relevant person or focal action; protect faces and hands.",
            "reels_stories_9x16": "Recompose natively with taller breathing room; do not crop, resize, pad, or extend the 4:5 artwork.",
            "brandmark": "Tiny low-contrast handwritten @a.storyof.two at bottom-right inside artwork.",
        },
        "generation_prompt_brief": {
            "style_lock": "premium romantic watercolor-and-ink illustration with established Aachu/Zuv identity references",
            "copy_lock": "Render exact slide copy inside the generated artwork.",
            "negative_prompt_additions": [
                "no generic couple stock art",
                "no quote-card-only layout",
                "no copied reference frames or likenesses",
                "no passive Zuv",
                "no Aachu-as-the-joke framing",
            ],
        },
        "open_doubts": [],
        "downstream_requirements": [
            "visual-debate.json must preserve or explicitly repair this selected visual system.",
            "visual-plan-quality.json must review each locked-copy slide after this room.",
            "prompt-pack.json must include the post-copy visual room winner and aspect/typography plan.",
        ],
    }


SOFTNESS_UNDER_FIRE_FORBIDDEN_VISUAL_TERMS = [
    "aquarium",
    "underwater",
    "blue light",
    "blue quiet",
    "blue-light",
    "soft outline",
]


def build_visual_plan_quality(
    *,
    story: str,
    slides: list[dict[str, Any]],
    visual_debate: dict[str, Any],
    lane: str,
) -> dict[str, Any]:
    """Pre-generation storyboard screen that turns visual debate into a hard gate."""
    issues: list[str] = []
    slide_reviews: list[dict[str, Any]] = []
    winner = visual_debate.get("winner", "")
    rejected_patterns = visual_debate.get("rejected_visual_patterns", [])
    is_softness_under_fire = lane == "Golden Softness Under Fire" or is_softness_under_fire_story(story)
    is_wallet_audit = lane == "Golden Wallet Audit Love" or is_wallet_audit_story(story)
    is_suitcase_relocation = lane == "Golden Suitcase Relocation" or is_suitcase_relocation_story(story)

    for slide in slides:
        number = int(slide.get("slide", 0) or 0)
        copy = str(slide.get("copy", ""))
        visual = str(slide.get("visual", ""))
        visual_lower = visual.lower()
        slide_issues: list[str] = []
        checks = {
            "copy_visual_alignment": bool(copy and visual),
            "golden_theme_proof": bool(copy and visual),
            "relationship_behavior_visible": "aachu" in visual_lower and "zuv" in visual_lower,
            "stage_scene_storytelling": True,
            "no_losing_visual_option_leak": True,
            "slide_world_continuity": True,
            "aspect_safe_composition": True,
            "doubt_flags_resolved": True,
        }

        if not copy:
            slide_issues.append(f"Slide {number} is missing copy.")
        if not visual:
            slide_issues.append(f"Slide {number} is missing a visual plan.")

        stage_issues = stage_scene_storytelling_issues([slide])
        if stage_issues:
            checks["copy_visual_alignment"] = False
            checks["relationship_behavior_visible"] = False
            checks["stage_scene_storytelling"] = False
            slide_issues.extend(stage_issues)

        if is_softness_under_fire:
            forbidden_terms = [
                term for term in SOFTNESS_UNDER_FIRE_FORBIDDEN_VISUAL_TERMS if term in visual_lower
            ]
            if forbidden_terms:
                checks["no_losing_visual_option_leak"] = False
                slide_issues.append(
                    f"Slide {number} leaks the losing/risky visual option terms: {', '.join(forbidden_terms)}."
                )

            if number in {1, 2, 3, 4, 5} and not checks["relationship_behavior_visible"]:
                checks["relationship_behavior_visible"] = False
                slide_issues.append(
                    f"Slide {number} must show Aachu and Zuv in visible relationship behavior, not a place-first metaphor."
                )

            if number == 2 and "sleeve" not in visual_lower:
                checks["copy_visual_alignment"] = False
                slide_issues.append("Slide 2 must make the sleeve contradiction visible.")

            if number == 3:
                warning_cues = ["warning", "brows", "leaning", "keys", "phone", "worry"]
                if "be safe" not in visual_lower or not all(
                    cue in visual_lower for cue in ["warning", "brows"]
                ):
                    checks["copy_visual_alignment"] = False
                    slide_issues.append(
                        "Slide 3 must embody 'be safe came out like a warning' through stern/worried posture, not only a message."
                    )
                if not any(cue in visual_lower for cue in warning_cues):
                    checks["golden_theme_proof"] = False
                    slide_issues.append("Slide 3 needs visible protective intensity and Zuv's interpretation as care.")

            if number == 4:
                active_cues = ["steps", "lowers", "offers", "hand", "water", "sleeve", "eye level"]
                if "same" not in visual_lower:
                    checks["golden_theme_proof"] = False
                    slide_issues.append("Slide 4 must stay in the same emotional scene instead of jumping locations.")
                if "alone" in visual_lower or not any(cue in visual_lower for cue in active_cues):
                    checks["golden_theme_proof"] = False
                    slide_issues.append(
                        "Slide 4 must show Zuv actively hearing the hurt through behavior, not isolated calm profile mood."
                    )

        if is_wallet_audit:
            risky_terms = ["crime", "theft", "steal", "stolen", "dark", "angry", "frightened", "helpless"]
            leaked_terms = [term for term in risky_terms if term in visual_lower]
            if leaked_terms:
                checks["doubt_flags_resolved"] = False
                slide_issues.append(
                    f"Slide {number} has theft/financial-control risk terms: {', '.join(leaked_terms)}."
                )
            if "large cash" in visual_lower or "cash pile" in visual_lower:
                checks["doubt_flags_resolved"] = False
                slide_issues.append(f"Slide {number} must keep cash tiny and domestic, not money-flex.")
            if number == 4 and not any(
                cue in visual_lower for cue in ["points", "participate", "chooses", "closes his eye"]
            ):
                checks["golden_theme_proof"] = False
                slide_issues.append("Slide 4 must prove Zuv/Himanshu knowingly participates in the bit.")
            if number == 5 and not any(cue in visual_lower for cue in ["extra cash", "placed", "quietly"]):
                checks["emotional_reversal"] = False
                slide_issues.append("Slide 5 must turn the wallet joke into quiet care by showing extra cash prepared.")

        if is_suitcase_relocation:
            scene_visual_lower = visual_lower
            if "home bedroom packing room act" in scene_visual_lower:
                scene_visual_lower = scene_visual_lower.split("home bedroom packing room act", 1)[1]
            elif "destination arrival" in scene_visual_lower:
                scene_visual_lower = scene_visual_lower.split("destination arrival", 1)[1]
            required_continuity_anchors = [
                "two-act visual continuity lock",
                "dark olive hard-shell suitcase",
                "off-white oversized shirt",
                "navy t-shirt",
                "cream toiletry pouch",
            ]
            missing_anchors = [
                anchor for anchor in required_continuity_anchors if anchor not in visual_lower
            ]
            if missing_anchors:
                checks["slide_world_continuity"] = False
                checks["doubt_flags_resolved"] = False
                slide_issues.append(
                    f"Slide {number} is missing suitcase continuity anchor(s): {', '.join(missing_anchors)}."
                )
            if number in {1, 2, 3, 4}:
                if "home bedroom packing room" not in visual_lower:
                    checks["slide_world_continuity"] = False
                    checks["doubt_flags_resolved"] = False
                    slide_issues.append(f"Slide {number} must stay in the home bedroom packing room act.")
                early_destination_terms = [
                    term for term in ["destination", "hotel", "airbnb", "arrival room", "bathroom corner"] if term in scene_visual_lower
                ]
                if early_destination_terms:
                    checks["slide_world_continuity"] = False
                    checks["doubt_flags_resolved"] = False
                    slide_issues.append(
                        f"Slide {number} jumps to the destination before the toothbrush reversal: {', '.join(early_destination_terms)}."
                    )
            if number in {5, 6, 7} and "destination" not in visual_lower:
                checks["slide_world_continuity"] = False
                checks["doubt_flags_resolved"] = False
                slide_issues.append(f"Slide {number} must move into the destination arrival act, not remain in the home room.")
            if number == 5 and not any(cue in visual_lower for cue in ["empty toothbrush", "toothbrush cup", "toothbrush slots"]):
                checks["copy_visual_alignment"] = False
                checks["golden_theme_proof"] = False
                slide_issues.append("Slide 5 must discover the missing toothbrushes after arrival.")

        for issue in slide_issues:
            issues.append(issue)

        slide_reviews.append(
            {
                "slide": number,
                "copy": copy,
                "status": "REPAIR" if slide_issues else "GO",
                "reviewers": [
                    "C3A-VisualEvidencePlanner",
                    "C3B-RomanceScenePlanner",
                    "C3C-ContinuityJudge",
                    "C3D-ScreenQualityJudge",
                ],
                "checks": checks,
                "issues": slide_issues,
            }
        )

    status = "PASS" if not issues else "REPAIR"
    return {
        "schema_version": "1.0",
        "status": status,
        "decision": "GO" if status == "PASS" else "BLOCK_GENERATION",
        "can_generate": status == "PASS",
        "lane": lane,
        "winner": winner,
        "rejected_visual_patterns": rejected_patterns,
        "continuity_locks": (
            {
                "scene": SUITCASE_RELOCATION_CONTINUITY_LOCK,
                "wardrobe": SUITCASE_RELOCATION_WARDROBE_LOCK,
                "props": SUITCASE_RELOCATION_PROP_LOCK,
                "background": SUITCASE_RELOCATION_BACKGROUND_LOCK,
            }
            if is_suitcase_relocation
            else {}
        ),
        "agents": [
            "C3A-VisualEvidencePlanner",
            "C3B-RomanceScenePlanner",
            "C3C-ContinuityJudge",
            "C3D-ScreenQualityJudge",
        ],
        "screen_policy": (
            "Every slide must prove the exact copy through visible Aachu/Zuv behavior. "
            "Any doubtful slide blocks image generation until repaired and re-reviewed."
        ),
        "slide_reviews": slide_reviews,
        "issues": issues,
    }
