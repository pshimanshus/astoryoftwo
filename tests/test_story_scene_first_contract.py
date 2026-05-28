from pipeline.stages.carousel_visual_rooms import build_visual_plan_quality
from pipeline.stages.carousel_lanes import (
    build_slides,
    build_suitcase_relocation_concept_selection,
    classify_content_lane,
)
from pipeline.stages.successful_carousel_standard import evaluate_successful_carousel_standard


def test_successful_standard_rejects_text_driven_poster_spine_even_with_high_scores():
    package = {
        "concept": {
            "story_selling_decision": {"score": {"total": 30}},
            "successful_carousel_standard_alignment": {
                "success_goals_addressed": [
                    "public identity mirror",
                    "concrete couple receipts",
                    "active Zuv care",
                    "emotional reversal",
                    "send/save thesis",
                ]
            },
        },
        "slides": [
            {
                "slide": 1,
                "copy": "Some couples don't pack. They relocate the house.",
                "role": "hook",
                "visual": "Aachu and Zuv stand beside a suitcase with the hook written large above them.",
                "emotion": "funny",
                "cta_intent": "tag overpackers",
            },
            {
                "slide": 2,
                "copy": "She packed just options.",
                "role": "proof",
                "visual": "Aachu and Zuv smile beside text explaining she packed options.",
                "emotion": "playful",
                "cta_intent": "tag overpackers",
            },
            {
                "slide": 3,
                "copy": "He packed chargers for gadgets they don't own.",
                "role": "proof",
                "visual": "Aachu and Zuv stand in a warm scene while the text carries the joke.",
                "emotion": "playful",
                "cta_intent": "tag overpackers",
            },
            {
                "slide": 4,
                "copy": "Maybe love is two overpackers blaming the zip.",
                "role": "save/share thesis",
                "visual": "A quote-card style final image with Aachu and Zuv added near the suitcase.",
                "emotion": "tender",
                "cta_intent": "tag overpackers",
            },
        ],
        "prompt_pack": {
            "successful_carousel_standard": {
                "source": "wiki/insights/successful-carousel-standard.md"
            }
        },
        "review": {"story_selling_score": {"total": 30}},
    }

    result = evaluate_successful_carousel_standard(package, slide_count=4)

    assert result["status"] == "REPAIR"
    assert not result["pass"]
    assert not result["dimensions"]["stage_scene_storytelling"]["pass"]
    assert "text-driven" in " ".join(result["issues"]).lower()


def test_visual_plan_quality_blocks_quote_card_visuals_with_characters_added_later():
    slides = [
        {
            "slide": 1,
            "copy": "Some couples don't pack. They relocate the house.",
            "role": "hook",
            "visual": "Quote-card poster: Aachu and Zuv stand beside a suitcase while the text explains the concept.",
            "emotion": "funny",
        },
        {
            "slide": 2,
            "copy": "She packed just options.",
            "role": "proof",
            "visual": "Aachu and Zuv smile near luggage; no action, the text carries the joke.",
            "emotion": "playful",
        },
        {
            "slide": 3,
            "copy": "Both blamed the zip.",
            "role": "reversal",
            "visual": "Aachu and Zuv are beside a bag, with poster text explaining both blamed the zip.",
            "emotion": "playful",
        },
        {
            "slide": 4,
            "copy": "Maybe love is two overpackers blaming the zip.",
            "role": "save/share thesis",
            "visual": "Final quote-card with generic couple art and the thesis as the main image.",
            "emotion": "tender",
        },
    ]

    quality = build_visual_plan_quality(
        story="A couple overpacks before a trip and blames the suitcase zip.",
        slides=slides,
        visual_debate={"winner": "Poster Copy Spine", "rejected_visual_patterns": []},
        lane="Tiny Rituals",
    )

    assert quality["status"] == "REPAIR"
    assert quality["decision"] == "BLOCK_GENERATION"
    assert not quality["can_generate"]
    assert "stage" in " ".join(quality["issues"]).lower()


