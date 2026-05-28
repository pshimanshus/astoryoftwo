"""
Codex-native carousel package builder.

This path is intentionally no-API: it turns story + reference images into the
C-layer artifact contract using local rules, and optionally renders simple
Instagram-ready stylized image exports from the supplied photos.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.c1_illustration_carousel import (
    DEFAULT_SLIDE_COUNT,
    validate_slide_count,
)
from pipeline.stages.carousel_contract import build_character_bible, load_style_contract
from pipeline.stages.carousel_master_prompt import MASTER_PROMPT_VERSION, master_prompt_contract
from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts
from pipeline.stages.carousel_style_consistency import HOUSE_STYLE_SCENE_RULE
from pipeline.stages.identity_dossier import build_identity_dossier_artifacts
from pipeline.stages.successful_carousel_standard import (
    SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT,
    SUCCESSFUL_CAROUSEL_STANDARD_PATH,
)
from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.contracts import LayerEDecision
from pipeline.layer_e.engine import run_layer_e

from pipeline.stages.carousel_lanes import (
    CAROUSEL_STORY_DIRECTOR_CONTRACT,
    FALLBACK_COMPACT_STYLE_PROMPT,
    MORNING_PERSON_TOKENS,
    STORY_SELLING_CONTRACT,
    build_fifty_fifty_care_concept_selection,
    build_food_denial_concept_selection,
    build_high_maintenance_care_concept_selection,
    build_identity_consistency_review,
    build_identity_continuity_for_slide,
    build_identity_continuity_prompt,
    build_identity_reference_selection,
    build_imperfect_repair_concept_selection,
    build_long_distance_ordinary_concept_selection,
    build_main_kar_lungi_concept_selection,
    build_pakka_reassurance_concept_selection,
    build_private_captions_concept_selection,
    build_slides,
    build_softness_under_fire_concept_selection,
    build_story_director_gate,
    build_story_selling_decision,
    build_suitcase_relocation_concept_selection,
    build_tasty_life_concept_selection,
    build_unfiltered_nonsense_concept_selection,
    build_wallet_audit_concept_selection,
    build_workday_homecoming_concept_selection,
    classify_content_lane,
    discover_identity_images,
    infer_origin,
    infer_place,
    infer_title,
    infer_workspace_root,
    is_fifty_fifty_care_story,
    is_food_denial_story,
    is_high_maintenance_care_story,
    is_imperfect_repair_story,
    is_kashmiri_language_story,
    is_long_distance_ordinary_story,
    is_main_kar_lungi_story,
    is_mood_changed_story,
    is_pakka_reassurance_story,
    is_photo_ritual_story,
    is_private_captions_story,
    is_softness_under_fire_story,
    is_suitcase_relocation_story,
    is_subtitle_language_story,
    is_tasty_life_story,
    is_unfiltered_nonsense_story,
    is_wallet_audit_story,
    is_waterfall_lantern_story,
    is_workday_homecoming_story,
    normalize_paths,
    select_identity_reference_bundle,
    slugify,
)
from pipeline.stages.carousel_package_writer import (
    build_manifest,
    try_render_assets,
    write_json,
    write_package,
)
from pipeline.stages.carousel_visual_rooms import (
    build_post_copy_visual_room,
    build_visual_debate,
    build_visual_plan_quality,
)


def build_package(
    *,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    title: str,
    slide_count: int,
    style_brief: str | None,
    layer_e_decision: LayerEDecision | None = None,
) -> dict[str, Any]:
    contract = load_style_contract()
    character_bible = build_character_bible(contract)
    lane = classify_content_lane(story)
    is_morning_person_story = any(token in story.lower() for token in MORNING_PERSON_TOKENS)
    is_photo_ritual = is_photo_ritual_story(story)
    is_subtitle_story = is_subtitle_language_story(story)
    is_mood_changed = is_mood_changed_story(story)
    is_workday_homecoming = is_workday_homecoming_story(story)
    is_high_maintenance_care = is_high_maintenance_care_story(story)
    is_pakka_reassurance = is_pakka_reassurance_story(story)
    is_softness_under_fire = is_softness_under_fire_story(story)
    is_imperfect_repair = is_imperfect_repair_story(story)
    is_main_kar_lungi = is_main_kar_lungi_story(story)
    is_fifty_fifty_care = is_fifty_fifty_care_story(story)
    is_wallet_audit = is_wallet_audit_story(story)
    is_tasty_life = is_tasty_life_story(story)
    is_food_denial = is_food_denial_story(story)
    is_private_captions = is_private_captions_story(story)
    is_unfiltered_nonsense = is_unfiltered_nonsense_story(story)
    is_long_distance_ordinary = is_long_distance_ordinary_story(story)
    is_suitcase_relocation = is_suitcase_relocation_story(story)
    if is_private_captions:
        concept_selection = build_private_captions_concept_selection()
    elif is_unfiltered_nonsense:
        concept_selection = build_unfiltered_nonsense_concept_selection()
    elif is_long_distance_ordinary:
        concept_selection = build_long_distance_ordinary_concept_selection()
    elif is_suitcase_relocation:
        concept_selection = build_suitcase_relocation_concept_selection()
    elif is_tasty_life:
        concept_selection = build_tasty_life_concept_selection()
    elif is_wallet_audit:
        concept_selection = build_wallet_audit_concept_selection()
    elif is_food_denial:
        concept_selection = build_food_denial_concept_selection()
    elif is_fifty_fifty_care:
        concept_selection = build_fifty_fifty_care_concept_selection()
    elif is_main_kar_lungi:
        concept_selection = build_main_kar_lungi_concept_selection()
    elif is_pakka_reassurance:
        concept_selection = build_pakka_reassurance_concept_selection()
    elif is_softness_under_fire:
        concept_selection = build_softness_under_fire_concept_selection()
    elif is_imperfect_repair:
        concept_selection = build_imperfect_repair_concept_selection()
    elif is_workday_homecoming:
        concept_selection = build_workday_homecoming_concept_selection()
    elif is_high_maintenance_care:
        concept_selection = build_high_maintenance_care_concept_selection()
    else:
        concept_selection = None
    place = infer_place(story)
    origin = infer_origin(story)
    slides = build_slides(story, image_paths, slide_count)
    visual_debate = build_visual_debate(story, slides, lane)
    post_copy_visual_room = build_post_copy_visual_room(
        story=story,
        slides=slides,
        lane=lane,
        visual_debate=visual_debate,
    )
    visual_plan_quality = build_visual_plan_quality(
        story=story,
        slides=slides,
        visual_debate=visual_debate,
        lane=lane,
    )
    style = style_brief or contract["shared_style_prompt"]
    compact_style = contract.get("compact_style_prompt", FALLBACK_COMPACT_STYLE_PROMPT)
    identity_paths = [str(path) for path in identity_image_paths]
    identity_dossier_references = identity_dossier.get("reference_images_for_generation", [])
    identity_selected_options = identity_dossier.get("selected_generation_options", [])
    identity_selected_option_ids = [
        str(option.get("option_id"))
        for option in identity_selected_options
        if option.get("option_id")
    ]
    face_identity_contract = identity_dossier.get("face_identity_contract", {})
    for slide in slides:
        slide["identity_continuity"] = build_identity_continuity_for_slide(slide, identity_paths)
    style_reference_paths = contract.get("style_references", [])[:3]
    brandmark = contract["brandmark"]
    golden_theme = contract.get("golden_theme_contract", {})
    golden_theme_rule = golden_theme.get(
        "rule",
        "Start from a universal relationship truth and prove it through Aachu/Zuv specifics.",
    )
    if is_private_captions:
        human_truth = (
            "The right person does not only see your public behavior; they give it the kinder private caption, "
            "and over time you learn to caption them kindly too."
        )
        emotional_arc = (
            "private-caption hook -> Aachu's dramatic/stressed/tiny-joy receipts -> Zuv's active generous readings -> "
            "Aachu's generous readings of Zuv -> mutual knownness -> captions-you-kindly thesis"
        )
        caption_recommended = (
            "some couples come with private captions.\n\n"
            "the world sees dramatic.\n"
            "your person reads: taking it seriously.\n\n"
            "the world sees stressed.\n"
            "your person reads: listening first.\n\n"
            "and sometimes he acts tough,\n"
            "and she already knows he is soft.\n\n"
            "maybe love is the person\n"
            "who captions you kindly."
        )
        caption_alt = (
            "Send this to the person who gives your dramatic, stressed, excited, tough, and silly moments the kinder caption."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#CoupleHumor",
            "#DesiCouple",
            "#EmotionalConnection",
            "#AachuAndZuv",
        ]
    elif is_unfiltered_nonsense:
        human_truth = (
            "The broadest everyday love is not being tolerated at your strangest; it is finding "
            "someone who enters your private logic, replies to every plot twist, and lets the "
            "unedited version stay wanted."
        )
        emotional_arc = (
            "nonsense anti-ideal -> five-updates proof -> mid-story escalation -> "
            "partner joins the plot -> never-nonsense reversal -> fluent-in-you thesis"
        )
        caption_recommended = (
            "marry the one who joins your nonsense.\n\n"
            "the five updates for one thought.\n"
            "the story that starts from the middle.\n"
            "the random commentary that somehow needs a full discussion.\n\n"
            "and the right person does not mute it.\n"
            "they ask follow-up questions like they were there.\n\n"
            "maybe it was never nonsense.\n"
            "maybe love is finding someone fluent in you."
        )
        caption_alt = (
            "Send this to the person who understands your five updates, mid-story starts, and private logic."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#CoupleHumor",
            "#SoftLoveNotes",
            "#DesiCouple",
            "#LoveInLittleThings",
            "#AachuAndZuv",
        ]
    elif is_long_distance_ordinary:
        human_truth = (
            "Long distance does not only make a couple miss big romantic moments; it makes them miss "
            "the boring, useless, ordinary time they would have wasted together if they were in the same room."
        )
        emotional_arc = (
            "long-distance ache -> tiny future-plan banter -> cooking/board-game/cab receipts -> "
            "Zuv joins the small wish -> ordinary-time thesis"
        )
        caption_recommended = (
            "long distance makes you miss the boring things.\n\n"
            "not just dates.\n"
            "not just trips.\n\n"
            "the ruined dinner.\n"
            "the board-game fight.\n"
            "the cab being late and both of you pretending to be annoyed.\n\n"
            "maybe closeness is not always grand romance.\n"
            "maybe it is ordinary time with you."
        )
        caption_alt = (
            "Send this to the person you do not only miss on special days. You miss wasting a normal Tuesday with them."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#LongDistanceLove",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiCouple",
            "#AachuAndZuv",
        ]
    elif is_suitcase_relocation:
        human_truth = (
            "Some couples do not pack light; they overprepare together, create the suitcase mess together, "
            "and choose a harmless villain instead of blaming each other."
        )
        emotional_arc = (
            "relocate-the-house hook -> Aachu options proof -> Zuv real charger-mess proof -> "
            "shared suitcase wrestling -> forgotten toothbrush reversal -> zip-not-each-other bridge -> "
            "two-overpackers thesis"
        )
        caption_recommended = (
            "some couples pack for a trip.\n"
            "some couples pack for every possible version of the trip.\n\n"
            "the outfit options.\n"
            "the charger pile.\n"
            "the suitcase negotiation.\n"
            "the toothbrushes, obviously forgotten.\n\n"
            "and after all that,\n"
            "nobody blamed each other.\n"
            "only the zip.\n\n"
            "send this to the person who says pack light and still sits on the suitcase with you."
        )
        caption_alt = (
            "Love is not packing perfectly. Sometimes it is two overpackers blaming the zip together."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#CoupleComedy",
            "#MarriedLife",
            "#DesiCouple",
            "#TravelWithPartner",
            "#RelationshipHumor",
        ]
    elif is_tasty_life:
        human_truth = (
            "The right love turns food from calculation into comfort and appetite-for-life, "
            "so the 55-to-70 line becomes a mischievous receipt for a life that got more loved "
            "instead of a body-shame joke."
        )
        emotional_arc = (
            "khaya hook -> aur-logi food bridge -> second serving proof -> "
            "comfort without comments -> wanting feels safe -> life-zyada-tasty thesis"
        )
        caption_recommended = (
            "some love does not make life smaller.\n\n"
            "he does not only ask, khaya?\n"
            "he asks, aur logi?\n\n"
            "and slowly the second serving stops being about food.\n"
            "it becomes comfort without comments.\n"
            "it becomes wanting without being watched.\n\n"
            "55 se 70 nahi.\n"
            "bas life zyada tasty ho gayi."
        )
        caption_alt = (
            "Maybe love is not staying the same. Maybe it is becoming safe enough to enjoy more of life."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#DesiCouple",
            "#LoveInLittleThings",
            "#CoupleHumor",
            "#AachuAndZuv",
        ]
    elif is_wallet_audit:
        human_truth = (
            "The best couples do not only tolerate each other's tiny nonsense; they quietly "
            "make room for it, budget for it, and turn the bit into a shared language."
        )
        emotional_arc = (
            "wallet-audit hook -> bas-500 proof -> backup-pocket escalation -> "
            "Zuv knowingly joins -> morning extra-cash reversal -> nonsense-has-a-budget thesis"
        )
        caption_recommended = (
            "Every couple has one finance minister.\n"
            "And one person pretending not to notice.\n\n"
            "She said bas 500.\n"
            "Then checked the backup pocket.\n\n"
            "He saw everything.\n"
            "He still pretended to sleep.\n\n"
            "By morning, he kept extra there.\n\n"
            "Maybe love is not always grand gestures.\n"
            "Sometimes it is quietly budgeting for each other's nonsense.\n\n"
            "Send this to the person who became your alibi, not your audience."
        )
        caption_alt = (
            "Send this to the person who knows your tiny nonsense and still quietly makes room for it."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#DesiCouple",
            "#CoupleComedy",
            "#MarriedLife",
            "#RelationshipHumor",
            "#AachuAndZuv",
        ]
    elif is_food_denial:
        human_truth = (
            "Love is not perfect food honesty; it is knowing the person who says they are not hungry, "
            "waiting for the best bite to prove otherwise, and ordering extra without making them confess."
        )
        emotional_arc = (
            "not-hungry anti-ideal -> Aachu's one-bite denial -> best-bite proof -> "
            "Zuv quietly orders extra -> knows-your-order thesis"
        )
        caption_recommended = (
            "some people say they are not hungry.\n\n"
            "then take one bite.\n"
            "then the best bite.\n"
            "then somehow the plate has become a shared property.\n\n"
            "and love is the person who stops arguing with the pattern\n"
            "and just orders extra.\n\n"
            "maybe love is not keeping plate score.\n"
            "maybe it is knowing your order anyway."
        )
        caption_alt = (
            "Send this to the person who says they are not hungry and then eats the best bite from your plate."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#DesiCouple",
            "#LoveInLittleThings",
            "#SoftLoveNotes",
            "#CoupleHumor",
            "#AachuAndZuv",
        ]
    elif is_fifty_fifty_care:
        human_truth = (
            "Love is not perfect 50-50 accounting; it is noticing when one person's half has become heavier "
            "and carrying the small task before the feeling has to become a whole case."
        )
        emotional_arc = (
            "50-50 anti-ideal -> Aachu's tired rehne-do proof -> paani as concrete receipt -> "
            "Zuv notices before counting -> heavier-half love thesis"
        )
        caption_recommended = (
            "50-50 sounds fair until someone has to ask for the same small thing twice.\n\n"
            "some days your half is heavier.\n"
            "some days mine is.\n\n"
            "and sometimes the fight is not about paani.\n"
            "it is about wanting to be noticed before you have to make a whole case out of it.\n\n"
            "maybe love is not keeping the perfect score.\n"
            "maybe it is seeing when your person has less left,\n"
            "and carrying the heavier half for today."
        )
        caption_alt = (
            "Maybe love is not splitting everything evenly. Maybe it is noticing when someone's half got heavier today."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiLove",
            "#MarriedLife",
            "#AachuAndZuv",
        ]
    elif is_main_kar_lungi:
        human_truth = (
            "Aachu's 'main kar lungi' is not a request for distance; it is pride asking to stay whole, "
            "and Zuv's love is the quiet care that helps without making her feel small."
        )
        emotional_arc = (
            "independent-love universal hook -> hidden don't-go-far translation -> Aachu pride proof -> "
            "Zuv's quiet public care -> care-without-a-scene thesis"
        )
        caption_recommended = (
            "main kar lungi.\n\n"
            "sometimes it means: i can do this.\n"
            "sometimes it also means: stay close, bas don't make it a scene.\n\n"
            "and he understood both.\n\n"
            "maybe love is care without making someone feel small."
        )
        caption_alt = (
            "Maybe the softest care is the kind that helps without taking over the moment."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiLove",
            "#CoupleIllustration",
            "#AachuAndZuv",
        ]
    elif is_pakka_reassurance:
        human_truth = (
            "Aachu's smallest doubts do not make her hard to love; they reveal the softest "
            "part of her heart, and Zuv's repeated reassurance turns that overthink into safety."
        )
        emotional_arc = (
            "universal reassurance hook -> Aachu's pakka after closeness -> tiny overthink proof -> "
            "Zuv's repeated haan-baba patience -> smallest-doubt thesis"
        )
        caption_recommended = (
            "the softest hearts ask twice.\n\n"
            "not because they do not trust love.\n"
            "because sometimes the tiny doubt needs to hear it again.\n\n"
            "pakka?\n"
            "haan baba.\n"
            "still pakka.\n\n"
            "maybe love is patience with your smallest doubt."
        )
        caption_alt = (
            "Maybe reassurance is not repeating yourself. Maybe it is choosing the softest part of someone again."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#EmotionalConnection",
            "#DesiLove",
            "#CoupleIllustration",
            "#AachuAndZuv",
        ]
    elif is_softness_under_fire:
        human_truth = (
            "Aachu's spicy tone is not the opposite of softness; it is often hurt, worry, and affection "
            "trying to protect itself, and Zuv's active love is hearing the feeling underneath before "
            "the moment becomes a fight."
        )
        emotional_arc = (
            "gentleness anti-ideal -> Aachu's don't-touch-me sleeve proof -> be-safe warning proof -> "
            "Zuv hears the hurt underneath -> softness-under-fire thesis"
        )
        caption_recommended = (
            "some people do not say love gently when they are hurt.\n\n"
            "they say don't touch me,\n"
            "but still hold your sleeve.\n\n"
            "they say be safe like a warning,\n"
            "because worry came out wearing attitude.\n\n"
            "and the right person does not fight the fire first.\n"
            "he hears the softness underneath.\n\n"
            "maybe love is softness under fire."
        )
        caption_alt = (
            "Send this to the person who knows your sharp words are sometimes just softness trying to stay protected."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#EmotionalConnection",
            "#DesiLove",
            "#CoupleIllustration",
            "#AachuAndZuv",
        ]
    elif is_imperfect_repair:
        human_truth = (
            "Aachu's apology does not always arrive as perfect words; sometimes it comes back as attitude, "
            "a tiny care gesture, and the choice to stand close again, while Zuv's love is understanding the "
            "repair without making her perform it."
        )
        emotional_arc = (
            "perfect-apology anti-ideal -> Aachu returns with attitude -> collar-fix proof -> "
            "Zuv chooses not to tease -> apology-accent thesis"
        )
        caption_recommended = (
            "some people don't say sorry like a movie scene.\n\n"
            "they come back with attitude.\n"
            "still angry.\n"
            "still fixing your collar.\n\n"
            "and the right person knows not to laugh too soon.\n\n"
            "maybe love is not always a perfect apology.\n"
            "maybe it is learning the apology's accent."
        )
        caption_alt = (
            "Send this to the person who understands your sorry even when it arrives with full attitude."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiLove",
            "#CoupleIllustration",
            "#AachuAndZuv",
        ]
    elif is_workday_homecoming:
        human_truth = (
            "After a day that makes him want silence, Zuv does not smile because the stress vanished; "
            "he smiles because he remembers Aachu's warm little chaos waiting at home, and that chaos is "
            "the safest place to land."
        )
        emotional_arc = (
            "bad-workday universal hook -> Aachu waiting as warm chaos -> chai/drama/long-story proof -> "
            "Zuv's parked-car smile and active choice -> chaos-as-home thesis"
        )
        caption_recommended = (
            "some days make you think you want silence.\n\n"
            "then you remember the person waiting at home.\n"
            "chai ready.\n"
            "drama ready.\n"
            "one long story definitely ready.\n\n"
            "and somehow, the day gets lighter before you even start the car.\n\n"
            "maybe chaos is also home."
        )
        caption_alt = (
            "Maybe home is not always quiet. Maybe it is the person whose warm little chaos makes the day feel survivable again."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiLove",
            "#MarriedLife",
            "#AachuAndZuv",
        ]
    elif is_mood_changed:
        human_truth = (
            "Some feelings change in the middle of an ordinary moment, and steady love is not "
            "the person who rushes the mood away; it is the hand that stays easy to reach."
        )
        emotional_arc = (
            "universal mood-change hook -> expressive emotional fullness -> hand-still-reaching proof -> "
            "steady partner slows the world down -> tender pace thesis"
        )
        caption_recommended = (
            "some moods change mid-walk.\n\n"
            "one minute soft.\n"
            "one minute quiet.\n"
            "one hand still reaching.\n\n"
            "love is not fixing the weather.\n"
            "sometimes it is slowing down enough to keep pace.\n\n"
            "love keeps pace."
        )
        caption_alt = (
            "Maybe steady love is not changing the mood. Maybe it is staying reachable until the mood changes back."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftRomanticArchive",
            "#LoveInLittleThings",
            "#DesiLove",
            "#CoupleIllustration",
        ]
    elif is_high_maintenance_care:
        human_truth = (
            "Aachu's little needs, soft impracticality, and full-alive green-dress energy are not "
            "high-maintenance when Zuv notices early and turns the tiny discomfort into gentle care."
        )
        emotional_arc = (
            "universal high-maintenance anti-label -> Aachu fully alive on the balcony -> "
            "bare-feet green-dress proof -> Zuv notices before she asks -> care-without-shrinking thesis"
        )
        caption_recommended = (
            "some people call it high-maintenance.\n\n"
            "but sometimes it is just being soft, dressed up, barefoot,\n"
            "and wanting the moment to stay beautiful for one more second.\n\n"
            "and sometimes love is the person who notices the tiny discomfort\n"
            "before you have to turn it into a request.\n\n"
            "maybe love is not asking someone to be easier.\n"
            "maybe it is care without shrinking."
        )
        caption_alt = (
            "Maybe the right love does not make your little needs feel heavy. "
            "Maybe it notices early and lets you stay fully yourself."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#SoftLoveNotes",
            "#LoveInLittleThings",
            "#DesiLove",
            "#CoupleIllustration",
            "#AachuAndZuv",
        ]
    elif is_photo_ritual:
        human_truth = (
            "Aachu turns places into memories with her 'bas ek photo aur' instinct, "
            "and Zuv's calm 'haan baba' patience is the tiny ritual that lets those memories become theirs."
        )
        emotional_arc = (
            "universal hook -> specific Aachu/Zuv revelation -> one-by-one proof -> "
            "emotional turn -> save/share thesis"
        )
        caption_recommended = (
            "har trip mein ek bas ek photo aur person hota hai.\n\n"
            "humare mein, obviously aachu.\n"
            "zuv ka kaam: haan baba, ek aur.\n\n"
            "waterfall ho ya lantern light, ritual same.\n\n"
            "pyaar shayad wahi hai:\n"
            "memories ko ours bana dena."
        )
        caption_alt = (
            "Some people take photos. Some people patiently wait while a place becomes your memory together."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#BasEkPhotoAur",
            "#LoveInLittleThings",
            "#TinyRituals",
            "#CoupleTravel",
            "#AachuAndZuv",
        ]
    elif is_kashmiri_language_story(story):
        human_truth = (
            "Some people enter a family by being polished, but Zuv enters Aachu's Kashmiri world "
            "by becoming the affectionate inside joke: not perfectly fluent, just fully committed."
        )
        emotional_arc = (
            "universal family-belonging hook -> Aachu's Kashmiri tone and family energy -> "
            "specific repeated phrase proof -> Zuv's committed parent-room moment -> tender belonging thesis"
        )
        caption_recommended = (
            "some people don't enter your family by being perfect.\n"
            "they enter by becoming the inside joke.\n\n"
            "aachu brought the kashmiri tone, the face, the full family energy.\n"
            "zuv brought questionable pronunciation and full commitment.\n\n"
            "maybe love is not fluency.\n"
            "maybe it is trying to belong."
        )
        caption_alt = (
            "Maybe love is not perfect pronunciation. Maybe it is making her people laugh while trying to belong."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#KashmiriWife",
            "#DesiLove",
            "#CoupleHumor",
            "#LoveInLittleThings",
            "#AachuAndZuv",
        ]
    elif is_subtitle_story:
        human_truth = (
            "Aachu's face, silence, and tiny 'kuch nahi' contain the whole emotional paragraph, "
            "and Zuv's love is the calm fluency of understanding her before she explains."
        )
        emotional_arc = (
            "universal mood-language hook -> Aachu's expressive subtitles -> "
            "specific kuch-nahi proof -> Zuv's quiet translation and care -> tender language thesis"
        )
        caption_recommended = (
            "some people don't explain their mood.\n"
            "they subtitle it.\n\n"
            "aachu says kuch nahi.\n"
            "her face says the full paragraph.\n\n"
            "zuv learned the translation.\n\n"
            "maybe love is learning the subtitles."
        )
        caption_alt = (
            "Maybe love is not always saying the right thing. Maybe it is learning the language nobody else hears."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#ChaoticWifeCalmHusband",
            "#CoupleHumor",
            "#DesiLove",
            "#LoveInLittleThings",
            "#AachuAndZuv",
        ]
    elif is_waterfall_lantern_story(story):
        human_truth = (
            "The memory is not only the waterfall, the lanterns, or the beautiful trip. "
            "It is the way Aachu and Zuv carry the same ease through big daylight places and tiny private night moments."
        )
        emotional_arc = "daylight memory -> scale and wonder -> lantern closeness -> then/there bridge -> home-in-a-person payoff"
        caption_recommended = (
            "some days become a whole chapter.\n\n"
            "one photo for the world going big.\n"
            "one photo for the night coming closer.\n\n"
            "same two people.\n"
            "different kind of magic."
        )
        caption_alt = (
            "Maybe the place becomes special only after someone makes it feel like yours."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#CoupleTravel",
            "#SoftLoveNotes",
            "#TravelMemories",
            "#LoveInLittleThings",
            "#AachuAndZuv",
        ]
    elif lane == "Tiny Rituals":
        human_truth = (
            "A tiny repeated ritual can carry the whole relationship: "
            "Aachu brings the spark, Zuv brings the steady care, and love becomes visible in the small things."
        )
        emotional_arc = "ritual hook -> hidden meaning -> then/now bridge -> married-life proof -> tender payoff"
        caption_recommended = (
            "right before the big promise, there was a tiny one.\n\n"
            "an anklet then.\n"
            "shoes and sandals now.\n\n"
            "same posture. same love."
        )
        caption_alt = "Some promises become visible in tiny rituals: anklets before proposals, sandals after marriage, and the same patient love in both."
        hashtags = ["#AStoryOfTwo", "#LoveInLittleThings", "#TinyRituals", "#MarriedLife", "#AachuAndZuv"]
    elif lane == "Chaotic Wife, Calm Husband" and is_morning_person_story:
        human_truth = (
            "Aachu's mornings have their own weather system, and Zuv's love shows up as chai, "
            "patience, and the wisdom to wait before asking questions."
        )
        emotional_arc = "anti-ideal hook -> sleepy proof -> mood rhythm -> care rule -> quiet love thesis"
        caption_recommended = (
            "some mornings need a warning label.\n\n"
            "5 more minutes is not a time.\n"
            "it's a boundary.\n\n"
            "so zuv learned the rule:\n"
            "chai and silence first. questions later."
        )
        caption_alt = "Some love stories begin after chai. Some husbands learn that silence is also a love language."
        hashtags = [
            "#AStoryOfTwo",
            "#ChaoticWifeCalmHusband",
            "#CoupleHumor",
            "#MorningMood",
            "#DesiLove",
            "#AachuAndZuv",
        ]
    elif lane == "Chaotic Wife, Calm Husband":
        human_truth = (
            "Aachu brings the plot, the feelings, the backup plans, and the sudden softness; "
            "Zuv's steadiness turns that chaos into something safe instead of noisy."
        )
        emotional_arc = "universal hook -> special revelation -> concrete proof beats -> emotional turn -> save/share thesis"
        caption_recommended = (
            "some people bring peace.\n"
            "aachu brings plot.\n\n"
            "\"mujhe kuch nahi hua\" means something definitely happened.\n"
            "one plan becomes twelve backup plans.\n\n"
            "and somehow, zuv makes all of it feel safe."
        )
        caption_alt = (
            "Maybe love is not less chaos. Maybe it is safer chaos."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#ChaoticWifeCalmHusband",
            "#CoupleHumor",
            "#DesiLove",
            "#MarriedLife",
            "#AachuAndZuv",
        ]
    else:
        human_truth = (
            f"The story begins with {origin}, then grows into shared comfort, "
            f"travel, and the realization that even in {place}, the real subject is still the two of them."
        )
        emotional_arc = "tiny beginning -> playful proof -> wider world -> quiet emotional payoff"
        caption_recommended = (
            f"it started with {origin}.\n\n"
            f"then somehow the story got bigger - the places, the views, the silence.\n\n"
            "but the best part stayed the same:\nit was still us."
        )
        caption_alt = (
            "Some stories begin quietly and only make sense later. "
            f"From the first tiny memory to {place}, this one kept coming back to us."
        )
        hashtags = [
            "#AStoryOfTwo",
            "#CoupleStory",
            "#CoupleTravel",
            "#LoveInLittleThings",
            f"#{place.replace(' ', '')}Diaries" if place != "the trip" else "#TravelMemories",
        ]

    story_selling_decision = build_story_selling_decision(
        lane=lane,
        story=story,
        human_truth=human_truth,
        emotional_arc=emotional_arc,
        concept_selection=concept_selection,
    )
    original_story_selling_card = story_selling_decision["selected_concept_process_card"]
    layer_e_payload = layer_e_decision.model_dump(mode="json") if layer_e_decision else None
    if layer_e_payload:
        process_cards = [
            influence
            for influence in layer_e_payload["process_influences"]
            if influence.get("influence_type") == "concept_process_card"
        ]
        selected_process_label = ", ".join(
            f"{item['id']} - {item['title']}" for item in process_cards[:3]
        ) or layer_e_payload["process_influences"][0]["title"]
        story_selling_decision = {
            "contract": {
                **STORY_SELLING_CONTRACT,
                "source": "layer-e-story-selling.json",
                "mode": "multi_room_thinking_engine",
            },
            "selected_concept_process_card": original_story_selling_card,
            "process_influence_summary": selected_process_label,
            "score": layer_e_payload["story_selling_score"],
            "threshold": "28/30",
            "decision": layer_e_payload["status"],
            "hard_fails": layer_e_payload["hard_fails"],
            "selector_verdict": layer_e_payload["selected_story_lens"],
            "authorial_flow": {
                "relationship_obstacle": layer_e_payload["human_story_setup"].get(
                    "emotional_obstacle",
                    layer_e_payload["reader_mirror"],
                ),
                "human_story_setup": layer_e_payload["human_story_setup"],
                "success_definition": layer_e_payload["success_definition"],
                "proof_engine": layer_e_payload["proof_engine"],
                "writer_rule": "Layer E is the source of truth; process cards are influences, not the answer.",
                "story_context": story,
                "emotional_machine": layer_e_payload["emotional_machine"],
                "distribution_reason": layer_e_payload["distribution_reason"],
            },
            "candidate_table": layer_e_payload["exploration_routes"],
            "rooms": layer_e_payload["rooms"],
            "process_influences": layer_e_payload["process_influences"],
        }
    story_selling_score = story_selling_decision["score"]
    story_selling_card = story_selling_decision["selected_concept_process_card"]
    story_director_gate = build_story_director_gate(
        story=story,
        lane=lane,
        slides=slides,
        human_truth=human_truth,
        emotional_arc=emotional_arc,
        concept_selection=concept_selection,
    )

    prompt_slides = [
        {
            "slide": slide["slide"],
            "slide_count": slide_count,
            "text": slide["copy"],
            "scene": slide["visual"],
            "visual": slide["visual"],
            "pose": slide.get("pose") or (
                "Use the slide scene as a lived-in romantic gesture: the couple should lean into "
                "the beat through eye contact, a small care action, hand placement, posture, or "
                f"playful distance that matches this role: {slide['role']}."
            ),
            "wardrobe": slide.get("wardrobe") or (
                "Use casual modern Indo-western wardrobe consistent with the selected identity bundle "
                "and previous slides: white shirts, denim, scarves, sneakers, small jewelry, tan pants, "
                "navy layers, or story-specific clothes only when the scene supports them."
            ),
            "props": slide.get("props") or (
                "Use only story-driven props from the slide visual or recurring @a.storyof.two motifs; "
                "props must prove the relationship beat and stay secondary to the couple."
            ),
            "background": slide.get("background") or (
                "Use a warm minimal setting implied by the slide visual, softly illustrated with faded "
                "watercolor edges and less detail than the couple."
            ),
            "emotion": slide["emotion"],
            "style": compact_style,
            "negative_prompt": contract["shared_negative_prompt"],
            "generation_mode": "model_native_publishable",
            "master_prompt_version": MASTER_PROMPT_VERSION,
            "style_reference_images": style_reference_paths,
            "identity_reference_images": identity_paths,
            "prompt": (
                f"Use case: illustration-story. Asset type: complete publishable carousel slide "
                f"{slide['slide']} of {slide_count}, prepared as two native outputs: "
                f"1080x1350 vertical 4:5 Instagram post and 1080x1920 vertical 9:16 Reels/Stories. "
                f"Never resize, crop, pad, or extend one output into the other. Story context: {story}. "
                f"Master prompt version: {MASTER_PROMPT_VERSION}. Every final image rendering prompt must include "
                "the project master prompt sections: use case, asset type, reference image roles, primary request, "
                "scene, character identity lock, face preservation, illustration style, color palette, composition, "
                "emotional direction, wardrobe continuity, props, background, line texture, anatomy, text rule, "
                "and final rendering layer. "
                f"North Star: {contract['north_star']} Content lane: {lane}. "
                f"Golden theme rule: {golden_theme_rule} "
                f"Successful Carousel Standard source: {SUCCESSFUL_CAROUSEL_STANDARD_PATH}. "
                f"Successful Carousel Standard rule: {SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT['rule']} "
                f"Successful Carousel Standard image rule: {SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT['prompt_rule']} "
                f"Post-copy visual room winner: {post_copy_visual_room['selected_visual_system']}. "
                f"Post-copy visual room decision: {post_copy_visual_room['status']} / {post_copy_visual_room['decision']}. "
                f"Visual Debate Gate winner: {visual_debate['winner']}. "
                f"{'Wallet audit safety lock: keep the cash amount tiny; show shared permission; no theft/crime mood, no angry or frightened faces, no helpless husband, no greedy wife framing, no readable card numbers, QR codes, transaction IDs, or private financial details. ' if is_wallet_audit else ''}"
                f"Visual debate verdict: {visual_debate['selector_verdict']} "
                f"Pre-generation visual screen: {visual_plan_quality['status']} / {visual_plan_quality['decision']}. "
                f"Carousel Story Director persona: {CAROUSEL_STORY_DIRECTOR_CONTRACT['rule']} "
                f"Story Director gate: {story_director_gate['status']}. "
                f"Selected first-slide hook: {story_director_gate['selected_hook']}. "
                f"Slide story-director job: {slide['role']}. "
                f"Story-Selling process card: {story_selling_card}. "
                f"Story-Selling authorial rule: {STORY_SELLING_CONTRACT['rule']} "
                f"Story-Selling score gate: {story_selling_score['total']}/30, decision {story_selling_decision['decision']}. "
                f"Style reference images: {style_reference_paths}. "
                "Canonical reference-role lock: identity references control Aachu/Zuv faces, hair, skin tone, "
                "age, body language, and emotional presence. Previous successful illustrations control only "
                "watercolor-and-ink visual language, warm paper texture, linework, spacing, wardrobe continuity, "
                "composition, and recurring props. Do not use style references as face identity references. "
                f"Identity reference images: {'; '.join(identity_paths)}. "
                f"Identity dossier path: {identity_dossier.get('path')}. "
                f"Identity preflight path: {identity_dossier.get('preflight_path')}. "
                f"Identity dossier visual references that must be loaded before generation: {identity_dossier_references}. "
                f"Selected contact sheet option IDs: {identity_selected_option_ids}. "
                f"Face identity contract: {face_identity_contract}. "
                f"Identity reference strategy: {identity_reference_selection['rule']} "
                f"Use this selected bundle only; do not infer missing outfits or attach the whole candidate library. "
                f"Character bible: {character_bible}. "
                f"{'Carousel continuity lock: ' + slide['continuity_lock'] + ' ' if slide.get('continuity_lock') else ''}"
                f"{build_identity_continuity_prompt(slide, identity_paths)} "
                f"Scene: {slide['visual']} Mood: {slide['emotion']}. "
                f"House style consistency: {HOUSE_STYLE_SCENE_RULE} "
                "Composition restraint: keep one clear focal action, two characters maximum, sparse background lines, "
                "no crowded props, no busy room, no collage, no in-your-face close-up unless the slide explicitly asks for a close proof beat, "
                "and leave generous warm-paper negative space around the couple and the handwritten text; "
                "the main image must be a lived Aachu/Zuv scene, not a paper object, receipt, museum label, poster, or stationery surface. "
                "minimalism must remove clutter, not redesign the couple's canonical illustrated identity or remove the innocent small reaction language. "
                "Keep a few tiny emotional micro-elements when useful: small hearts, blush marks, reaction ticks, tiny motion lines, "
                "soft thought bubbles, or one small care detail that makes the beat lovable. "
                "Style: use the slide's compact style field as the canonical style prompt; final art must be "
                "romantic watercolor-and-ink, not flat vector, photorealistic, anime, 3D, or glossy AI. "
                "Generate the complete publishable social slide artwork as one integrated image for each native output. "
                f"Render this exact handwritten-style text inside the artwork, spelled exactly: '{slide['copy']}'. "
                f"Render the tiny low-contrast handwritten brandmark '{brandmark}' at bottom-right inside the artwork. "
                "Follow the faces, clothing, posture, and relationship energy from the identity references. "
                "Follow the attached style references for warm paper texture, hand-drawn lettering, outfit detail, spacing, and composition. "
                "Do not create a separate quote-card panel; the text must feel naturally drawn into the illustrated scene."
            ),
        }
        for slide in slides
    ]
    identity_consistency_review = build_identity_consistency_review(
        slides=slides,
        prompt_slides=prompt_slides,
        identity_paths=identity_paths,
    )
    concept = {
        "title": title,
        "content_lane": lane,
        "north_star": contract["north_star"],
        "golden_theme_contract": golden_theme,
        "successful_carousel_standard": SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT,
        "human_truth": human_truth,
        "emotional_arc": emotional_arc,
        "slide_count": slide_count,
        "source_story_summary": story,
        "visual_style": style,
        "target_voice": "Aachu/Zuv archive voice: warm, specific, playful underneath the tenderness",
        "story_selling_contract": STORY_SELLING_CONTRACT,
        "story_selling_decision": story_selling_decision,
        "layer_e_story_selling": (
            {
                "artifact": "layer-e-story-selling.json",
                "markdown_artifact": "layer-e-story-selling.md",
                "status": layer_e_payload["status"],
                "selected_story_lens": layer_e_payload["selected_story_lens"],
                "emotional_machine": layer_e_payload["emotional_machine"],
                "human_story_setup": layer_e_payload["human_story_setup"],
                "success_definition": layer_e_payload["success_definition"],
                "process_influences": layer_e_payload["process_influences"],
            }
            if layer_e_payload
            else None
        ),
        "carousel_story_director_persona": story_director_gate,
        "identity_dossier": {
            "path": identity_dossier.get("path"),
            "preflight_path": identity_dossier.get("preflight_path"),
            "contact_sheet_path": identity_dossier.get("contact_sheet_path"),
            "status": identity_dossier.get("status"),
        },
    }
    if concept_selection:
        concept["concept_selection"] = concept_selection

    return {
        "concept": concept,
        "post_copy_visual_room": post_copy_visual_room,
        "visual_debate": visual_debate,
        "visual_plan_quality": visual_plan_quality,
        "slides": slides,
        "concept_selection": concept_selection,
        "identity_consistency_review": identity_consistency_review,
        "prompt_pack": {
            "shared_style_prompt": contract["shared_style_prompt"],
            "shared_negative_prompt": contract["shared_negative_prompt"],
            "house_style_scene_rule": HOUSE_STYLE_SCENE_RULE,
            "generation_mode": "model_native_publishable",
            "post_copy_visual_room": {
                "status": post_copy_visual_room["status"],
                "decision": post_copy_visual_room["decision"],
                "selected_visual_system": post_copy_visual_room["selected_visual_system"],
                "why_it_wins": post_copy_visual_room["why_it_wins"],
            },
            "visual_debate": {
                "status": visual_debate["status"],
                "winner": visual_debate["winner"],
                "selector_verdict": visual_debate["selector_verdict"],
                "hard_fails_checked": visual_debate["hard_fails_checked"],
            },
            "visual_plan_quality": {
                "status": visual_plan_quality["status"],
                "decision": visual_plan_quality["decision"],
                "can_generate": visual_plan_quality["can_generate"],
                "issues": visual_plan_quality["issues"],
            },
            "successful_carousel_standard": SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT,
            "model_native_master_prompt": master_prompt_contract(),
            "layer_e_story_selling": (
                {
                    "artifact": "layer-e-story-selling.json",
                    "status": layer_e_payload["status"],
                    "selected_story_lens": layer_e_payload["selected_story_lens"],
                    "emotional_machine": layer_e_payload["emotional_machine"],
                    "human_story_setup": layer_e_payload["human_story_setup"],
                    "success_definition": layer_e_payload["success_definition"],
                    "proof_engine": layer_e_payload["proof_engine"],
                    "distribution_reason": layer_e_payload["distribution_reason"],
                }
                if layer_e_payload
                else None
            ),
            "carousel_story_director_persona": story_director_gate,
            "style_reference_images": style_reference_paths,
            "identity_reference_images": identity_paths,
            "identity_dossier_reference_images": identity_dossier_references,
            "identity_dossier_path": identity_dossier.get("path"),
            "identity_generation_preflight_path": identity_dossier.get("preflight_path"),
            "identity_selected_options": identity_selected_options,
            "face_identity_contract": face_identity_contract,
            "identity_reference_strategy": identity_reference_selection,
            "identity_reference_usage": (
                "Use this small curated identity bundle for recurring Aachu/Zuv face identity, "
                "body-language continuity, and clothing/outfit references only when relevant "
                "to the story. Load the identity dossier contact sheet first, then the selected "
                "identity images as actual visual inputs. Do not dump unrelated identity candidates "
                "into the prompt."
            ),
            "character_bible": character_bible,
            "text_overlay_plan": {
                "strategy": contract["typography"]["strategy"],
                "composition_role": "publishable_final_illustration_with_text",
                "font_direction": "handwritten storybook type, dark charcoal, readable at 1080x1350 and 1080x1920, rendered by the image model inside each native illustration",
                "brandmark": contract["brandmark"],
                "brandmark_placement": contract["typography"]["brandmark_placement"],
                "slide_copy": [slide["copy"] for slide in slides],
            },
            "slides": prompt_slides,
        },
        "copy": {
            "carousel_title": title,
            "caption_recommended": caption_recommended,
            "caption_alt": caption_alt,
            "alt_text": [
                f"Illustrated carousel slide {slide['slide']}: {slide['visual']}"
                for slide in slides
            ],
            "hashtags": hashtags,
            "posting_notes": [
                "Use the first slide as the cover.",
                "Keep the caption personal and archive-like.",
                "Review generated text for exact readability before posting.",
                *(
                    ["Golden Theme selected concept: Some Couples Come With Private Captions (29.7/30)."]
                    if is_private_captions
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: Private Caption Shared Frames."]
                    if is_private_captions
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Ordinary Time With You (29.5/30)."]
                    if is_long_distance_ordinary
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: Chat Bubbles Become Shared Rooms."]
                    if is_long_distance_ordinary
                    else []
                ),
                *(
                    ["Keep lowercase paired labels near each person; do not copy sitcom frames or celebrity likenesses."]
                    if is_private_captions
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: Scoreboard Becomes A Soft Relay."]
                    if is_fifty_fifty_care
                    else []
                ),
                *(
                    ["Golden Theme selected concept: The Heavier Half (29.5/30)."]
                    if is_fifty_fifty_care
                    else []
                ),
                *(
                    ["Golden Theme score: 29.5/30"]
                    if is_fifty_fifty_care
                    else []
                ),
                *(
                    ["Carousel-first route: no Reel script or Reel signal gate; generate native 4:5 and separate native 9:16 slide sets from the same idea."]
                    if is_wallet_audit
                    else []
                ),
                *(
                    ["Safety note: money must read as tiny shared domestic mischief, not theft, disrespect, financial control, or money-flex."]
                    if is_wallet_audit
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Wallet Audit Love (30/30)."]
                    if is_wallet_audit
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: Outdoor Threshold."]
                    if is_main_kar_lungi
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Main Kar Lungi (29.5/30)."]
                    if is_main_kar_lungi
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Pakka? (30/30)."]
                    if is_pakka_reassurance
                    else []
                ),
                *(
                    ["Golden Theme score: 30/30"]
                    if is_pakka_reassurance
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: Sharp Words, Soft Hands."]
                    if is_softness_under_fire
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Softness Under Fire (29.5/30)."]
                    if is_softness_under_fire
                    else []
                ),
                *(
                    ["Golden Theme score: 29.5/30"]
                    if is_softness_under_fire
                    else []
                ),
                *(
                    ["Visual Debate Gate selected: One Gesture, Wide Silence."]
                    if is_imperfect_repair
                    else []
                ),
                *(
                    ["Golden Theme selected concept: She Was Sorry. Bas Style Alag Tha. (29.5/30)."]
                    if is_imperfect_repair
                    else []
                ),
                *(
                    ["Composition note: keep one focal gesture per slide with generous negative space; no crowded props or in-your-face framing."]
                    if is_imperfect_repair
                    else []
                ),
                *(
                    ["Golden Theme selected concept: Maybe Chaos Is Also Home (29/30)."]
                    if is_workday_homecoming
                    else []
                ),
                *(
                    ["Golden Theme selected concept: She Was Not High-Maintenance (29.5/30)."]
                    if is_high_maintenance_care
                    else []
                ),
                *(
                    ["Golden Theme score: 29.5/30"]
                    if is_high_maintenance_care
                    else []
                ),
                *(
                    ["Golden Theme score: 29.5/30"]
                    if is_kashmiri_language_story(story)
                    else []
                ),
            ],
        },
        "review": {
            "status": (
                "draft_review"
                if visual_plan_quality["can_generate"] and post_copy_visual_room["status"] == "GO"
                else "visual_repair_required"
            ),
            "scorecard": {
                "story_specificity": 4,
                "photo_to_illustration_faithfulness": 4,
                "character_likeness_prompting": 4,
                "visual_simplicity": 4,
                "slide_to_slide_flow": 4,
                "emotional_payoff": 4,
                "channel_voice_fit": 4,
                "absence_of_generic_couple_content": 4,
            },
            "total": 32,
            "max": 40,
            "pass": visual_plan_quality["can_generate"] and post_copy_visual_room["status"] == "GO",
            "story_director_gate": {
                "status": story_director_gate["status"],
                **story_director_gate["structural_audit"],
                "verdict": story_director_gate["verdict"],
                "blocks": story_director_gate["blocks"],
            },
            "visual_plan_quality_gate": {
                "status": visual_plan_quality["status"],
                "decision": visual_plan_quality["decision"],
                "can_generate": visual_plan_quality["can_generate"],
                "issues": visual_plan_quality["issues"],
            },
            "post_copy_visual_room_gate": {
                "status": post_copy_visual_room["status"],
                "decision": post_copy_visual_room["decision"],
                "selected_visual_system": post_copy_visual_room["selected_visual_system"],
                "open_doubts": post_copy_visual_room["open_doubts"],
            },
            "story_selling_score": story_selling_score,
            "story_selling_gate": {
                "status": "PASS" if story_selling_decision["decision"] == "GO" else "REPAIR",
                "source": "layer-e-story-selling.json" if layer_e_payload else "synthetic_lane_story_selling",
                "selected_concept_process_card": story_selling_card,
                "threshold": "28/30",
                "selector_verdict": story_selling_decision["selector_verdict"],
                "candidate_count": len(story_selling_decision["candidate_table"]),
            },
            "story_selling_hard_fails": story_selling_decision["hard_fails"],
            "issues": [
                "This is a local no-API package; nuanced story mining is based on deterministic rules and the provided story text.",
                "Use the Codex built-in local image-generation handoff for final illustrated art.",
                *(
                    ["post-copy-visual-room.json must return GO before image generation."]
                    if post_copy_visual_room["status"] != "GO"
                    else []
                ),
                *visual_plan_quality["issues"],
            ],
            "required_changes_before_image_generation": [
                *(
                    ["Repair post-copy visual room before image generation."]
                    if post_copy_visual_room["status"] != "GO"
                    else []
                ),
                *visual_plan_quality["issues"],
            ],
        },
    }


def create_codex_native_carousel(
    *,
    story: str,
    image_paths: list[str | Path],
    identity_image_paths: list[str | Path] | None = None,
    title: str | None = None,
    slide_count: int = DEFAULT_SLIDE_COUNT,
    style_brief: str | None = None,
    output_root: Path = Path("output") / "carousels",
    render_assets: bool = True,
    today: date | None = None,
) -> Path:
    if not story.strip():
        raise ValueError("Story is required.")
    validate_slide_count(slide_count)
    today = today or date.today()
    workspace_root = infer_workspace_root(output_root)
    layer_e_root = workspace_root if (workspace_root / "output" / "story-canon").exists() else Path(__file__).resolve().parents[2]

    paths = normalize_paths(image_paths)
    explicit_identity_bundle = identity_image_paths is not None
    identity_candidates = (
        normalize_paths(identity_image_paths)
        if explicit_identity_bundle
        else discover_identity_images(workspace_root)
    )
    identity_paths = select_identity_reference_bundle(
        identity_candidates,
        explicit=explicit_identity_bundle,
    )
    identity_reference_selection = build_identity_reference_selection(
        candidate_paths=identity_candidates,
        selected_paths=identity_paths,
        explicit=explicit_identity_bundle,
    )
    final_title = infer_title(story, title)
    slug = slugify(final_title)
    dated_root = output_root / str(today)
    out_dir = dated_root / slug
    suffix = 2
    while out_dir.exists():
        out_dir = dated_root / f"{slug}-{suffix}"
        suffix += 1
    layer_e_decision = run_layer_e(
        layer_e_root,
        {
            "task_type": "carousel_idea",
            "story_or_moment": story,
            "constraints": [
                "C-layer carousel package",
                "golden theme remains mandatory",
                "use process cards as influences, not the answer",
            ],
            "requested_tone": style_brief or "",
            "reference_images": [str(path) for path in [*paths, *identity_paths]],
        },
    )
    identity_dossier = build_identity_dossier_artifacts(
        workspace_root=workspace_root,
        out_dir=out_dir,
        selected_paths=identity_paths,
        today=today,
    )

    package = build_package(
        story=story,
        image_paths=paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=identity_reference_selection,
        identity_dossier=identity_dossier,
        title=final_title,
        slide_count=slide_count,
        style_brief=style_brief,
        layer_e_decision=layer_e_decision,
    )
    manifest = build_manifest(
        title=final_title,
        slug=out_dir.name,
        story=story,
        image_paths=paths,
        identity_image_paths=identity_paths,
        identity_reference_selection=identity_reference_selection,
        identity_dossier=identity_dossier,
        slide_count=slide_count,
        today=today,
    )
    write_package(out_dir, manifest, package)
    write_layer_e_artifacts(out_dir, layer_e_decision)

    render_result = (
        try_render_assets(out_dir, package["slides"])
        if render_assets
        else {"status": "skipped", "reason": "render_assets=False"}
    )
    write_json(out_dir / "local-preview-render.json", render_result)
    write_quality_artifacts(
        QualityContext(
            story=story,
            title=final_title,
            slug=out_dir.name,
            today=today,
            out_dir=out_dir,
            image_paths=paths,
            slide_count=slide_count,
            package=package,
            manifest=manifest,
            render_result=render_result,
            workspace_root=workspace_root,
        )
    )
    return out_dir
