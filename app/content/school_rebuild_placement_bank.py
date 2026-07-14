"""Approved authored content for the School Prep English placement staircase.

Placement content is self-contained and independent from chapter seed content.
Every scored item belongs to one primary skill and every reachable source band
has dedicated targeted and confirmatory variants.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Literal

from app.content.school_rebuild_placement_validation import (
    RUBRIC_REMEDIATION_BY_CRITERION,
    STRICT_RUBRIC_CRITERIA_BY_REF,
    normalize_placement_answer,
    validate_placement_bank,
)


PlacementDiagnosticStage = Literal["snapshot", "targeted_diagnostic", "confirmatory"]
PlacementItemType = Literal["short_answer", "multiple_choice", "fill_blank"]
PlacementEvaluationMode = Literal["deterministic", "strict_rubric"]
PlacementTrackDomain = Literal["reading", "vocabulary", "grammar", "writing"]


@dataclass(frozen=True)
class PlacementApproval:
    engineering_qa_status: Literal["in_progress", "passed"]
    human_review_status: Literal["pending", "approved"]
    launch_status: Literal["blocked_pending_human_review", "approved"]
    reviewed_by: str
    reviewed_on: str
    version: str
    reference: str


@dataclass(frozen=True)
class PlacementLearnerCopy:
    instruction: str
    support: str


@dataclass(frozen=True)
class PlacementMisconceptionCluster:
    code: str
    learner_safe_label: str
    triggers: tuple[str, ...]


@dataclass(frozen=True)
class SchoolPlacementBankItem:
    item_id: str
    track_id: str
    subject_id: str
    target_class_no: int
    source_class_no: int
    stage: PlacementDiagnosticStage
    primary_skill_id: str
    telemetry_skill_ids: tuple[str, ...]
    learner_skill_label: str
    prompt: str
    passage: str
    item_type: PlacementItemType
    evaluation_mode: PlacementEvaluationMode
    answer_key: str | None
    accepted_answers: tuple[str, ...]
    rubric_ref: str | None
    misconception_clusters: tuple[PlacementMisconceptionCluster, ...]
    localized_copy: Mapping[str, PlacementLearnerCopy]
    approval: PlacementApproval
    options: tuple[str, ...] = ()

    @property
    def skill_ids(self) -> tuple[str, ...]:
        """Compatibility view: only the primary skill is score-bearing."""

        return (self.primary_skill_id,)

    @property
    def misconception_tags(self) -> tuple[str, ...]:
        return tuple(cluster.code for cluster in self.misconception_clusters)


@dataclass(frozen=True)
class PlacementBand:
    source_class_no: int
    variants: tuple[SchoolPlacementBankItem, ...]


@dataclass(frozen=True)
class PlacementTrack:
    track_id: str
    subject_id: str
    target_class_no: int
    domain: PlacementTrackDomain
    primary_skill_id: str
    learner_skill_label: str
    snapshot_item: SchoolPlacementBankItem
    bands: tuple[PlacementBand, ...]
    approval: PlacementApproval


@dataclass(frozen=True)
class _ItemSeed:
    key: str
    passage: str
    prompt: str
    item_type: PlacementItemType
    answer_key: str | None = None
    accepted_answers: tuple[str, ...] = ()
    options: tuple[str, ...] = ()
    rubric_ref: str | None = None
    misconception_code: str = "needs_review"


_APPROVAL = PlacementApproval(
    engineering_qa_status="passed",
    human_review_status="pending",
    launch_status="blocked_pending_human_review",
    reviewed_by="task-1-engineering-qa",
    reviewed_on="2026-07-12",
    version="placement-bank-v1",
    reference="app/content/school_rebuild_placement_review_manifest.json",
)


_LOCALIZED_COPY: Mapping[
    PlacementTrackDomain,
    Mapping[str, PlacementLearnerCopy],
] = MappingProxyType({
    "reading": MappingProxyType({
        "en": PlacementLearnerCopy("Read the English text, then answer.", "Return to the sentence that gives the clearest clue."),
        "hi": PlacementLearnerCopy("अंग्रेज़ी पाठ पढ़ें, फिर उत्तर दें।", "सबसे साफ़ संकेत वाले वाक्य को दोबारा देखें।"),
        "hi_en": PlacementLearnerCopy("English text padho, phir answer do.", "Sabse clear clue wale sentence ko dobara dekho."),
    }),
    "vocabulary": MappingProxyType({
        "en": PlacementLearnerCopy("Use the English sentence clues to choose or write the word.", "Read the words around the blank or highlighted word."),
        "hi": PlacementLearnerCopy("अंग्रेज़ी वाक्य के संकेतों से शब्द चुनें या लिखें।", "खाली जगह या दिए गए शब्द के आसपास के शब्द पढ़ें।"),
        "hi_en": PlacementLearnerCopy("English sentence ke clues se word chuno ya likho.", "Blank ya diye gaye word ke aas-paas ke words padho."),
    }),
    "grammar": MappingProxyType({
        "en": PlacementLearnerCopy("Read the full English sentence before answering.", "Check which choice makes the whole sentence clear and complete."),
        "hi": PlacementLearnerCopy("उत्तर देने से पहले पूरा अंग्रेज़ी वाक्य पढ़ें।", "देखें कि कौन-सा विकल्प पूरे वाक्य को साफ़ और पूरा बनाता है।"),
        "hi_en": PlacementLearnerCopy("Answer se pehle poora English sentence padho.", "Dekho kaunsa option sentence ko clear aur complete banata hai."),
    }),
    "writing": MappingProxyType({
        "en": PlacementLearnerCopy("Write your response in English.", "Use the text details and make your meaning complete."),
        "hi": PlacementLearnerCopy("अपना उत्तर अंग्रेज़ी में लिखें।", "पाठ के संकेत लें और अपनी बात पूरी लिखें।"),
        "hi_en": PlacementLearnerCopy("Apna response English mein likho.", "Text ke clues use karo aur apni baat poori likho."),
    }),
})


def _det(
    key: str,
    passage: str,
    prompt: str,
    answer_key: str,
    *alternatives: str,
    options: tuple[str, ...] = (),
    item_type: PlacementItemType = "short_answer",
    misconception: str = "deterministic_miss",
) -> _ItemSeed:
    accepted_answers: list[str] = []
    normalized_answers: set[str] = set()
    for answer in (answer_key, *alternatives):
        normalized = normalize_placement_answer(answer)
        if normalized not in normalized_answers:
            accepted_answers.append(answer)
            normalized_answers.add(normalized)
    return _ItemSeed(
        key=key,
        passage=passage,
        prompt=prompt,
        item_type=item_type,
        answer_key=answer_key,
        accepted_answers=tuple(accepted_answers),
        options=options,
        misconception_code=misconception,
    )


def _open(
    key: str,
    passage: str,
    prompt: str,
    rubric_ref: str,
    *,
    misconception: str,
) -> _ItemSeed:
    return _ItemSeed(
        key=key,
        passage=passage,
        prompt=prompt,
        item_type="short_answer",
        rubric_ref=rubric_ref,
        misconception_code=misconception,
    )


def _clusters(seed: _ItemSeed) -> tuple[PlacementMisconceptionCluster, ...]:
    if seed.item_type == "multiple_choice":
        return tuple(
            PlacementMisconceptionCluster(
                code=f"{seed.misconception_code}_distractor_{index}",
                learner_safe_label="Recheck the clue that separates this choice from the text.",
                triggers=(option,),
            )
            for index, option in enumerate(seed.options, start=1)
            if option != seed.answer_key
        )
    if seed.rubric_ref:
        return tuple(
            PlacementMisconceptionCluster(
                code=f"{seed.misconception_code}_{criterion_id}",
                learner_safe_label=RUBRIC_REMEDIATION_BY_CRITERION[criterion_id],
                triggers=(f"criterion:{criterion_id}",),
            )
            for criterion_id in STRICT_RUBRIC_CRITERIA_BY_REF[seed.rubric_ref]
        )
    return (
        PlacementMisconceptionCluster(
            code=seed.misconception_code,
            learner_safe_label="Re-read the clue and try the same skill again.",
            triggers=("no_accepted_match",),
        ),
    )


def _make_item(
    *,
    class_no: int,
    track_id: str,
    domain: PlacementTrackDomain,
    primary_skill_id: str,
    learner_skill_label: str,
    source_class_no: int,
    stage: PlacementDiagnosticStage,
    seed: _ItemSeed,
) -> SchoolPlacementBankItem:
    return SchoolPlacementBankItem(
        item_id=f"sp_c{class_no}_{track_id.rsplit('.', 1)[-1]}_{stage}_{source_class_no}_{seed.key}",
        track_id=track_id,
        subject_id="english",
        target_class_no=class_no,
        source_class_no=source_class_no,
        stage=stage,
        primary_skill_id=primary_skill_id,
        telemetry_skill_ids=(),
        learner_skill_label=learner_skill_label,
        prompt=seed.prompt,
        passage=seed.passage,
        item_type=seed.item_type,
        evaluation_mode="strict_rubric" if seed.rubric_ref else "deterministic",
        answer_key=seed.answer_key,
        accepted_answers=seed.accepted_answers,
        rubric_ref=seed.rubric_ref,
        misconception_clusters=_clusters(seed),
        localized_copy=_LOCALIZED_COPY[domain],
        approval=_APPROVAL,
        options=seed.options,
    )


def _track(
    class_no: int,
    slug: str,
    domain: PlacementTrackDomain,
    primary_skill_id: str,
    label: str,
    snapshot_source: int,
    seeds: tuple[_ItemSeed, _ItemSeed, _ItemSeed, _ItemSeed, _ItemSeed],
) -> PlacementTrack:
    lower_band = max(1, class_no - 1)
    track_id = f"english.c{class_no}.{slug}"
    snapshot_seed, lower_target, lower_confirm, target_target, target_confirm = seeds
    snapshot_item = _make_item(
        class_no=class_no,
        track_id=track_id,
        domain=domain,
        primary_skill_id=primary_skill_id,
        learner_skill_label=label,
        source_class_no=snapshot_source,
        stage="snapshot",
        seed=snapshot_seed,
    )

    def variant(source: int, stage: PlacementDiagnosticStage, seed: _ItemSeed) -> SchoolPlacementBankItem:
        return _make_item(
            class_no=class_no,
            track_id=track_id,
            domain=domain,
            primary_skill_id=primary_skill_id,
            learner_skill_label=label,
            source_class_no=source,
            stage=stage,
            seed=seed,
        )

    return PlacementTrack(
        track_id=track_id,
        subject_id="english",
        target_class_no=class_no,
        domain=domain,
        primary_skill_id=primary_skill_id,
        learner_skill_label=label,
        snapshot_item=snapshot_item,
        bands=(
            PlacementBand(
                source_class_no=lower_band,
                variants=(
                    variant(lower_band, "targeted_diagnostic", lower_target),
                    variant(lower_band, "confirmatory", lower_confirm),
                ),
            ),
            PlacementBand(
                source_class_no=class_no,
                variants=(
                    variant(class_no, "targeted_diagnostic", target_target),
                    variant(class_no, "confirmatory", target_confirm),
                ),
            ),
        ),
        approval=_APPROVAL,
    )


def _class_2_tracks() -> tuple[PlacementTrack, ...]:
    return (
        _track(2, "sentence_detail_place", "reading", "reading.sentence_comprehension", "Find where something is", 1, (
            _det("kite", "A red kite is in the sky.", "Where is the kite?", "sky", "in the sky"),
            _det("cat", "The cat sleeps on a rug.", "Where does the cat sleep?", "rug", "on a rug", "on the rug"),
            _det("cup", "Mina keeps her cup on the table.", "Where is Mina's cup?", "table", "on the table"),
            _det("lunchbox", "Arun put his lunch box beside the school bag.", "Where did Arun put the lunch box?", "beside the school bag", "beside the bag"),
            _det("shoes", "Ria left her shoes under the bed before sleeping.", "Where are Ria's shoes?", "under the bed", "bed"),
        )),
        _track(2, "sentence_detail_action", "reading", "reading.sentence_comprehension", "Find who did an action", 1, (
            _det("runs", "Ravi runs to the gate.", "Who runs to the gate?", "Ravi"),
            _det("sweeps", "Asha sweeps the classroom floor.", "Who sweeps the floor?", "Asha"),
            _det("waters", "Kabir waters the small plant every day.", "Who waters the plant?", "Kabir"),
            _det("opens", "The teacher opens the blue book after lunch.", "Who opens the blue book?", "the teacher", "teacher"),
            _det("carries", "Neha carries a basket of oranges to her mother.", "Who carries the basket?", "Neha"),
        )),
        _track(2, "context_word", "vocabulary", "reading.word_meaning_context", "Use a sentence clue to understand a word", 1, (
            _det("tiny", "The tiny ant is very small.", "What does tiny mean?", "small", options=("small", "loud", "wet"), item_type="multiple_choice", misconception="context_clue"),
            _det("huge", "The huge elephant is much bigger than the goat.", "What does huge mean here?", "very big", options=("very big", "very quiet", "very thin"), item_type="multiple_choice", misconception="context_clue"),
            _det("empty", "The empty bowl has no food in it.", "What does empty mean?", "having nothing inside", options=("having nothing inside", "full of rice", "made of metal"), item_type="multiple_choice", misconception="context_clue"),
            _det("quick", "A quick rabbit reached the tree before the slow turtle.", "What does quick mean?", "fast", options=("fast", "sleepy", "heavy", "late"), item_type="multiple_choice", misconception="context_clue"),
            _det("silent", "The library was silent; nobody was speaking.", "What does silent mean here?", "quiet", options=("quiet", "crowded", "bright", "open"), item_type="multiple_choice", misconception="context_clue"),
        )),
        _track(2, "word_choice", "vocabulary", "vocab.chapter_word_usage", "Choose a word that fits the sentence", 1, (
            _det("drink", "I am thirsty. I need a ___.", "Which word fits the blank?", "drink", options=("drink", "shoe", "song"), item_type="multiple_choice", misconception="word_fit"),
            _det("warm", "The sun makes the stone feel ___.", "Which word fits the blank?", "warm", options=("warm", "hungry", "round"), item_type="multiple_choice", misconception="word_fit"),
            _det("bark", "The dog began to ___ when the bell rang.", "Which word fits the blank?", "bark", options=("bark", "read", "swim"), item_type="multiple_choice", misconception="word_fit"),
            _det("borrow", "Sita asked to ___ a pencil and return it later.", "Which word fits the blank?", "borrow", options=("borrow", "break", "hide", "paint"), item_type="multiple_choice", misconception="word_fit"),
            _det("careful", "The glass may break, so please be ___.", "Which word fits the blank?", "careful", options=("careful", "noisy", "empty", "early"), item_type="multiple_choice", misconception="word_fit"),
        )),
        _track(2, "naming_words", "grammar", "grammar.noun_verb_adjective", "Recognize naming words", 2, (
            _det("ball", "The ball rolled away.", "Which word names a thing?", "ball", options=("ball", "rolled", "away"), item_type="multiple_choice", misconception="noun_role"),
            _det("girl", "The girl smiled brightly.", "Which word names a person?", "girl", options=("girl", "smiled", "brightly"), item_type="multiple_choice", misconception="noun_role"),
            _det("park", "We played in the park.", "Which word names a place?", "park", options=("park", "played", "in"), item_type="multiple_choice", misconception="noun_role"),
            _det("doctor", "The kind doctor helped the child.", "Which word names a person?", "doctor", options=("doctor", "kind", "helped", "the"), item_type="multiple_choice", misconception="noun_role"),
            _det("market", "Mother walked to the busy market.", "Which word names a place?", "market", options=("market", "walked", "busy", "to"), item_type="multiple_choice", misconception="noun_role"),
        )),
        _track(2, "sentence_order", "grammar", "grammar.sentence_order", "Put words in sentence order", 2, (
            _det("birds_fly", "Words: birds / fly", "Write the words as a sentence.", "birds fly", "Birds fly"),
            _det("I_read", "Words: read / I", "Put the words in the right order.", "I read", "i read"),
            _det("sun_shines", "Words: shines / sun / the", "Put the words in the right order.", "the sun shines", "The sun shines"),
            _det("children_play", "Words: children / outside / play", "Make one correct sentence.", "children play outside", "Children play outside"),
            _det("soup_hot", "Words: soup / is / the / hot", "Make one correct sentence.", "the soup is hot", "The soup is hot"),
        )),
        _track(2, "complete_sentence_action", "writing", "writing.complete_sentence", "Complete a sentence with an action", 2, (
            _open("fish", "A fish moves through clear water beside green plants.", "Write one complete English sentence about what the fish is doing.", "school.strict.complete_sentence.class2.v1", misconception="complete_action"),
            _open("baby", "A baby has closed eyes and rests quietly in a cot.", "Write one complete English sentence about the baby.", "school.strict.complete_sentence.foundation.v1", misconception="complete_action"),
            _open("bell", "The school bell makes a loud sound at the start of class.", "Write one complete English sentence about the bell.", "school.strict.complete_sentence.foundation.v1", misconception="complete_action"),
            _open("farmers", "Farmers place seeds in the soil at the start of the season.", "Write one complete English sentence about what the farmers are doing.", "school.strict.complete_sentence.class2.v1", misconception="complete_action"),
            _open("clouds", "Dark clouds travel across the sky before the rain.", "Write one complete English sentence about the clouds.", "school.strict.complete_sentence.class2.v1", misconception="complete_action"),
        )),
        _track(2, "complete_sentence_idea", "writing", "writing.complete_sentence", "Write one complete idea", 2, (
            _open("rain", "Rain fell outside the classroom.", "Write one complete English sentence about the rain.", "school.strict.complete_sentence.class2.v1", misconception="complete_idea"),
            _open("friend", "A friend shares crayons with you.", "Write one complete English sentence about the friend.", "school.strict.complete_sentence.foundation.v1", misconception="complete_idea"),
            _open("tree", "A tall tree gives shade in the playground.", "Write one complete English sentence about the tree.", "school.strict.complete_sentence.foundation.v1", misconception="complete_idea"),
            _open("morning", "The school garden looks fresh in the morning.", "Write one complete English sentence about the garden.", "school.strict.complete_sentence.class2.v1", misconception="complete_idea"),
            _open("helping", "Dev picks up books that fell from a shelf.", "Write one complete English sentence about Dev.", "school.strict.complete_sentence.class2.v1", misconception="complete_idea"),
        )),
    )


def _class_3_tracks() -> tuple[PlacementTrack, ...]:
    return (
        _track(3, "sentence_detail", "reading", "reading.sentence_comprehension", "Find a detail in a sentence", 2, (
            _det("mat", "Rina sat on the mat near the window.", "Where did Rina sit?", "on the mat", "mat"),
            _det("mangoes", "Nila put three mangoes in a basket.", "What did Nila put in the basket?", "three mangoes", "mangoes"),
            _det("shell", "Mira found a shell beside the river.", "What did Mira find?", "a shell", "shell"),
            _det("umbrella", "Farah carried a yellow umbrella to school.", "What colour was Farah's umbrella?", "yellow"),
            _det("ticket", "The conductor gave Mohan a blue ticket.", "What did the conductor give Mohan?", "a blue ticket", "ticket", "a ticket"),
        )),
        _track(3, "main_idea", "reading", "reading.paragraph_main_idea", "Find what a short passage is mostly about", 2, (
            _det("pets", "A dog needs food, clean water, and a safe place to rest.", "What is this text mostly about?", "caring for a dog", options=("caring for a dog", "riding a bus", "making tea"), item_type="multiple_choice", misconception="main_idea"),
            _det("garden", "Aman watered the plants and removed dry leaves. Soon, new shoots appeared.", "What is the text mostly about?", "Aman caring for plants", options=("Aman caring for plants", "Aman losing a toy", "Aman missing school"), item_type="multiple_choice", misconception="main_idea"),
            _det("library", "The children chose books, sat quietly, and read for thirty minutes.", "What is the text mostly about?", "children reading", options=("children reading", "children cooking", "children racing"), item_type="multiple_choice", misconception="main_idea"),
            _det("recycling", "Our class placed paper in one bin and food waste in another. We wanted to reuse what we could.", "What is the passage mostly about?", "sorting waste for recycling", options=("sorting waste for recycling", "buying notebooks", "painting a wall", "planning a race"), item_type="multiple_choice", misconception="main_idea"),
            _det("bus_stop", "People formed a line at the bus stop. Each person waited for a turn to board.", "What is the passage mostly about?", "waiting in an orderly line", options=("waiting in an orderly line", "repairing a bus", "selling fruit", "crossing a river"), item_type="multiple_choice", misconception="main_idea"),
        )),
        _track(3, "reason_inference", "reading", "reading.inference_reason", "Use a text clue to explain why", 2, (
            _open("lamp", "The room was dark, so Kabir switched on the lamp.", "Why did Kabir switch on the lamp?", "school.strict.reason_from_text.v1", misconception="reason_clue"),
            _open("water", "Sana drank water after running in the sun.", "Why did Sana drink water?", "school.strict.reason_from_text.v1", misconception="reason_clue"),
            _open("sweater", "Anu wore a sweater because the cold wind was strong.", "Why did Anu wear a sweater?", "school.strict.reason_from_text.v1", misconception="reason_clue"),
            _open("whisper", "The baby was sleeping, so Vikram spoke in a whisper.", "Why did Vikram whisper?", "school.strict.reason_from_text.v1", misconception="reason_clue"),
            _open("late", "The road was blocked by a fallen tree. The school bus arrived late.", "Why did the bus arrive late?", "school.strict.reason_from_text.v1", misconception="reason_clue"),
        )),
        _track(3, "context_word", "vocabulary", "reading.word_meaning_context", "Use context to understand a word", 2, (
            _det("tiny", "The tiny seed was small enough to rest on one finger.", "What does tiny mean?", "small", options=("small", "heavy", "angry"), item_type="multiple_choice", misconception="context_clue"),
            _det("clever", "The clever crow used stones to raise the water.", "What does clever mean here?", "smart", options=("smart", "sleepy", "wet"), item_type="multiple_choice", misconception="context_clue"),
            _det("empty", "The empty box had nothing inside.", "What does empty mean here?", "having nothing inside", options=("having nothing inside", "full of toys", "moving fast"), item_type="multiple_choice", misconception="context_clue"),
            _det("delighted", "Pooja was delighted; she smiled all day after winning the art prize.", "What does delighted mean?", "very happy", options=("very happy", "very tired", "very worried", "very quiet"), item_type="multiple_choice", misconception="context_clue"),
            _det("sturdy", "The sturdy chair did not shake even when two bags were placed on it.", "What does sturdy mean?", "strong", options=("strong", "colourful", "small", "expensive"), item_type="multiple_choice", misconception="context_clue"),
        )),
        _track(3, "word_roles", "grammar", "grammar.noun_verb_adjective", "Recognize a word's job in a sentence", 3, (
            _det("flower", "The red flower opened.", "Which word names a thing?", "flower", options=("flower", "red", "opened"), item_type="multiple_choice", misconception="word_role"),
            _det("teacher", "The teacher wrote neatly.", "Which word names a person?", "teacher", options=("teacher", "wrote", "neatly"), item_type="multiple_choice", misconception="word_role"),
            _det("soft", "Maya held the soft blanket.", "Which word describes the blanket?", "soft", options=("soft", "held", "Maya"), item_type="multiple_choice", misconception="word_role"),
            _det("rushed", "The excited children rushed into the playground.", "Which word shows an action?", "rushed", options=("rushed", "excited", "children", "playground"), item_type="multiple_choice", misconception="word_role"),
            _det("ancient", "We visited an ancient fort on Sunday.", "Which word describes the fort?", "ancient", options=("ancient", "visited", "Sunday", "we"), item_type="multiple_choice", misconception="word_role"),
        )),
        _track(3, "past_tense", "grammar", "grammar.tense_usage", "Recognize and use past tense", 3, (
            _det("played", "Yesterday, the children played in the park.", "Which word shows a past action?", "played", options=("played", "children", "park"), item_type="multiple_choice", misconception="past_tense"),
            _det("went", "Today I go to school. Yesterday I went to school.", "Which word shows the past action?", "went", options=("went", "today", "school"), item_type="multiple_choice", misconception="past_tense"),
            _det("washed", "This morning, Amir washed his bicycle.", "Which word is in the past tense?", "washed", options=("washed", "bicycle", "morning"), item_type="multiple_choice", misconception="past_tense"),
            _det("found", "Last week, the class found a bird's nest near the field.", "Which word tells what happened in the past?", "found", options=("found", "class", "nest", "near"), item_type="multiple_choice", misconception="past_tense"),
            _det("brought", "Renu brings lunch today. Yesterday, she brought fruit.", "Which word is the past form of bring?", "brought", options=("brought", "brings", "fruit", "today"), item_type="multiple_choice", misconception="past_tense"),
        )),
        _track(3, "complete_sentence", "writing", "writing.complete_sentence", "Complete a meaningful sentence", 3, (
            _open("bird", "A bird rests on a branch and watches the garden below.", "Write one complete English sentence about the bird.", "school.strict.complete_sentence.class3.v1", misconception="complete_sentence"),
            _open("dog", "A dog runs across the field after a red ball.", "Write one complete English sentence about the dog.", "school.strict.complete_sentence.class2.v1", misconception="complete_sentence"),
            _open("baby", "The baby's eyes are closed while the room stays quiet.", "Write one complete English sentence about the baby.", "school.strict.complete_sentence.class2.v1", misconception="complete_sentence"),
            _open("market", "The market became busy after sunrise.", "Write one complete English sentence about the market.", "school.strict.complete_sentence.class3.v1", misconception="complete_sentence"),
            _open("team", "Four children worked together to move a table.", "Write one complete English sentence about the team.", "school.strict.complete_sentence.class3.v1", misconception="complete_sentence"),
        )),
        _track(3, "short_answer", "writing", "writing.short_answer", "Answer clearly in one or two sentences", 3, (
            _open("shade", "The children moved under a tree when the afternoon sun became hot.", "Where did the children go, and why?", "school.strict.short_answer.v1", misconception="short_answer"),
            _open("lost_pencil", "Isha found Ravi's pencil near her desk and returned it to him.", "What did Isha do?", "school.strict.short_answer.v1", misconception="short_answer"),
            _open("rain_game", "Rain began during the match, so the players covered the equipment.", "What happened during the match?", "school.strict.short_answer.v1", misconception="short_answer"),
            _open("seedlings", "The seedlings bent in the wind. The gardener tied each one to a thin stick.", "How did the gardener help the seedlings?", "school.strict.short_answer.v1", misconception="short_answer"),
            _open("missing_bus", "Aarav reached the stop after the bus had left. He called his uncle for help.", "What problem did Aarav face, and what did he do?", "school.strict.short_answer.v1", misconception="short_answer"),
        )),
    )


def _class_4_tracks() -> tuple[PlacementTrack, ...]:
    return (
        _track(4, "sentence_detail", "reading", "reading.sentence_comprehension", "Find connected details in a passage", 3, (
            _det("medal", "Tara placed her silver medal inside a wooden box.", "What did Tara place in the box?", "her silver medal", "silver medal", "medal"),
            _det("parcel", "The guard left a parcel with Meena's neighbour at noon.", "Who received the parcel?", "Meena's neighbour", "the neighbour", "neighbour"),
            _det("notebook", "After science class, Dev returned the green notebook to the second shelf.", "Which notebook did Dev return?", "the green notebook", "green notebook"),
            _det("meeting", "The eco-club meeting moved from Tuesday to Thursday because the hall was busy.", "On which day will the meeting happen?", "Thursday"),
            _det("route", "Bus 12 stops at the museum before it reaches the railway station.", "Which place does Bus 12 reach first?", "the museum", "museum"),
        )),
        _track(4, "main_idea", "reading", "reading.paragraph_main_idea", "Identify the central idea", 3, (
            _det("clean_corner", "Asha sorted books, Imran wiped tables, and Tara made labels. Together they cleaned the reading corner.", "What is the passage mostly about?", "children working together", options=("children working together", "a missing label", "a sports day"), item_type="multiple_choice", misconception="main_idea"),
            _det("water_saving", "The tap leaked all night. Students reported it and placed a bucket below it until it was repaired.", "What is the main idea?", "students preventing water waste", options=("students preventing water waste", "students washing a bucket", "students closing a classroom"), item_type="multiple_choice", misconception="main_idea"),
            _det("lost_puppy", "Several neighbours checked lanes and gardens. By evening, they found the lost puppy near the bakery.", "What is the passage mostly about?", "neighbours finding a lost puppy", options=("neighbours finding a lost puppy", "a bakery selling bread", "a garden contest"), item_type="multiple_choice", misconception="main_idea"),
            _det("reading_drive", "Older students collected storybooks, repaired torn covers, and opened a reading shelf for younger children.", "What is the central idea?", "students creating a reading shelf", options=("students creating a reading shelf", "students writing an exam", "students planting trees", "students learning a dance"), item_type="multiple_choice", misconception="main_idea"),
            _det("safe_crossing", "Residents painted a zebra crossing and asked drivers to slow down near the school gate.", "What is the passage mainly about?", "making the school crossing safer", options=("making the school crossing safer", "decorating the school gate", "repairing a classroom", "planning a holiday"), item_type="multiple_choice", misconception="main_idea"),
        )),
        _track(4, "reason_inference", "reading", "reading.inference_reason", "Explain a reason using evidence", 3, (
            _open("baton", "Nitin dropped the baton. Reva picked it up and passed it back so the relay could continue.", "Why was Reva's action helpful?", "school.strict.reason_from_text.v1", misconception="reason_evidence"),
            _open("wet_floor", "A sign was placed beside the wet floor before visitors entered.", "Why was the sign placed there?", "school.strict.reason_from_text.v1", misconception="reason_evidence"),
            _open("shade", "The sapling's leaves were drying, so Omar moved it away from the harsh afternoon sun.", "Why did Omar move the sapling?", "school.strict.reason_from_text.v1", misconception="reason_evidence"),
            _open("practice", "Lata practised the difficult tune slowly each day. At the concert, she played it without stopping.", "How did daily practice help Lata?", "school.strict.reason_from_text.v1", misconception="reason_evidence"),
            _open("bridge", "The old footbridge was closed after cracks appeared in two wooden boards.", "Why was the footbridge closed?", "school.strict.reason_from_text.v1", misconception="reason_evidence"),
        )),
        _track(4, "context_word", "vocabulary", "reading.word_meaning_context", "Infer word meaning from context", 3, (
            _det("bond", "The teammates trusted one another. Their bond grew after every shared task.", "What does bond mean here?", "a close connection", options=("a close connection", "a loud sound", "a long delay"), item_type="multiple_choice", misconception="context_clue"),
            _det("fragile", "Handle the fragile cup gently because it can break easily.", "What does fragile mean?", "easy to break", options=("easy to break", "hard to carry", "safe to drop"), item_type="multiple_choice", misconception="context_clue"),
            _det("generous", "Rohan was generous and shared his lunch with two classmates.", "What does generous mean here?", "willing to share", options=("willing to share", "ready to sleep", "afraid to speak"), item_type="multiple_choice", misconception="context_clue"),
            _det("reluctant", "Navi stood at the edge of the stage and hesitated. She was reluctant to step forward.", "What does reluctant mean?", "not willing or unsure", options=("not willing or unsure", "eager to begin", "unable to hear", "ready to laugh"), item_type="multiple_choice", misconception="context_clue"),
            _det("vanished", "The puddle vanished after hours of bright sunshine; no water remained.", "What does vanished mean here?", "disappeared", options=("disappeared", "grew deeper", "became dirty", "froze solid"), item_type="multiple_choice", misconception="context_clue"),
        )),
        _track(4, "connectors", "grammar", "grammar.connectors_because_and_but", "Use connectors to show reason or contrast", 4, (
            _det("but", "Leena wanted to lead the song, ___ she let Arjun go first because he had practised the opening.", "Which connector best shows the contrast?", "but", options=("but", "because", "so"), item_type="multiple_choice", misconception="connector"),
            _det("because", "We moved indoors ___ it began to rain.", "Which connector introduces the reason?", "because", options=("because", "but", "and"), item_type="multiple_choice", misconception="connector"),
            _det("and", "Mira packed her notebook ___ her pencils.", "Which connector adds another item?", "and", options=("and", "because", "but"), item_type="multiple_choice", misconception="connector"),
            _det("contrast", "The path was steep, ___ the hikers continued carefully.", "Which connector best shows contrast?", "but", options=("but", "because", "so", "and"), item_type="multiple_choice", misconception="connector"),
            _det("reason", "The team checked the map ___ they did not want to take the wrong road.", "Which connector introduces the reason?", "because", options=("because", "but", "and", "or"), item_type="multiple_choice", misconception="connector"),
        )),
        _track(4, "tense", "grammar", "grammar.tense_usage", "Choose a tense that matches time", 4, (
            _det("visited", "Last Sunday, we ___ the fort.", "Which word fits?", "visited", options=("visited", "visit", "will visit"), item_type="multiple_choice", misconception="tense_time"),
            _det("is_reading", "Right now, Sona ___ a story.", "Which words fit?", "is reading", options=("is reading", "read yesterday", "will read tomorrow"), item_type="multiple_choice", misconception="tense_time"),
            _det("will_clean", "Tomorrow, the class ___ the garden.", "Which words fit?", "will clean", options=("will clean", "cleaned", "is cleaning yesterday"), item_type="multiple_choice", misconception="tense_time"),
            _det("had_finished", "By the time the bell rang, Arif ___ his drawing.", "Which words correctly show the earlier action?", "had finished", options=("had finished", "finishes", "will finish", "is finish"), item_type="multiple_choice", misconception="tense_time"),
            _det("has_lived", "Nina ___ in this town for four years and still lives here.", "Which words fit the time clue?", "has lived", options=("has lived", "lived tomorrow", "will lived", "is live"), item_type="multiple_choice", misconception="tense_time"),
        )),
        _track(4, "summary", "writing", "writing.summary_own_words", "Summarize a short passage in your own words", 4, (
            _open("seed", "A seed split after rain reached the soil. A small root grew downward and a shoot moved toward the light.", "Summarize what happened to the seed in one English sentence.", "school.strict.summary.v1", misconception="summary"),
            _open("lost_wallet", "Maya found a wallet near the gate. She gave it to the office, and its owner collected it later.", "Summarize the event in one English sentence.", "school.strict.summary.v1", misconception="summary"),
            _open("power_cut", "The lights went out during rehearsal. Students opened the curtains and continued practising in daylight.", "Summarize what the students did.", "school.strict.summary.v1", misconception="summary"),
            _open("pond", "Residents removed plastic from the pond, planted reeds near the bank, and put up signs asking visitors not to litter.", "Summarize how residents cared for the pond.", "school.strict.summary.v1", misconception="summary"),
            _open("science_model", "A model bridge collapsed twice. The group widened its base, tested it again, and finally held the weights.", "Summarize how the group improved the bridge.", "school.strict.summary.v1", misconception="summary"),
        )),
        _track(4, "reason_answer", "writing", "writing.reason_answer", "Write an answer supported by a reason", 4, (
            _open("fair_turn", "Two children want the same football. The coach asks them to decide fairly.", "What should they do? Give one reason.", "school.strict.reason_answer.v1", misconception="reason_answer"),
            _open("water_bottle", "A walk will last two hours on a warm day.", "Should Ritu carry water? Give one reason.", "school.strict.reason_answer.v1", misconception="reason_answer"),
            _open("quiet_zone", "Several students are reading for a test in the library.", "Should a group play music there? Give one reason.", "school.strict.reason_answer.v1", misconception="reason_answer"),
            _open("tree_choice", "The playground has little shade and becomes very hot by noon.", "Should the school plant trees there? Support your answer.", "school.strict.reason_answer.v1", misconception="reason_answer"),
            _open("repair_reuse", "A backpack has one broken zip but the cloth is still strong.", "Is repairing it a good choice? Explain your reason.", "school.strict.reason_answer.v1", misconception="reason_answer"),
        )),
    )


def _class_5_tracks() -> tuple[PlacementTrack, ...]:
    return (
        _track(5, "sentence_detail", "reading", "reading.sentence_comprehension", "Combine details from a passage", 4, (
            _det("train", "The morning train to Jaipur leaves platform three at 7:20.", "Which platform does the Jaipur train leave from?", "platform three", "platform 3", "three", "3"),
            _det("permission", "Rohit may use the lab only after his teacher signs the blue form.", "What must happen before Rohit uses the lab?", "his teacher signs the blue form", "the teacher must sign the form"),
            _det("delivery", "The parcel reached the office on Monday but was collected by Zoya on Tuesday.", "When did Zoya collect the parcel?", "Tuesday"),
            _det("museum", "The museum opens at ten, but the guided tour begins thirty minutes later near the main staircase.", "What time does the guided tour begin?", "10:30", "ten thirty", "10.30"),
            _det("competition", "Entries must be emailed by Friday, while printed posters may be delivered on Monday morning.", "What must be sent by Friday?", "entries", "the entries", "emailed entries"),
        )),
        _track(5, "main_idea", "reading", "reading.paragraph_main_idea", "Distinguish a central idea from details", 4, (
            _det("community_kitchen", "Families donated rice, shopkeepers lent large pots, and volunteers cooked meals after the flood.", "What is the main idea?", "the community worked together to provide meals", options=("the community worked together to provide meals", "shopkeepers sold new pots", "families moved to another town"), item_type="multiple_choice", misconception="main_idea"),
            _det("roof_garden", "Students measured sunlight, chose suitable plants, and reused bottles as planters on the school roof.", "What is the passage mainly about?", "students creating a roof garden", options=("students creating a roof garden", "students measuring a classroom", "students buying plastic bottles"), item_type="multiple_choice", misconception="main_idea"),
            _det("oral_history", "Children interviewed grandparents, recorded old neighbourhood stories, and displayed them with photographs.", "What is the central idea?", "children preserving local memories", options=("children preserving local memories", "children learning photography only", "grandparents moving houses"), item_type="multiple_choice", misconception="main_idea"),
            _det("lake_restore", "For months, citizens tested the lake water, stopped waste pipes, and planted native grasses along the shore.", "What is the passage mainly about?", "a community restoring a lake", options=("a community restoring a lake", "citizens building a swimming pool", "a town preparing for a fair", "workers widening a road"), item_type="multiple_choice", misconception="main_idea"),
            _det("book_exchange", "Instead of buying every new title, families brought books they had finished and exchanged them for others.", "What is the central idea?", "families sharing books through an exchange", options=("families sharing books through an exchange", "families opening a bookshop", "children writing textbooks", "people repairing a library roof"), item_type="multiple_choice", misconception="main_idea"),
        )),
        _track(5, "inference", "reading", "reading.inference_reason", "Infer an unstated reason from evidence", 4, (
            _open("wet_shoes", "The sky was clear when Ira left. She returned with wet shoes and a closed umbrella dripping by the door.", "What probably happened while Ira was outside? Use one clue.", "school.strict.inference.v1", misconception="inference"),
            _open("empty_plate", "Only crumbs remained on the plate, and the puppy licked its lips under the table.", "What probably happened to the food? Use a clue.", "school.strict.inference.v1", misconception="inference"),
            _open("dark_house", "Newspapers had collected at the door, and no lights had appeared for several evenings.", "What can you infer about the people who live there?", "school.strict.inference.v1", misconception="inference"),
            _open("quiet_team", "The scoreboard showed one run needed. Every player leaned forward and stopped talking as the bowler began.", "Why did the team become quiet? Use evidence.", "school.strict.inference.v1", misconception="inference"),
            _open("wilted_plants", "The balcony plants drooped, the soil was dry, and the watering can had been empty for days.", "What most likely caused the plants to droop? Explain with a clue.", "school.strict.inference.v1", misconception="inference"),
        )),
        _track(5, "context_word", "vocabulary", "reading.word_meaning_context", "Infer precise meaning from context", 4, (
            _det("glanced", "Ravi glanced at the clock, then quickly returned to his book.", "What does glanced mean?", "looked quickly", options=("looked quickly", "slept deeply", "spoke loudly"), item_type="multiple_choice", misconception="context_clue"),
            _det("scarce", "Water became scarce; each family received only one bucket.", "What does scarce mean here?", "not enough", options=("not enough", "very clean", "easy to carry"), item_type="multiple_choice", misconception="context_clue"),
            _det("resolved", "After discussing both plans, the group resolved the disagreement and chose one route.", "What does resolved mean?", "settled", options=("settled", "started", "ignored"), item_type="multiple_choice", misconception="context_clue"),
            _det("meticulous", "Anaya checked every measurement twice and corrected even tiny errors. Her work was meticulous.", "What does meticulous mean?", "very careful and exact", options=("very careful and exact", "done in a hurry", "brightly coloured", "hard to explain"), item_type="multiple_choice", misconception="context_clue"),
            _det("deteriorated", "Without repairs, the path deteriorated: cracks widened and stones came loose.", "What does deteriorated mean?", "became worse", options=("became worse", "became shorter", "was painted", "was discovered"), item_type="multiple_choice", misconception="context_clue"),
        )),
        _track(5, "word_usage", "vocabulary", "vocab.chapter_word_usage", "Choose precise vocabulary for a context", 5, (
            _det("inspect", "Before using the rope, the climber will ___ it for damage.", "Which word fits best?", "inspect", options=("inspect", "scatter", "borrow", "whisper"), item_type="multiple_choice", misconception="precise_word"),
            _det("conserve", "Turning off unused lights helps us ___ electricity.", "Which word fits best?", "conserve", options=("conserve", "divide", "announce", "decorate"), item_type="multiple_choice", misconception="precise_word"),
            _det("persuade", "The team used facts to ___ the council to add a crossing.", "Which word fits best?", "persuade", options=("persuade", "measure", "replace", "observe"), item_type="multiple_choice", misconception="precise_word"),
            _det("allocate", "The captain must ___ equal practice time to every player.", "Which word most precisely fits?", "allocate", options=("allocate", "scatter", "predict", "remove"), item_type="multiple_choice", misconception="precise_word"),
            _det("verify", "Before publishing the result, the class should ___ the numbers against the original table.", "Which word most precisely fits?", "verify", options=("verify", "imagine", "erase", "celebrate"), item_type="multiple_choice", misconception="precise_word"),
        )),
        _track(5, "tense", "grammar", "grammar.tense_usage", "Maintain consistent tense", 5, (
            _det("arrived", "The guests ___ before the music began.", "Which word fits?", "arrived", options=("arrived", "arrive tomorrow", "arrives now"), item_type="multiple_choice", misconception="tense_consistency"),
            _det("will_present", "Next Friday, our group ___ the model.", "Which words fit?", "will present", options=("will present", "presented yesterday", "is present last week"), item_type="multiple_choice", misconception="tense_consistency"),
            _det("has_finished", "Meera ___ her homework, so she can play now.", "Which words fit?", "has finished", options=("has finished", "finish tomorrow", "finishing yesterday"), item_type="multiple_choice", misconception="tense_consistency"),
            _det("had_left", "By the time we reached the station, the train ___.", "Which words correctly show the earlier action?", "had left", options=("had left", "leaves tomorrow", "is leaving yesterday", "will left"), item_type="multiple_choice", misconception="tense_consistency"),
            _det("has_been_working", "Salim ___ on the model since Monday and is still improving it.", "Which words best match the time clue?", "has been working", options=("has been working", "worked tomorrow", "will working", "had work now"), item_type="multiple_choice", misconception="tense_consistency"),
        )),
        _track(5, "sentence_order", "grammar", "grammar.sentence_order", "Arrange clauses into a clear sentence", 5, (
            _det("rain", "Parts: because it rained / indoors / we stayed", "Arrange the parts into one sentence.", "we stayed indoors because it rained", "We stayed indoors because it rained"),
            _det("library", "Parts: after lunch / the library / opens", "Arrange the parts into one sentence.", "the library opens after lunch", "The library opens after lunch"),
            _det("practice", "Parts: improved / she practised daily / because / her serve", "Arrange the parts into one sentence.", "her serve improved because she practised daily", "Her serve improved because she practised daily"),
            _det("experiment", "Parts: the result / although the first trial failed / the team repeated / to verify", "Arrange the parts into a clear sentence.", "although the first trial failed, the team repeated it to verify the result", "Although the first trial failed, the team repeated it to verify the result"),
            _det("meeting", "Parts: before the meeting ended / who would present / the group decided / each section", "Arrange the parts into a clear sentence.", "before the meeting ended, the group decided who would present each section", "Before the meeting ended, the group decided who would present each section"),
        )),
        _track(5, "summary", "writing", "writing.summary_own_words", "Summarize without copying", 5, (
            _open("storm", "A storm broke two branches and blocked the lane. Residents cut the branches into smaller pieces and cleared a path.", "Summarize the problem and response in one or two English sentences.", "school.strict.summary.v1", misconception="summary"),
            _open("solar", "The school compared electricity bills, installed solar panels, and used the savings to buy library books.", "Summarize the sequence in your own words.", "school.strict.summary.v1", misconception="summary"),
            _open("injured_bird", "Children found an injured bird, called a rescue centre, and kept the area quiet until help arrived.", "Summarize what the children did.", "school.strict.summary.v1", misconception="summary"),
            _open("bus_project", "Students mapped unsafe bus stops, interviewed commuters, and submitted three practical changes to the transport office.", "Summarize the project and its outcome in your own words.", "school.strict.summary.v1", misconception="summary"),
            _open("water_test", "Two water samples looked equally clear, but a test showed that one contained harmful bacteria and needed treatment.", "Summarize the key finding without copying the sentence.", "school.strict.summary.v1", misconception="summary"),
        )),
    )


def _assign_opaque_item_ids(
    class_no: int,
    tracks: tuple[PlacementTrack, ...],
) -> tuple[PlacementTrack, ...]:
    opaque_tracks: list[PlacementTrack] = []
    for track_index, track in enumerate(tracks, start=1):
        variant_index = 1
        snapshot_item = replace(
            track.snapshot_item,
            item_id=f"spv_c{class_no:02d}_t{track_index:02d}_v{variant_index:02d}",
        )
        opaque_bands: list[PlacementBand] = []
        for band in track.bands:
            opaque_variants: list[SchoolPlacementBankItem] = []
            for item in band.variants:
                variant_index += 1
                opaque_variants.append(
                    replace(
                        item,
                        item_id=(
                            f"spv_c{class_no:02d}_t{track_index:02d}_v{variant_index:02d}"
                        ),
                    )
                )
            opaque_bands.append(
                replace(band, variants=tuple(opaque_variants))
            )
        opaque_tracks.append(
            replace(
                track,
                snapshot_item=snapshot_item,
                bands=tuple(opaque_bands),
            )
        )
    return tuple(opaque_tracks)


PLACEMENT_TRACKS_BY_CLASS: Mapping[int, tuple[PlacementTrack, ...]] = MappingProxyType({
    2: _assign_opaque_item_ids(2, _class_2_tracks()),
    3: _assign_opaque_item_ids(3, _class_3_tracks()),
    4: _assign_opaque_item_ids(4, _class_4_tracks()),
    5: _assign_opaque_item_ids(5, _class_5_tracks()),
})


def placement_tracks_for(subject_id: str, target_class_no: int) -> tuple[PlacementTrack, ...]:
    if subject_id != "english":
        return ()
    return PLACEMENT_TRACKS_BY_CLASS.get(int(target_class_no), ())


def _flatten_class(class_no: int) -> tuple[SchoolPlacementBankItem, ...]:
    tracks = PLACEMENT_TRACKS_BY_CLASS[class_no]
    snapshots = tuple(track.snapshot_item for track in tracks)
    targeted = tuple(
        item
        for track in tracks
        for band in track.bands
        for item in band.variants
        if item.stage == "targeted_diagnostic"
    )
    confirmatory = tuple(
        item
        for track in tracks
        for band in track.bands
        for item in band.variants
        if item.stage == "confirmatory"
    )
    return snapshots + targeted + confirmatory


PLACEMENT_BANK_BY_CLASS: Mapping[
    int,
    tuple[SchoolPlacementBankItem, ...],
] = MappingProxyType({class_no: _flatten_class(class_no) for class_no in range(2, 6)})

CLASS_2_PLACEMENT_BANK = PLACEMENT_BANK_BY_CLASS[2]
CLASS_3_PLACEMENT_BANK = PLACEMENT_BANK_BY_CLASS[3]
CLASS_4_PLACEMENT_BANK = PLACEMENT_BANK_BY_CLASS[4]
CLASS_5_PLACEMENT_BANK = PLACEMENT_BANK_BY_CLASS[5]


SIGNAL_SKILL_PRIORITY: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "reading": (
        "reading.sentence_comprehension",
        "reading.word_meaning_context",
        "reading.paragraph_main_idea",
        "reading.inference_reason",
    ),
    "vocabulary": ("reading.word_meaning_context", "vocab.chapter_word_usage"),
    "grammar": (
        "grammar.noun_verb_adjective",
        "grammar.sentence_order",
        "grammar.connectors_because_and_but",
        "grammar.tense_usage",
    ),
    "writing": (
        "writing.complete_sentence",
        "writing.short_answer",
        "writing.reason_answer",
        "writing.summary_own_words",
    ),
    "chapter_answers": (
        "reading.inference_reason",
        "writing.short_answer",
        "reading.paragraph_main_idea",
    ),
})


def placement_bank_for(subject_id: str, target_class_no: int) -> tuple[SchoolPlacementBankItem, ...]:
    if subject_id != "english":
        return ()
    class_no = int(target_class_no)
    return PLACEMENT_BANK_BY_CLASS.get(class_no, ())


def public_placement_item(item: SchoolPlacementBankItem, language: str = "en") -> dict:
    learner_copy = item.localized_copy.get(language, item.localized_copy["en"])
    return {
        "item_id": item.item_id,
        "stage": item.stage,
        "type": item.item_type,
        "source_class_no": item.source_class_no,
        "target_class_no": item.target_class_no,
        "learner_skill_label": item.learner_skill_label,
        "instruction": learner_copy.instruction,
        "support": learner_copy.support,
        "prompt": item.prompt,
        "passage": item.passage,
        "options": list(item.options) if item.options else None,
    }


PLACEMENT_BANK_VALIDATED = validate_placement_bank(PLACEMENT_TRACKS_BY_CLASS)