def test_suitcase_relocation_uses_real_mutual_overpacking_receipts():
    story = (
        "Suitcase Relocation. Some couples don't pack. They relocate the house. "
        "She packed just options. He packed every charger except the one they needed. "
        "They sat on the suitcase. Still forgot toothbrushes. Nobody blamed each other. Only the zip."
    )

    assert classify_content_lane(story) == "Golden Suitcase Relocation"

    slides = build_slides(story, [], 7)
    copies = [slide["copy"] for slide in slides]
    visuals = " ".join(slide["visual"] for slide in slides).lower()

    assert "He packed every charger except the one they needed." in copies
    assert "Nobody blamed each other. Only the zip." in copies
    assert "chargers for gadgets" not in " ".join(copies).lower()
    assert "chargers for gadgets" not in visuals
    assert any("both" in slide["visual"].lower() and "suitcase" in slide["visual"].lower() for slide in slides)


def test_suitcase_relocation_uses_two_act_visual_continuity_not_one_room():
    story = (
        "Suitcase Relocation. Some couples don't pack. They relocate the house. "
        "She packed just options. He packed every charger except the one they needed. "
        "They sat on the suitcase. Still forgot toothbrushes. Nobody blamed each other. Only the zip."
    )

    slides = build_slides(story, [], 7)
    by_number = {slide["slide"]: slide["visual"].lower() for slide in slides}

    for number in [1, 2, 3, 4]:
        assert "home bedroom packing room" in by_number[number]
        assert "home bedroom packing room act" in by_number[number]
    for number in [5, 6, 7]:
        assert "destination" in by_number[number]
        assert "destination arrival" in by_number[number]
    assert "empty toothbrush" in by_number[5]

    for anchor in [
        "two-act visual continuity lock",
        "dark olive hard-shell suitcase",
        "off-white oversized shirt",
        "navy t-shirt",
        "cream toiletry pouch",
    ]:
        assert all(anchor in slide["visual"].lower() for slide in slides)


def test_suitcase_relocation_visual_quality_blocks_slide_world_drift():
    drifted_slides = [
        {
            "slide": 1,
            "copy": "Some couples don't pack. They relocate the house.",
            "role": "universal hook",
            "visual": "Aachu and Zuv stand beside an open suitcase in a bedroom.",
            "emotion": "instant recognition",
        },
        {
            "slide": 2,
            "copy": "She packed \"just options.\"",
            "role": "aachu-specific proof",
            "visual": "Aachu holds outfit options in a bedroom while Zuv watches.",
            "emotion": "playful denial",
        },
        {
            "slide": 3,
            "copy": "He packed every charger except the one they needed.",
            "role": "zuv-specific proof",
            "visual": "Zuv shows a charger pile in a destination hotel bathroom while Aachu judges him.",
            "emotion": "mutual judgment",
        },
    ]

    quality = build_visual_plan_quality(
        story="Suitcase Relocation with forgotten toothbrushes and a blamed zip.",
        slides=drifted_slides,
        visual_debate={"winner": "Short-Film Packing Room", "rejected_visual_patterns": []},
        lane="Golden Suitcase Relocation",
    )

    assert quality["status"] == "REPAIR"
    assert quality["decision"] == "BLOCK_GENERATION"
    assert not quality["can_generate"]
    assert "continuity" in " ".join(quality["issues"]).lower()


def test_suitcase_relocation_visual_quality_allows_arrival_discovery_after_packing():
    slides = build_slides(
        (
            "Suitcase Relocation. Some couples don't pack. They relocate the house. "
            "She packed just options. He packed every charger except the one they needed. "
            "They sat on the suitcase. Still forgot toothbrushes. Nobody blamed each other. Only the zip."
        ),
        [],
        7,
    )

    quality = build_visual_plan_quality(
        story="Suitcase Relocation with forgotten toothbrushes and a blamed zip.",
        slides=slides,
        visual_debate={"winner": "Short-Film Packing Room", "rejected_visual_patterns": []},
        lane="Golden Suitcase Relocation",
    )

    assert quality["status"] == "PASS"
    assert quality["decision"] == "GO"
    assert quality["can_generate"]


def test_suitcase_relocation_concept_selection_bans_rejected_charger_joke():
    selection = build_suitcase_relocation_concept_selection()
    serialized = str(selection).lower()

    assert selection["winner"] == "Blame The Zip, Not Each Other"
    assert selection["winner_score"] >= 29
    assert "he packed every charger except the one they needed" in serialized
    assert "chargers for gadgets" not in serialized
