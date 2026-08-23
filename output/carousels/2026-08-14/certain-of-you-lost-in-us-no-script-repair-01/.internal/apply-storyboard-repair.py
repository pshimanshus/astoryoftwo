from __future__ import annotations

import json
from pathlib import Path


PACKAGE = Path("output/carousels/2026-08-14/certain-of-you-lost-in-us-no-script-repair-01")


SCENES = {
    4: (
        "OBJECT-DOMINANT HIGH OVER-TABLE CLOSE INSERT during rehearsal blackout, widened only enough to establish the next cue. Exactly Aachu and Zuv are present, but the open blank rehearsal script is the hero object in the lower-middle frame. Aachu appears as a clean partial shoulder, hair edge and soft profile at viewer-left; Zuv's full three-quarter face is readable beyond the pages at viewer-right. Aachu uses exactly one visible right hand to lift and turn the completely blank right ivory page while Zuv uses exactly one visible left index finger and palm to press the completely blank left page corner flat—two clearly separate hands from two clearly separate owners on opposite sides of the central spread. No letters, lines, title, symbols, staff marks or print appear anywhere on either page. Along the far wall, one single straight taut indigo theatre fly-line runs vertically flush into a clearly visible metal wall cleat; it has no free-hanging section, loop, knot, curve, coil, rope end or noose-like silhouette. A narrow strip of the still-hanging indigo curtain is visible at the far edge. One distant ghost light glows between them, while hands, pages, table edge, wall line, curtain, hair and torsos remain spatially separate. Reserve generous clean upper paper for exact copy. No other person, extra chair, audience, crew, reflection, silhouette, clock, speech bubble, heart, label, sign, or random text."
    ),
    5: (
        "LOW SIDE-STAGE MEDIUM-WIDE RECOVERY ACTION immediately after a scene change fails. Exactly Aachu and Zuv kneel at the same depth on opposite sides of the same fallen indigo curtain, which lies safely on the bare stage floor and never wraps around either body. Aachu uses exactly one visible inside hand to lift the left curtain corner; Zuv uses exactly one visible inside hand to lift the right curtain corner. They actively fold the two separately owned corners toward the same center, creating one shallow fabric ridge and two short fresh dust marks beneath the moving cloth. The fold lands slightly crooked, and at that exact active moment both turn their heads toward each other and begin the same small exhausted laugh. Their outside hands remain fully outside the crop. The same closed script rests on the separate rehearsal table in the middle background as a featureless dark-indigo book with a completely blank cover—no title, label, symbol, marks or letters. No loose line, loop, rope, coil or hanging cord appears anywhere. Pale ghost-light rims keep Aachu's black hair and overshirt and Zuv's white jacket separate from curtain and floor. Clean upper paper for copy. No chair, embrace, rescue gesture, audience, extra person, reflection, silhouette, duplicate limb, halo, heart, label, sign, or random text."
    ),
    6: (
        "ACTIVE PAYOFF AND COVER ECHO, HIGH REAR THREE-QUARTER MEDIUM-WIDE from just above the stage lip. Exactly Aachu and Zuv stand at the same depth behind the two plain rehearsal chairs that began in opposite wings. Each person uses exactly one inside hand to pull their own chair by its backrest toward the same new pale-peach pool of light; Aachu owns the left chair with her right hand and Zuv owns the right chair with his left hand. Their outside hands remain fully outside the crop. The chairs angle slightly inward and are visibly still moving; one short fresh skid of chalky dust sits immediately behind each chair leg, with no long trail, rope, map line or path. Their shoulders and forward direction echo the cover, and the same indigo and dusty-rose scenery flats again slide apart in the far background, now leaving one shared open center. The fallen indigo curtain remains pooled safely behind them beside the separate rehearsal table. On that table, the same closed script appears only as a small featureless dark-indigo book with a completely blank cover—no title, label, icon, mark, line, symbol, letter or suggestive pseudo-text of any kind. Both look toward the same newly illuminated footlight and unfinished center, with a readable small side glance beginning between them. Keep every chair, book, table and scenery boundary separate from legs, hands and clothing. Keep the upper-middle ivory paper clean for copy. Exactly two people; no audience, silhouettes, reflections, crew, finished home, destination, applause, heart-shaped light, map, blueprint, arrow, sign, labels, or random text."
    ),
}


