from pipeline.stages.carousel_visual_rooms import build_visual_plan_quality
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
