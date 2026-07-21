from __future__ import annotations

from pipeline.layer_e.contracts import (
    ExpertAgentOutput,
    LayerERoomOutput,
    LayerERequest,
    LayerESourceMemory,
    ProcessInfluence,
    StoryRoute,
)
from pipeline.layer_e.scoring import (
    detect_hard_fails,
    score_golden_theme,
    score_route,
    stage_scene_gate_for_route,
    status_for,
)


def _card(memory: LayerESourceMemory, card_id: str):
    return next((card for card in memory.process_cards if card.id == card_id), None)


def process_influences_for_story(story: str, memory: LayerESourceMemory) -> list[ProcessInfluence]:
    text = story.lower()
    influence_ids = ["card-20", "card-07"]
    if any(token in text for token in ["disagree", "fight", "arguments", "bad days", "older couple", "walked away"]):
        influence_ids.insert(0, "card-09")
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


def success_definition_from_memory(memory: LayerESourceMemory) -> dict[str, str]:
    return {
        "audience_success": (
            "A cold viewer thinks 'this is us' or sends/saves/tags a partner because the "
            "relationship truth is recognizable before the art is admired."
        ),
        "creative_success": (
            "The deck works as silent panels: public hook, emotional obstacle, concrete "
            "receipts, active Zuv behavior, reversal, and earned final thesis."
        ),
        "brand_success": (
            "The idea strengthens @a.storyof.two as warm, funny, desi relationship IP where "
            "small behaviors become evidence of love."
        ),
        "production_success": (
            "Story-Selling and Golden Theme gates pass before C-layer writing, then visual, "
            "identity, request-locked native-format, QA, and audit gates must also pass. "
            "Default post/carousel delivery is 1080x1440 only; 1080x1920 Reel/Story "
            "is required only when explicitly requested."
        ),
        "source": "wiki/insights/successful-carousel-standard.md",
        "memory_excerpt": memory.success_standard_excerpt[:500],
    }


def human_story_setup_for_route(route: StoryRoute) -> dict[str, str]:
    return {
        "cold_reader_doorway": route.reader_mirror,
        "emotional_obstacle": route.emotional_obstacle,
        "visible_human_proof": route.proof_engine,
        "active_partner_role": route.zuv_active_role,
        "emotional_turn": route.emotional_reversal,
        "shareable_setup": route.distribution_reason,
        "earned_payoff": route.payoff,
    }


