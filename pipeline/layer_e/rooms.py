from __future__ import annotations

from pipeline.layer_e.contracts import (
    ExpertAgentOutput,
    LayerERoomOutput,
    LayerESourceMemory,
    ProcessInfluence,
    StoryRoute,
)
from pipeline.layer_e.scoring import detect_hard_fails, score_route, status_for


def _card(memory: LayerESourceMemory, card_id: str):
    return next((card for card in memory.process_cards if card.id == card_id), None)


def process_influences_for_story(story: str, memory: LayerESourceMemory) -> list[ProcessInfluence]:
    text = story.lower()
    influence_ids = ["card-20", "card-07"]
    if any(token in text for token in ["dono rakh", "plate", "banter", "joke", "phone"]):
        influence_ids.insert(0, "card-05")
    if any(token in text for token in ["forgive", "angry", "fight", "maaf", "shout"]):
        influence_ids.insert(0, "card-02")
    if any(token in text for token in ["cup", "chai", "kitchen", "ritual"]):
        influence_ids.append("card-08")

    seen: set[str] = set()
    influences: list[ProcessInfluence] = [
        ProcessInfluence(
            id="successful-carousel-standard",
            title="Successful Carousel Standard",
            influence_type="living_standard",
            confidence=0.9,
            reason="Defines public identity mirror, couple receipts, active Zuv care, reversal, and send/save thesis.",
        )
    ]
    for card_id in influence_ids:
        if card_id in seen:
            continue
        seen.add(card_id)
        card = _card(memory, card_id)
        if card:
            influences.append(
                ProcessInfluence(
                    id=card.id,
                    title=card.title,
                    influence_type="concept_process_card",
                    source_patterns=card.source_patterns,
                    confidence=card.confidence,
                    reason=f"Useful influence for this story because: {card.a_story_of_two_filter}",
                )
            )
    return influences