SLIDE_DETAILS = {
    4: {
        "pose": "Asymmetric high over-table insert: Aachu turns the blank right page with her right hand while Zuv's separate left index finger and palm press the blank left page corner flat; all other hands stay outside frame.",
        "props": "one small rehearsal table, one open completely blank script, one straight taut fly-line fixed flush into a metal wall cleat, one narrow still-hanging curtain edge, one distant ghost light",
        "continuity_lock": "The blank-script hero frame reveals no instruction while a straight wall-fixed fly-line and still-hanging curtain establish the next technical cue without any hanging loop or self-harm silhouette.",
        "cta_intent": "They actively search and turn the page together, but no instruction appears.",
    },
    5: {
        "pose": "Same-depth kneeling recovery two-shot: each lifts one separate curtain corner toward center with one inside hand as their crooked fold triggers reciprocal exhausted laughter; exactly two visible hands total.",
        "props": "the same fallen indigo curtain actively being folded; the same featureless closed blank script on the separate rehearsal table; no rope, line, loop, coil or hanging cord",
        "continuity_lock": "The prior technical cue has visibly failed; both people now handle the aftermath with equal agency while the blank script stays behind on its own table.",
        "cta_intent": "Their shared action changes the meaning of failure without pretending the stage is fixed.",
    },
    6: {
        "props": "the same two rehearsal chairs actively converging, one short local skid behind each chair, one next footlight, the same opposing scenery flats, pooled fallen curtain, separate rehearsal table and one small featureless closed blank script",
        "continuity_lock": "Separate chairs -> shared light -> handled demands -> blank script and fixed cue -> visible curtain failure -> shared recovery -> both actively move one chair into the next light as the cover's opposing scenery movement returns.",
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


prompt_path = PACKAGE / "prompt-pack.json"
prompt_pack = read_json(prompt_path)
for record in prompt_pack["slides"]:
    number = int(record["slide"])
    if number in SCENES:
        record["scene"] = SCENES[number]
        record["visual"] = SCENES[number]
write_json(prompt_path, prompt_pack)

slides_path = PACKAGE / "slides.json"
slides = read_json(slides_path)
for record in slides:
    number = int(record["slide"])
    if number in SCENES:
        record["visual"] = SCENES[number]
        record.update(SLIDE_DETAILS[number])
write_json(slides_path, slides)

cards_path = PACKAGE / ".internal/event-a-blind-cards.json"
cards = read_json(cards_path)
card_updates = {
    4: {
        "visible_setting": "A small rehearsal table during stage blackout, with one distant ghost light, one straight taut indigo fly-line fixed flush into a metal wall cleat, and a narrow edge of the still-hanging curtain.",
        "observable_action": "The woman lifts and turns the completely blank right script page with her right hand while the man's separate left index finger and palm press the completely blank left page corner flat.",
        "hands_and_contact": "Exactly two focal hands from two separate owners are visible on opposite sides of the spread, one turning a page and one pressing the other page flat; all other hands remain outside frame.",
        "gaze": "Both gazes remain on the empty spread as their two active hands search for an instruction that is not there.",
        "body_blocking": "One partial foreground presence and one readable background face sit on opposite sides of the central script; both separate hands, pages, table and bodies stay spatially distinct.",
        "object_state": "The two ivory pages are completely blank. One single straight taut fly-line is fixed vertically and flush into a visible wall cleat, with no loose section, loop, knot, curve, coil or hanging end. A narrow curtain edge and one ghost light remain.",
        "visible_continuity": "The same pair and dusty wardrobe; shared light has fallen to blackout, the technical line is visibly fixed, and the script supplies no answer.",
    },
    5: {
        "visible_setting": "Bare side-stage floor immediately after an indigo curtain has collapsed safely, with a separate rehearsal table in the middle background.",
        "observable_action": "They kneel on opposite sides of the fallen curtain and actively lift one separately owned corner each toward the same center; the fold lands crooked and both begin the same tired laugh.",
        "hands_and_contact": "Exactly two inside hands are visible, one per person gripping only that person's curtain corner; all outside hands stay outside crop.",
        "gaze": "Their eye-lines meet directly at the instant the crooked fold reveals the shared mishap.",
        "body_blocking": "They kneel at the same depth with bodies separate; a shallow central fabric ridge and two short fresh dust marks prove the cloth is actively moving.",
        "object_state": "The fallen curtain is being folded toward center. A small featureless dark-indigo closed script with a completely blank cover remains on the separate table. No rope, line, loop, coil or cord appears.",
        "camera_view": "Low side-stage medium-wide recovery view.",
        "visible_continuity": "The same pair and wardrobe, visible cue failure and equal shared recovery occupy one active moment.",
    },
    6: {
        "object_state": "The two chairs are nearly adjacent but still moving; one short local skid of chalky dust sits behind each chair leg. The pooled curtain and separate rehearsal table remain behind them, holding one small featureless dark-indigo closed script whose cover is completely blank and contains no marks or text.",
        "visible_continuity": "The two previously separated chairs actively converge; the recovered curtain and completely blank closed script are left behind; the opposing scenery-flat movement echoes the opening; exactly two people are present.",
    },
}
for card in cards:
    number = int(card["slide"])
    if number in card_updates:
        card.update(card_updates[number])
write_json(cards_path, cards)

print(json.dumps({"status": "updated", "slides": [4, 5, 6]}, indent=2))