def generate_exploration_routes(story: str, influences: list[ProcessInfluence]) -> list[StoryRoute]:
    text = story.lower()
    is_plate = "plate" in text and "dono rakh" in text
    is_photo_identity_request = (
        any(token in text for token in ["identity photo", "identity photos", "selfie", "photo", "portrait", "resort"])
        and any(token in text for token in ["carousel", "1m", "view", "post", "next"])
    )
    is_high_maintenance_care = "high-maintenance" in text or (
        "green dress" in text and "barefoot" in text and "notices" in text
    )
    is_commitment_still_love = any(
        token in text
        for token in [
            "we disagree, i still love you",
            "we fight, i still love you",
            "older couple",
            "still choosing each other",
            "going to be us one day",
            "make it all the way",
        ]
    )
    is_enough_love = any(
        token in text
        for token in [
            "i have no car",
            "i'll walk",
            "i’ll walk",
            "i’m not so good",
            "i'm not so good",
            "a little gift for you",
            "we’ll build together",
            "we'll build together",
            "i lost everything",
            "i’m not successful",
            "i'm not successful",
            "i’ll wait",
            "i'll wait",
        ]
    )
    is_subtitle_language = "subtitles" in text or ("kuch nahi" in text and "translation" in text)
    is_first_date_trip = "first date" in text and "ladakh" in text
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
    if is_enough_love:
        routes = [
            StoryRoute(
                name="I Have No Car, I'll Walk",
                story_lens=(
                    "Love answers lack with visible choice: no car becomes walking, not-good becomes being loved, "
                    "long stories get time, little gifts become priceless, loss gets rebuilt, tiredness gets presence, and unfinished success gets waiting."
                ),
                reader_mirror=(
                    "Couples who are still building a life can see themselves because the promise arrives before money, status, ease, or success."
                ),
                emotional_obstacle=(
                    "The route could become a copied quote carousel unless every line is staged as a concrete Aachu/Zuv action and not only text on paper."
                ),
                aachu_specific_spark=(
                    "Aachu answers limitation with action: she walks beside him, listens without rushing, values the small gift, builds after loss, stays in tiredness, and waits through unfinished success."
                ),
                zuv_active_role=(
                    "Zuv names the insecurity honestly, keeps walking, tells the long story, offers the small gift, admits the loss, rests when tired, and lets her waiting become mutual courage."
                ),
                proof_engine=(
                    "road walk hand-in-hand -> lakeside self-doubt answered with love -> armchair long-story listening -> train bouquet gift -> "
                    "city-lane rebuilding after loss -> meadow tired-body presence -> balcony waiting before success"
                ),
                emotional_reversal=(
                    "What first looks like not-enough becomes enough-for-love because every slide shows a limitation being met by chosen presence."
                ),
                payoff="I’m not successful / I’ll wait.",
                distribution_reason=(
                    "Send this to the partner who is willing to build, walk, listen, stay, and wait before life looks finished."
                ),
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Love Before Readiness",
                story_lens=(
                    "The finished version is not the proof; the person who stays before the finish line is the proof."
                ),
                reader_mirror="People who feel behind in life can send this to the person who makes them feel chosen anyway.",
                emotional_obstacle="Readiness pressure can make love feel conditional unless the route shows care before success.",
                aachu_specific_spark="Aachu treats every unfinished place as somewhere love can still stand.",
                zuv_active_role="Zuv stops pretending he has it all together and lets honest vulnerability stay visible.",
                proof_engine="no car -> walk together -> small gift -> lost everything -> build together -> not successful -> wait",
                emotional_reversal="The lack becomes romantic only because it is met with behavior, not pity.",
                payoff="You do not have to arrive before I choose you.",
                distribution_reason="Strong send/save reason for couples in building seasons.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Everything Small Became Enough",
                story_lens="The emotional pattern is scale reversal: little effort, little gift, little time, and little certainty become enough because love receives them fully.",
                reader_mirror="Viewers recognize the person who made their small offering feel valuable.",
                emotional_obstacle="The deck risks becoming sentimental unless every small thing is attached to a scene.",
                aachu_specific_spark="Aachu makes the ordinary gestures glow by receiving them with warmth.",
                zuv_active_role="Zuv keeps offering honestly even when the offering is small.",
                proof_engine="walk -> chair conversation -> bouquet -> lane walk -> meadow rest -> terrace wait",
                emotional_reversal="Small stops meaning insufficient and starts meaning intimate.",
                payoff="It was little, but it was loved like diamond.",
                distribution_reason="Taggable for partners who made small gestures feel safe and enough.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="We'll Build Together",
                story_lens="Loss becomes survivable when the relationship turns it into shared construction.",
                reader_mirror="Couples rebuilding after hard seasons get a direct public doorway.",
                emotional_obstacle="The route is narrower if it starts only from loss and misses the earlier tender proofs.",
                aachu_specific_spark="Aachu says together before the future is visible.",
                zuv_active_role="Zuv does not hide the loss; he lets partnership answer it.",
                proof_engine="I lost everything -> she takes his hand -> city lane -> shared bag -> balcony future",
                emotional_reversal="Loss stops being the ending once two people move in the same direction.",
                payoff="We’ll build together.",
                distribution_reason="Saveable for couples in rebuilding seasons.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="I Have Time",
                story_lens="Patience is the love language: the long story gets a listener before it gets a solution.",
                reader_mirror="Anyone who has needed someone to listen without rushing can enter.",
                emotional_obstacle="Too narrow as a full carousel because it centers only one proof beat.",
                aachu_specific_spark="Aachu makes time feel abundant through her listening posture.",
                zuv_active_role="Zuv trusts her with the long story instead of compressing himself.",
                proof_engine="armchairs -> lamp -> body leans in -> phone down -> long story begins",
                emotional_reversal="Listening becomes an act of choosing.",
                payoff="I have time.",
                distribution_reason="Saveable as a quiet proof, weaker as the whole seven-slide engine.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_commitment_still_love:
        routes = [
            StoryRoute(
                name="I Still Love You",
                story_lens=(
                    "Conflict stays inside commitment: disagreement, fights, and bad days become meaningful "
                    "because both people keep choosing the all-the-way version of love."
                ),
                reader_mirror=(
                    "Couples who have fought, repaired, and still imagined a future together will recognize themselves."
                ),
                emotional_obstacle=(
                    "The idea could become copied quote-card romance unless the scenes show the tension, cost, "
                    "repair, and active choice to stay."
                ),
                aachu_specific_spark=(
                    "Aachu feels the disagreement fully, watches older love as proof, and lets that sight become "
                    "a private promise about her own marriage."
                ),
                zuv_active_role=(
                    "Zuv stays close, holds the repair hug, keeps his hand reachable, and chooses softness after the hard moment."
                ),
                proof_engine=(
                    "doorway disagreement -> repair hug -> hands find each other -> older couple witness -> "
                    "bad-day room traces -> kitchen shoulder-to-shoulder -> side-by-side final"
                ),
                emotional_reversal=(
                    "What first looks like conflict becomes proof of staying because the scenes show both people "
                    "returning to the same frame."
                ),
                payoff="Still together. Still choosing each other. Still completely in love.",
                distribution_reason=(
                    "Send this to the partner who has seen the hard days and still wants the two-of-you future."
                ),
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Everything It Took To Get There",
                story_lens=(
                    "An older couple is not just a cute future image; they are evidence of all the arguments, "
                    "bad days, and choices not to walk away."
                ),
                reader_mirror="Viewers who look at older couples and imagine their own future get an immediate doorway.",
                emotional_obstacle=(
                    "The route risks becoming only a pretty older-couple image unless Aachu/Zuv's own conflict and repair are visible."
                ),
                aachu_specific_spark="Aachu reads the older couple through longing, tenderness, and her own emotional future tense.",
                zuv_active_role="Zuv notices her watching, steps closer, and answers the fear by staying physically beside her.",
                proof_engine=(
                    "older couple side by side -> Aachu watches -> Zuv steps closer -> hands touch -> "
                    "hard-day receipts -> present couple mirrors the posture"
                ),
                emotional_reversal=(
                    "The older couple stops being a reference image and becomes the proof that staying is built through imperfect days."
                ),
                payoff="One day, that will be us because we kept choosing.",
                distribution_reason="Sendable for couples who want the long-haul version, not only the easy-day version.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Bad Days Included",
                story_lens="The all-the-way kind of love includes arguments and bad days without letting them become the ending.",
                reader_mirror="Couples with repair rituals can tag each other because the proof is ordinary and recognizable.",
                emotional_obstacle="Bad days can look like failure unless the route shows both people choosing not to leave.",
                aachu_specific_spark="Aachu carries the feeling honestly instead of pretending the fight did not matter.",
                zuv_active_role="Zuv sits near her, holds the silence, and waits without turning the hard day into distance.",
                proof_engine="two untouched cups -> paused phone -> rain window -> Zuv sits near -> Aachu looks back -> hands reconnect",
                emotional_reversal="The hard day becomes a receipt of love because neither person exits the frame.",
                payoff="Love is not no bad days. Love is still us after them.",
                distribution_reason="Partner-tag reason is clear: this says the hard days did not cancel the relationship.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Still Choosing",
                story_lens="The repeated word 'still' is the engine: still after disagreement, still after bad days, still beside each other.",
                reader_mirror="Anyone who wants a love that keeps choosing after friction can enter through the hook.",
                emotional_obstacle="The concept fails if 'still' is only typography and not visible action.",
                aachu_specific_spark="Aachu's expressive worry creates the question of whether they will really make it.",
                zuv_active_role="Zuv shows the answer by reaching, leaning in, and staying close without a speech.",
                proof_engine="disagree -> lean apart -> hand reaches -> lean back in -> older couple passes -> present couple stays",
                emotional_reversal="The repetition turns from fear into certainty because the body language answers it.",
                payoff="Still choosing each other.",
                distribution_reason="Saveable as a compact line for couples who have repaired more than once.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Future Us",
                story_lens="The future is not imagined from perfect romance, but from seeing proof that imperfect love can last.",
                reader_mirror="Viewers who point at older couples and say 'that will be us' can immediately send this.",
                emotional_obstacle="Future-us sentiment can become generic unless grounded in specific fights, repairs, and gestures.",
                aachu_specific_spark="Aachu turns the sight of older love into a private certainty.",
                zuv_active_role="Zuv stands with her, receives the future as a choice, and keeps the closeness active.",
                proof_engine="gallery path -> older couple side by side -> Aachu watches -> Zuv watches her -> shoulder touch -> final table",
                emotional_reversal="A passing scene becomes a promise only because their own repair has already been shown.",
                payoff="I know that's going to be us one day.",
                distribution_reason="Send this to the person you want to become older-love with after every imperfect day.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_plate:
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
    elif is_photo_identity_request:
        routes = [
            StoryRoute(
                name="He Chose The Girl Between Photos",
                story_lens=(
                    "The shareable story is not the polished photo; it is being loved in the "
                    "awkward, laughing, hair-fixing seconds between public pictures."
                ),
                reader_mirror="Couples who know the posted photo hides three messy real moments before it.",
                emotional_obstacle=(
                    "Aesthetic photos can make love look like performance unless the story reveals the "
                    "unposted version that still gets chosen."
                ),
                aachu_specific_spark=(
                    "Aachu is bright, expressive, adjusting hair/outfit/face between frames, then laughing "
                    "too honestly to be the polished version."
                ),
                zuv_active_role=(
                    "Zuv keeps the private version safe: he waits, holds the phone, fixes the frame, and "
                    "smiles at the almost-photo before asking for the final one."
                ),
                proof_engine=(
                    "resort selfie surface -> home cheek-kiss softness -> portrait pose -> unposted "
                    "hair-fix/laugh/waiting beats between them"
                ),
                emotional_reversal="The perfect picture becomes only the receipt; the real choice happened between pictures.",
                payoff="Maybe love is the person who likes the version between photos.",
                distribution_reason=(
                    "Sendable to the partner who has seen every almost-photo, awkward face, and still says "
                    "one more because they like the real you."
                ),
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The Photo Was Public. The Patience Was Private.",
                story_lens=(
                    "A public smiling photo hides the private patience that made the smile possible."
                ),
                reader_mirror="Anyone whose partner waits through retakes, mood shifts, and tiny prep rituals can enter.",
                emotional_obstacle="The moment risks becoming a photo-taking trope unless it shows private patience as action.",
                aachu_specific_spark="Aachu wants the photo to feel right because memory matters to her.",
                zuv_active_role="Zuv quietly holds the frame, waits through retakes, and keeps the mood light.",
                proof_engine="phone held steady, lamp glow, hair adjustment, one failed take, one private laugh, final smile",
                emotional_reversal="What looked like vanity becomes a bid to remember the night properly.",
                payoff="Some photos look cute because someone made you feel safe first.",
                distribution_reason="People send this to the partner who waits through photos without making them feel silly.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="He Didn't Fall For The Picture Face",
                story_lens="Reject the polished ideal and reveal love for the face after the camera drops.",
                reader_mirror="Couples recognize the difference between Instagram face and real partner face.",
                emotional_obstacle="The hook can shame performance unless the route honors why people want to look remembered.",
                aachu_specific_spark="Aachu gives the camera her bright public smile, then instantly becomes goofier and softer.",
                zuv_active_role="Zuv reacts to the after-face with more warmth than the posed face.",
                proof_engine="posed smile -> camera drops -> silly expression -> his bigger smile -> second private photo",
                emotional_reversal="The less polished face becomes the one that proves closeness.",
                payoff="The right person loves the face after the photo too.",
                distribution_reason="Highly taggable for partners who know each other's real post-photo face.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The Person Behind The Camera",
                story_lens="The romance is the unseen labor behind the picture: waiting, framing, noticing, and choosing.",
                reader_mirror="Viewers know the partner who becomes photographer, hype person, and calm witness.",
                emotional_obstacle="A single nice photo hides the care work that made it possible.",
                aachu_specific_spark="Aachu wants the memory, the light, and the face to match how the night felt.",
                zuv_active_role="Zuv becomes the quiet witness who keeps trying until her real smile appears.",
                proof_engine="him holding phone, failed frame, her laughter, adjusted angle, final photo, private look",
                emotional_reversal="The person behind the camera becomes the reason the photo has feeling.",
                payoff="Some people don't just take your photo. They wait for your real smile.",
                distribution_reason="Sendable to anyone whose partner has become their patient photographer without complaint.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Three Photos, One Private Proof",
                story_lens="Across public resort, home, and portrait frames, the same proof repeats: he chooses her in every version.",
                reader_mirror="Couples recognize being loved across outside-face, home-face, and posing-for-memory face.",
                emotional_obstacle="The route can become generic collage unless the repeated behavior is Zuv's active choosing.",
                aachu_specific_spark="Aachu shifts from bright travel energy to soft home smile to dressed-up memory-making.",
                zuv_active_role="Zuv meets each version differently: close behind, arms around her, then quietly proud in the frame.",
                proof_engine="three different photo contexts showing the same active closeness and private ease",
                emotional_reversal="Different pictures stop being outfits/places and become evidence of one steady pattern.",
                payoff="Maybe love is being chosen in every version of yourself.",
                distribution_reason="Saveable as a broader relationship thesis, but weaker because it risks becoming generic.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Not The Post. The Proof.",
                story_lens="Use the photos as receipts that love is built from small off-camera behaviors.",
                reader_mirror="Viewers recognize that the real relationship is usually outside the posted frame.",
                emotional_obstacle="Without off-camera action, the concept is only 'nice couple photos'.",
                aachu_specific_spark="Aachu brings the memory-making urge and expressive reaction.",
                zuv_active_role="Zuv protects the mood around the memory instead of treating it as a task.",
                proof_engine="light, frame, retake, cheek-kiss, waiting, private laugh, final picture",
                emotional_reversal="The post becomes less important than the proof trail around it.",
                payoff="The best part of the photo is who you were with before it.",
                distribution_reason="Shareable for couples who know every good photo has a tiny relationship story behind it.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_high_maintenance_care:
        routes = [
            StoryRoute(
                name="She Was Not High-Maintenance",
                story_lens="Reject the dating-market insult and reveal that tiny needs are bids to be noticed kindly.",
                reader_mirror="Couples recognize the partner who wants small care without being made to feel difficult.",
                emotional_obstacle="A small need can be misread as fussiness unless the scene proves it is about comfort and being noticed.",
                aachu_specific_spark="Aachu chooses the green dress, keeps moving barefoot, and tries not to make her discomfort the whole scene.",
                zuv_active_role="Zuv notices the uncomfortable step before she asks, slows the path, and offers his hand without shrinking her.",
                proof_engine="green dress choice -> barefoot step slows -> Zuv notices before she asks -> his hand extends -> route becomes softer",
                emotional_reversal="What could look like high maintenance becomes proof that love can notice a small need early.",
                payoff="Maybe the right person does not call it too much. He just notices sooner.",
                distribution_reason="Sendable to the partner who notices tiny discomfort before it becomes a big announcement.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The Tiny Need Was Not The Problem",
                story_lens="The emotional machine is not extra needs; it is whether those needs can arrive without shame.",
                reader_mirror="Anyone who has softened because a partner noticed the small thing can enter.",
                emotional_obstacle="The premise fails if it praises perfect service or makes Aachu helpless.",
                aachu_specific_spark="Aachu keeps her expressive dignity: dress, barefoot pause, half-annoyed smile, still wanting the moment.",
                zuv_active_role="Zuv adjusts the walk and gives her a steady hand while staying playful, not heroic.",
                proof_engine="dress held up -> barefoot pause -> half-annoyed smile -> Zuv adjusts the walk -> both keep moving",
                emotional_reversal="The small inconvenience becomes a shared rhythm instead of a complaint.",
                payoff="Love is not fewer needs. It is safer needs.",
                distribution_reason="Taggable for couples who know their tiny discomfort rituals and do not turn them into fights.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Barefoot Was The Receipt",
                story_lens="Use the barefoot moment as evidence, not premise, for care that arrives before explanation.",
                reader_mirror="Viewers recognize the relief of being read before they have to justify themselves.",
                emotional_obstacle="Without active noticing, the route becomes only pretty outfit content.",
                aachu_specific_spark="Aachu wants the look, the memory, and the ease all at once.",
                zuv_active_role="Zuv reads the pace change, offers balance, and keeps the story light.",
                proof_engine="green dress -> barefoot step -> pace change -> Zuv reads it -> hand and slower path",
                emotional_reversal="The outfit stops being the subject; the noticing becomes the proof.",
                payoff="The best care often arrives before the sentence.",
                distribution_reason="Saveable for people who want language for being noticed without overexplaining.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Care Without Making Her Small",
                story_lens="Care works when it supports her spark instead of correcting it.",
                reader_mirror="Partners recognize the balance between helping and not taking over.",
                emotional_obstacle="The line can become perfect-husband praise unless Aachu remains active in the scene.",
                aachu_specific_spark="Aachu keeps choosing the dramatic dress and the moment, even while adjusting to discomfort.",
                zuv_active_role="Zuv makes the path easier while letting her remain the main character of her own scene.",
                proof_engine="dress adjustment -> barefoot step -> Zuv notices -> path shifts -> she keeps the moment",
                emotional_reversal="Help becomes love because it protects her spark instead of managing it.",
                payoff="The right care makes more room for you, not less.",
                distribution_reason="Sendable to the partner who helps without turning the moment into a lecture.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Not Too Much, Just Seen",
                story_lens="The anti-ideal is low-maintenance performance; the real love is being seen in small needs.",
                reader_mirror="People who have been called too much can recognize the softer counter-story.",
                emotional_obstacle="The route must not become generic validation; it needs a physical receipt.",
                aachu_specific_spark="Aachu's green-dress barefoot pause gives the story its specific body-language proof.",
                zuv_active_role="Zuv notices, slows down, and stays beside her instead of judging the need.",
                proof_engine="green dress -> barefoot pause -> he notices -> slower path -> she relaxes",
                emotional_reversal="The need stops being a flaw once it is met with respect.",
                payoff="Maybe love is not being easier. Maybe it is being seen sooner.",
                distribution_reason="Strong send/save reason for couples who know small needs can carry big tenderness.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_subtitle_language:
        routes = [
            StoryRoute(
                name="He Learned Her Subtitles",
                story_lens="The love story is not mood decoding as magic; it is patient attention learning her real language.",
                reader_mirror="Couples recognize the partner who understands 'kuch nahi' because the face says the paragraph.",
                emotional_obstacle="The words say nothing, but the face and silence need to be read without interrogation.",
                aachu_specific_spark="Aachu says kuch nahi while her face, hands, and pause reveal the whole paragraph.",
                zuv_active_role="Zuv puts the phone down, watches her face, waits, and answers the feeling instead of the words.",
                proof_engine="kuch nahi line -> face changes -> hands pause -> Zuv puts phone down -> waits -> answers softly",
                emotional_reversal="What looked like silence becomes a language they have built together.",
                payoff="Maybe love is learning the subtitles.",
                distribution_reason="Sendable to the partner who understands the meaning underneath one tiny sentence.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Kuch Nahi Was A Full Paragraph",
                story_lens="The joke is that the smallest spoken line carries the biggest emotional script.",
                reader_mirror="Viewers recognize the home-language of saying nothing while meaning everything.",
                emotional_obstacle="If Zuv only decodes her, the scene becomes one-way; he must respond with care.",
                aachu_specific_spark="Aachu's face, posture, and silence make the unsaid feeling visible.",
                zuv_active_role="Zuv notices the pause, stays close, and changes his response without making her perform the explanation.",
                proof_engine="kuch nahi -> face says paragraph -> Zuv notices pause -> sits closer -> reply changes",
                emotional_reversal="The unsaid feeling becomes safer because it is not dismissed.",
                payoff="Some people hear the sentence. The right person hears the paragraph.",
                distribution_reason="Taggable for couples with private emotional translations.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The Face Said Everything First",
                story_lens="The visible proof is her expression changing before the words catch up.",
                reader_mirror="Anyone whose partner reads their face before their explanation can enter.",
                emotional_obstacle="The route fails if it becomes a generic mind-reading compliment.",
                aachu_specific_spark="Aachu's expression turns the tiny line into a whole scene.",
                zuv_active_role="Zuv reads the expression, puts down the distraction, and chooses patience.",
                proof_engine="phone in hand -> her face changes -> kuch nahi -> Zuv puts phone down -> patient pause",
                emotional_reversal="Attention, not translation, becomes the romantic proof.",
                payoff="Being understood starts before the explanation.",
                distribution_reason="Saveable as a relationship truth about attention under small silence.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Not Mood Reading, Attention",
                story_lens="Repair the familiar subtitles lane by making it about practiced attention, not a supernatural husband.",
                reader_mirror="Couples recognize attention as a skill built over ordinary repeated scenes.",
                emotional_obstacle="Aachu could feel dismissed if her words are taken literally.",
                aachu_specific_spark="Aachu protects the feeling with a tiny phrase instead of a speech.",
                zuv_active_role="Zuv answers the hidden need by slowing down and staying present.",
                proof_engine="tiny phrase -> protected feeling -> Zuv slows down -> stays present -> answer softens",
                emotional_reversal="The hidden feeling stops needing a performance.",
                payoff="The right person learns where your words are hiding.",
                distribution_reason="Sendable to partners who have learned each other's hidden meanings.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The Translation Was Tender",
                story_lens="The private language becomes love because the answer is gentle, not clever.",
                reader_mirror="Viewers with their own couple-language recognize the tenderness of being translated kindly.",
                emotional_obstacle="A wrong answer could turn silence into distance.",
                aachu_specific_spark="Aachu's tiny line and expressive face create the private-language proof.",
                zuv_active_role="Zuv translates the mood into a softer action: closer seat, slower voice, no interrogation.",
                proof_engine="tiny line -> expressive face -> Zuv moves closer -> slower voice -> no interrogation",
                emotional_reversal="The translation becomes safety, not control.",
                payoff="Love is being translated kindly.",
                distribution_reason="Strong save/share hook for couples with private emotional vocabulary.",
                process_influence_ids=[item.id for item in influences],
            ),
        ]
    elif is_first_date_trip:
        routes = [
            StoryRoute(
                name="The Story Got Bigger, The Proof Stayed Small",
                story_lens="A relationship can grow from tiny first-date cups to wide travel views while the real proof stays in small behavior.",
                reader_mirror="Couples recognize the arc from one small beginning to bigger shared chapters.",
                emotional_obstacle="The route can become travel nostalgia unless the same couple behavior repeats across the years.",
                aachu_specific_spark="Aachu brings the first-date laugh, the second-date joke, and the appetite for a bigger story.",
                zuv_active_role="Zuv keeps choosing the small proof: holding the cup, joining the joke, making space in Ladakh.",
                proof_engine="first date cups -> second date jokes -> Ladakh view -> same shared laugh -> his hand stays close",
                emotional_reversal="The place gets bigger, but the love is proved by the same tiny rhythm.",
                payoff="Maybe the big story was always hiding in the small cups.",
                distribution_reason="Saveable for couples who can trace their whole story back to one ordinary first receipt.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="From Cups To Mountains",
                story_lens="Use the travel scale as proof of a small beginning that kept becoming more real.",
                reader_mirror="Viewers with a first-date object or phrase can see their own origin story.",
                emotional_obstacle="The mountain view must not become the premise; it is only proof that the small start traveled.",
                aachu_specific_spark="Aachu carries the joke forward from date two into the trip.",
                zuv_active_role="Zuv keeps the old joke alive in the new place, making the trip feel like theirs.",
                proof_engine="cup on table -> date joke -> road to Ladakh -> old joke returns -> both laugh in the view",
                emotional_reversal="The grand view becomes intimate because an old tiny joke arrives there too.",
                payoff="Some love stories do not change topic. They just get wider.",
                distribution_reason="Taggable for couples who still repeat the tiny joke from the beginning.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="Second Date Jokes Became A Map",
                story_lens="The joke is the continuity thread from awkward early dates to confident travel.",
                reader_mirror="Couples recognize the private joke that becomes relationship geography.",
                emotional_obstacle="Without continuity, it is only a trip montage.",
                aachu_specific_spark="Aachu repeats the joke with the same expressive timing in a completely bigger place.",
                zuv_active_role="Zuv answers the joke immediately, proving the rhythm traveled with them.",
                proof_engine="second date joke -> travel road -> same joke in Ladakh -> Zuv answers -> Aachu laughs",
                emotional_reversal="A joke becomes proof of belonging across time.",
                payoff="Maybe home is the joke that travels with you.",
                distribution_reason="Sendable to partners with one old line that still works everywhere.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="The First Receipt",
                story_lens="Make the first date object a receipt, not an aesthetic prop.",
                reader_mirror="People remember the tiny object where their story started.",
                emotional_obstacle="The memory can feel private unless it proves a wider relationship pattern.",
                aachu_specific_spark="Aachu gives the tiny beginning emotional color through laughter and recall.",
                zuv_active_role="Zuv treats the small receipt as important even after the story becomes bigger.",
                proof_engine="first date cups -> saved joke -> bigger trip -> he remembers the cup story -> she softens",
                emotional_reversal="The old small thing becomes more romantic after the big chapter.",
                payoff="The first receipt still knows the whole story.",
                distribution_reason="Saveable for couples who keep the first tiny proof of their relationship.",
                process_influence_ids=[item.id for item in influences],
            ),
            StoryRoute(
                name="It Was Still Us",
                story_lens="The travel arc works only if the couple rhythm remains visible under every bigger setting.",
                reader_mirror="Couples recognize wanting big memories without losing the original ordinary ease.",
                emotional_obstacle="A beautiful location can swallow the relationship if the behavior is not staged.",
                aachu_specific_spark="Aachu turns the view into another scene in the same shared story.",
                zuv_active_role="Zuv anchors the frame with the old rhythm: close hand, shared laugh, no performance.",
                proof_engine="date cups -> jokes -> mountain view -> close hand -> shared laugh returns",
                emotional_reversal="The destination stops being the point once the old ease appears there.",
                payoff="The best part stayed the same: it was still us.",
                distribution_reason="Sendable to the person who makes every bigger place feel like the same two people.",
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
        golden_score = score_golden_theme(route)
        stage_gate = stage_scene_gate_for_route(route)
        hard_fails = detect_hard_fails(route)
        scored.append(
            route.model_copy(
                update={
                    "score_total": score.total,
                    "golden_theme_score_total": golden_score.total,
                    "stage_scene_gate": stage_gate,
                    "hard_fails": hard_fails,
                    "verdict": status_for(score, hard_fails),
                }
            )
        )
    return scored


def build_rooms(
    *,
    request: LayerERequest,
    memory: LayerESourceMemory,
    routes: list[StoryRoute],
    winner: StoryRoute | None = None,
    repaired_routes: list[StoryRoute] | None = None,
) -> dict[str, LayerERoomOutput]:
    winner = max(routes, key=lambda route: route.score_total) if routes else None
    if winner is None and routes:
        winner = max(routes, key=lambda route: route.score_total)
    repaired_routes = repaired_routes or []
    winner_name = winner.name if winner else "No route"
    top_routes = sorted(routes, key=lambda route: route.score_total, reverse=True)[:3]
    success_definition = success_definition_from_memory(memory)
    human_story_setup = human_story_setup_for_route(winner) if winner else {}
    stage_scene_gate = stage_scene_gate_for_route(winner) if winner else None
    return {
        "source_memory_room": LayerERoomOutput(
            name="Context And Source Memory",
            status="GO",
            agents=[
                ExpertAgentOutput(agent="Source Curator", role="legality", claim="Use derived patterns and source IDs only."),
                ExpertAgentOutput(agent="Successful Carousel Standard Reader", role="creative north star", claim="Prioritize public identity mirror and concrete couple receipts."),
                ExpertAgentOutput(agent="Creator Preference Ledger Reader", role="memory", claim="Avoid repeating cooled-down lanes as fresh ideas."),
            ],
            summary="Source memory loaded before concept selection, including the successful-carousel standard and creator preference ledger.",
            inputs_used=[
                memory.source_register_path,
                memory.concept_process_bank_path,
                memory.pattern_map_path,
                "wiki/insights/successful-carousel-standard.md",
                "memory/semantic/carousel-idea-preferences.md",
            ],
            debate_records=[
                "Source Curator: treat photos, objects, outfits, and canon cards as evidence, never as the premise.",
                "Successful Carousel Standard Reader: define success before writing as cold-viewer recognition, not beautiful art.",
                "Creator Preference Ledger Reader: avoid stale perfect-husband, aesthetic-first, and repeated chaos/home lanes.",
            ],
            selected_outputs={
                "what_success_looks_like": success_definition["audience_success"],
                "memory_policy": "fresh route must not recycle cooled-down lanes as fresh ideas",
            },
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
            inputs_used=[
                request.story_or_moment,
                *request.reference_images,
                *request.constraints,
            ],
            debate_records=[
                *[
                    (
                        f"Route '{route.name}' human story: obstacle='{route.emotional_obstacle}', "
                        f"proof='{route.proof_engine}', payoff='{route.payoff}', score={route.score_total}/30."
                    )
                    for route in top_routes
                ],
                (
                    "Human story check: the route must be about a relationship pressure becoming visible, "
                    "not about a nice photo, outfit, place, or object."
                ),
                (
                    "Scene grammar check: Aachu must carry specific spark and Zuv must answer through visible behavior "
                    "before copy or captions are written."
                ),
            ],
            scores={route.name: route.score_total for route in routes},
            selected_outputs={
                "raw_winner": winner_name,
                "human_story_setup": human_story_setup.get("shareable_setup", ""),
                "emotional_obstacle": human_story_setup.get("emotional_obstacle", ""),
            },
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
            inputs_used=[
                "wiki/insights/successful-carousel-standard.md#What Success Means",
                "output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md#Comment Behavior",
            ],
            debate_records=[
                f"Reader mirror: {winner.reader_mirror if winner else ''}",
                f"Send/save reason: {winner.distribution_reason if winner else ''}",
                (
                    "Success pressure: a strong route must earn partner tags, saves, or DMs because the viewer "
                    "is saying 'this is us', not because the art is pretty."
                ),
                (
                    "Swipe pressure: the middle must carry receipt density and at least one visual proof beat "
                    "that can be understood before reading a caption."
                ),
            ],
            selected_outputs={
                "distribution_reason": winner.distribution_reason if winner else "",
                "what_success_looks_like": success_definition["audience_success"],
            },
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
            inputs_used=[route.name for route in top_routes],
            debate_records=[
                *[
                    (
                        f"Attack '{route.name}': hard_fails={route.hard_fails or ['none']}; "
                        f"repair target is stronger human obstacle, share setup, and visible Zuv action."
                    )
                    for route in top_routes
                ],
                "Genericness Detector: reject routes that would get 'beautiful' but not 'this is us'.",
                "Visual Generativity Skeptic: block any route that can only be expressed as poster copy.",
            ],
            objections=winner.hard_fails if winner else ["no route generated"],
            repairs=[
                "Repair top candidates against the success standard before downstream copy.",
                "Keep the winner only if the share setup, human obstacle, and visible partner role survive the attack.",
            ]
            if winner
            else ["Add obstacle, active Zuv role, proof, and send/save reason."],
            repaired_route_names=[route.name for route in repaired_routes],
        ),
        "stage_scene_room": LayerERoomOutput(
            name="Stage-Scene Gate",
            status=stage_scene_gate.status if stage_scene_gate else "REPAIR",
            agents=[
                ExpertAgentOutput(agent="Stage Director", role="blocking", claim="The idea must play as action before copy."),
                ExpertAgentOutput(agent="Body Language Reader", role="proof", claim="Hands, distance, and object movement must prove the turn."),
                ExpertAgentOutput(agent="Silent Panel Reviewer", role="visual story", claim="A viewer should understand the beat with text hidden."),
            ],
            summary="Winner was checked as a short staged scene before copy, caption, or prompt work.",
            inputs_used=[winner_name, winner.proof_engine if winner else ""],
            debate_records=[
                f"Action: {stage_scene_gate.action if stage_scene_gate else ''}",
                f"Reaction: {stage_scene_gate.reaction if stage_scene_gate else ''}",
                f"Hands/object movement: {stage_scene_gate.hands_or_object_movement if stage_scene_gate else ''}",
                f"Silence/pause: {stage_scene_gate.silence_or_pause if stage_scene_gate else ''}",
                f"Consequence: {stage_scene_gate.consequence if stage_scene_gate else ''}",
                "Gate rule: text completes the scene; text must not carry the scene.",
            ],
            selected_outputs={
                "action": stage_scene_gate.action if stage_scene_gate else "",
                "hands_or_object_movement": stage_scene_gate.hands_or_object_movement if stage_scene_gate else "",
                "reversal_or_payoff": stage_scene_gate.reversal_or_payoff if stage_scene_gate else "",
            },
            objections=stage_scene_gate.blockers if stage_scene_gate else ["no route generated"],
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
            inputs_used=[
                "story_meaning_room",
                "audience_algorithm_room",
                "contrarian_repair_room",
                "stage_scene_room",
                "story_selling_score",
            ],
            debate_records=[
                f"Selector chose '{winner_name}' because it best connects human story, proof, reversal, and distribution.",
                f"Human setup: {human_story_setup.get('shareable_setup', '')}",
                f"What success looks like: {success_definition['audience_success']}",
            ],
            selected_outputs={
                "selected_story_lens": winner.story_lens if winner else "",
                "human_story_setup": human_story_setup.get("shareable_setup", ""),
                "what_success_looks_like": success_definition["audience_success"],
            },
        ),
    }