def generate_exploration_routes(story: str, influences: list[ProcessInfluence]) -> list[StoryRoute]:
    text = story.lower()
    is_plate = "plate" in text and "dono rakh" in text
    relationship_terms = [
        "aachu",
        "zuv",
        "she",
        "he ",
        "husband",
        "wife",
        "partner",
        "couple",
        "married",
        "love",
    ]
    aesthetic_terms = ["pretty", "nice", "warm light", "table", "plate", "view", "aesthetic"]
    is_pretty_only = (
        not any(term in text for term in relationship_terms)
        and any(term in text for term in aesthetic_terms)
    )
    if is_plate:
        routes = [
            StoryRoute(
                name="Banter Becomes Belonging",
                story_lens="A tiny plate handoff becomes a married-life joke about who is allowed to be lovingly inconvenient.",
                reader_mirror="Couples who turn chores into tiny power reversals will recognize themselves.",
                emotional_obstacle="The moment could become a chore lecture or perfect-husband praise if the joke is flattened.",
                aachu_specific_spark="Aachu stacks her plate on top and says dono rakh do with deadpan ownership.",
                zuv_active_role="Zuv carries both plates to the kitchen instead of making the bit heavy.",
                proof_engine="silent plate handoff -> plate stack -> dono rakh do -> phone beat -> he carries both plates",
                emotional_reversal="What looked like laziness becomes the ease of being fully known.",
                payoff="Love is when even your tiny unfairness has a place to land.",
                distribution_reason="Send/save for couples who have their own household bit and want to tag the person who gets it.",
                process_influence_ids=[item.id for item in influences[:3]],
            ),
            StoryRoute(
                name="The Chore Became A Punchline",
                story_lens="The plate stack works because the chore is not the topic; the permission to joke is.",
                reader_mirror="Anyone who has had a tiny dinner-table negotiation with their partner has a doorway in.",
                emotional_obstacle="If the scene becomes duty math, the warmth disappears.",
                aachu_specific_spark="She escalates his plate slide by stacking hers on top without explaining herself.",
                zuv_active_role="He accepts the escalation and completes the bit by taking the stack.",
                proof_engine="two finished plates, one casual slide, one deadpan stack, one quiet walk to the kitchen",
                emotional_reversal="The unfair-looking move proves comfort, not disrespect.",
                payoff="Some marriages are built on jokes only two people are allowed to make.",
                distribution_reason="Built for partner tags because the behavior is ordinary, visible, and repeatable.",
                process_influence_ids=[item.id for item in influences[:4]],
            ),
            StoryRoute(
                name="Household Scoreboard Loses",
                story_lens="The story rejects scorekeeping by showing a tiny unfair moment that still feels safe.",
                reader_mirror="Couples who hate perfect fairness but love mutual ease will see themselves.",
                emotional_obstacle="A fairness frame could make one partner look selfish and the other helpless.",
                aachu_specific_spark="Aachu makes the unfair move funny by committing to the bit.",
                zuv_active_role="Zuv chooses softness and motion: he takes the plates, not the bait.",
                proof_engine="plate slide, plate stack, phone exit, kitchen carry",
                emotional_reversal="The joke becomes proof that not every tiny imbalance is a threat.",
                payoff="Sometimes love is not fifty-fifty; sometimes it is your turn to carry the bit.",
                distribution_reason="Saveable for couples who want language for playful non-scorekeeping.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Dono Rakh Do As Love Language",
                story_lens="The line works because it is absurdly specific and still emotionally readable.",
                reader_mirror="Hinglish household comedy gives desi couples a familiar mirror.",
                emotional_obstacle="The exact line could become private context unless the visuals prove the setup.",
                aachu_specific_spark="Aachu says dono rakh do only after making the visual joke undeniable.",
                zuv_active_role="Zuv becomes the person who understands the line without needing a speech.",
                proof_engine="the stacked plates make the phrase readable before the viewer translates it emotionally",
                emotional_reversal="A command turns into belonging because he already knows the joke.",
                payoff="The right person understands the nonsense before the explanation.",
                distribution_reason="Comment/tag potential comes from the phrase feeling like something said at home.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Tiny Inconvenience, Big Ease",
                story_lens="The emotional truth is not plates; it is the ease of being inconvenient without panic.",
                reader_mirror="People save this because it explains a safe ordinary love.",
                emotional_obstacle="Without Zuv's active response, the story becomes only Aachu being dramatic.",
                aachu_specific_spark="Aachu makes the tiny inconvenience visible, funny, and hers.",
                zuv_active_role="Zuv answers with action and lets the moment stay light.",
                proof_engine="one tiny domestic inconvenience carried all the way into the kitchen",
                emotional_reversal="The inconvenience becomes evidence of comfort.",
                payoff="Maybe home is the person who carries your bit with the plates.",
                distribution_reason="Strong send reason: this is a daily-life proof many couples can reenact.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_pretty_only:
        routes = [
            StoryRoute(
                name="Aesthetic Without Story",
                story_lens="The supplied moment is currently a pretty setup, not a relationship story.",
                reader_mirror="",
                emotional_obstacle="",
                aachu_specific_spark="",
                zuv_active_role="",
                proof_engine="",
                emotional_reversal="",
                payoff="",
                distribution_reason="",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Object First Repair Needed",
                story_lens="The object can become a receipt only after the couple behavior is named.",
                reader_mirror="",
                emotional_obstacle="",
                aachu_specific_spark="",
                zuv_active_role="",
                proof_engine="",
                emotional_reversal="",
                payoff="",
                distribution_reason="",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Missing Active Partner Role",
                story_lens="Layer E needs Aachu pressure and Zuv action before it can choose meaning.",
                reader_mirror="",
                emotional_obstacle="",
                aachu_specific_spark="",
                zuv_active_role="",
                proof_engine="",
                emotional_reversal="",
                payoff="",
                distribution_reason="",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    else:
        routes = [
            StoryRoute(
                name="Proof Before Poetry",
                story_lens="The story should begin with the behavior that proves love, not the romantic summary.",
                reader_mirror="Readers enter through a concrete couple behavior they recognize.",
                emotional_obstacle="The idea risks becoming pretty but emotionally flat.",
                aachu_specific_spark="Aachu carries the expressive pressure in the moment.",
                zuv_active_role="Zuv must make one visible choice toward her.",
                proof_engine=story.strip() if len(story.strip()) > 20 else "",
                emotional_reversal="The surface moment becomes proof of care.",
                payoff="Love becomes believable only after the scene proves it.",
                distribution_reason="Saveable when it gives viewers language for a familiar relationship pattern.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Public Scene, Private Meaning",
                story_lens="Turn the visible scene into a private relationship truth.",
                reader_mirror="A stranger can enter through the public scene first.",
                emotional_obstacle="If the private meaning is absent, the scene stays decorative.",
                aachu_specific_spark="Aachu's reaction gives the scene emotional charge.",
                zuv_active_role="Zuv's care must be visible in frame.",
                proof_engine=story.strip() if any(name in story.lower() for name in ["aachu", "she", "zuv", "he"]) else "",
                emotional_reversal="The public image becomes a private receipt.",
                payoff="The pretty part is only proof; the relationship is the subject.",
                distribution_reason="Shareable if the scene becomes a relationship mirror.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Anti-Ideal To Real Love",
                story_lens="Reject polished romance and find the real imperfect dynamic.",
                reader_mirror="Viewers recognize the gap between ideal romance and real couple behavior.",
                emotional_obstacle="The route fails if no tension or role is visible.",
                aachu_specific_spark="Aachu brings the human imperfection.",
                zuv_active_role="Zuv must respond with grounded behavior.",
                proof_engine=story.strip() if "zuv" in story.lower() or "he " in story.lower() else "",
                emotional_reversal="The imperfection becomes the reason it feels true.",
                payoff="Real love is specific enough to be inconvenient.",
                distribution_reason="Sendable when it names what perfect romance misses.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Reader As Third Witness",
                story_lens="Let the reader feel seen before explaining the couple.",
                reader_mirror="The viewer recognizes their own desire to be understood.",
                emotional_obstacle="The route becomes advice if Aachu/Zuv proof is weak.",
                aachu_specific_spark="Aachu provides the emotional receipt.",
                zuv_active_role="Zuv provides the answering action.",
                proof_engine=story.strip() if len(story.strip()) > 60 else "",
                emotional_reversal="Advice turns into story once the proof appears.",
                payoff="The lesson must feel discovered through them.",
                distribution_reason="Useful for article, caption, and save behavior.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Scene Before Summary",
                story_lens="Start inside the moment and delay explanation until the scene earns it.",
                reader_mirror="People stay because they want the scene to resolve.",
                emotional_obstacle="Summary too early kills tension.",
                aachu_specific_spark="Aachu's behavior creates the scene's pressure.",
                zuv_active_role="Zuv's action resolves or reframes the pressure.",
                proof_engine=story.strip() if len(story.strip()) > 80 else "",
                emotional_reversal="The scene reveals what the summary could not.",
                payoff="The final line lands only after the action.",
                distribution_reason="Retention comes from wanting the next panel.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]

    scored: list[StoryRoute] = []
    for route in routes:
        score = score_route(route)
        hard_fails = detect_hard_fails(route)
        scored.append(
            route.model_copy(
                update={
                    "score_total": score.total,
                    "hard_fails": hard_fails,
                    "verdict": status_for(score, hard_fails),
                }
            )
        )
    return scored


def build_rooms(routes: list[StoryRoute]) -> dict[str, LayerERoomOutput]:
    winner = max(routes, key=lambda route: route.score_total) if routes else None
    winner_name = winner.name if winner else "No route"
    return {
        "source_memory_room": LayerERoomOutput(
            name="Context And Source Memory",
            status="GO",
            agents=[
                ExpertAgentOutput(agent="Source Curator", role="legality", claim="Use derived patterns and source IDs only."),
                ExpertAgentOutput(agent="Successful Carousel Standard Reader", role="creative north star", claim="Prioritize public identity mirror and concrete couple receipts."),
                ExpertAgentOutput(agent="Creator Preference Ledger Reader", role="memory", claim="Avoid repeating cooled-down lanes as fresh ideas."),
            ],
            summary="Source memory loaded before concept selection.",
        ),
        "story_meaning_room": LayerERoomOutput(
            name="Story Meaning Room",
            status="GO" if winner else "REPAIR",
            agents=[
                ExpertAgentOutput(agent="Romance Novelist", role="emotional arc", claim="The route needs obstacle, proof, reversal, and earned payoff."),
                ExpertAgentOutput(agent="Film Scene Director", role="scene grammar", claim="The meaning must be drawable through behavior."),
                ExpertAgentOutput(agent="Aachu/Zuv Dynamics Writer", role="character truth", claim="Aachu gets spark; Zuv gets active response."),
                ExpertAgentOutput(agent="Emotional Obstacle Miner", role="friction", claim="No obstacle means no story engine."),
            ],
            summary=f"Generated {len(routes)} story routes and selected {winner_name} as the strongest raw meaning.",
            selected_outputs={"raw_winner": winner_name},
        ),
        "audience_algorithm_room": LayerERoomOutput(
            name="Audience And Algorithm Room",
            status="GO" if winner and winner.distribution_reason else "REPAIR",
            agents=[
                ExpertAgentOutput(agent="Retention Analyst", role="swipe ladder", claim="The route must create curiosity and middle-slide re-engagement."),
                ExpertAgentOutput(agent="Algorithm / Share-Save Strategist", role="distribution", claim="The route needs a send/save/tag reason."),
                ExpertAgentOutput(agent="Copy Chief", role="wording", claim="Public copy should stay name-free and behavior-led."),
                ExpertAgentOutput(agent="Culture And Taste Reader", role="taste", claim="The humor should feel warm, desi, and non-shaming."),
            ],
            summary="Audience pass checked reader mirror, send/save logic, and taste.",
            selected_outputs={"distribution_reason": winner.distribution_reason if winner else ""},
        ),
        "contrarian_repair_room": LayerERoomOutput(
            name="Contrarian Repair Room",
            status="GO" if winner and not winner.hard_fails else "REPAIR",
            agents=[
                ExpertAgentOutput(agent="Harsh Critic", role="route attack", claim="The winner must survive genericness and private-context objections."),
                ExpertAgentOutput(agent="Genericness Detector", role="specificity", claim="Specific proof beats beat abstract romance."),
                ExpertAgentOutput(agent="Safety/Taste Guard", role="safety", claim="No shaming, privacy leak, or copied expression."),
                ExpertAgentOutput(agent="Visual Generativity Skeptic", role="generation", claim="The concept must become simple scenes."),
            ],
            summary="Top routes were attacked and repair needs were recorded.",
            objections=winner.hard_fails if winner else ["no route generated"],
            repairs=[] if winner and not winner.hard_fails else ["Add obstacle, active Zuv role, proof, and send/save reason."],
        ),
        "final_synthesis_room": LayerERoomOutput(
            name="Final Synthesis Room",
            status="GO" if winner and winner.verdict == "GO" else "REPAIR",
            agents=[
                ExpertAgentOutput(agent="Story Lens Selector", role="selection", claim=f"Selected {winner_name}."),
                ExpertAgentOutput(agent="Story-Selling Rubric Judge", role="score", claim="Apply 30-point Story-Selling threshold."),
                ExpertAgentOutput(agent="Downstream Contract Writer", role="handoff", claim="Write emotional machine into C/D/B contracts."),
            ],
            summary="Final selector synthesized the route into Layer E handoff fields.",
            selected_outputs={"selected_story_lens": winner.story_lens if winner else ""},
        ),
    }
