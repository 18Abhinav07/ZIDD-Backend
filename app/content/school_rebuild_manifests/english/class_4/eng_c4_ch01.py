"""Original deep manifest and scoped authoring helpers for Class 4 English.

The official extract is used only to map chapter themes, section order, and
exercise forms. Every learner-facing passage, prompt, option, response model,
and rubric in this module is original Zidd content.
"""

from __future__ import annotations

import re
from typing import Any


_ALIAS_REWRITES = (
    ("coordinated effort", "team effort"),
    ("shared goal", "common aim"),
    ("finds", "locates"),
    ("address card", "address clue"),
    ("office calls", "office rings"),
    ("reach the owner", "contact the owner"),
    ("pause at", "stop beside"),
    ("entering from the road", "coming from the street"),
    ("reversing from the gate", "backing out through the gate"),
    ("sustained attention", "steady focus"),
    ("switching leaves tasks unfinished", "jumping leaves work incomplete"),
    ("consume all", "take every"),
    ("share-first routine", "giving fruit before eating"),
    ("speech output", "spoken directions"),
    ("hard to locate", "cannot find"),
    ("raised marker", "touch marker"),
    ("retests", "tries again"),
    ("checking Kamal's well being", "reviewing whether Kamal is well"),
    ("three item checklist", "final packet checklist"),
    ("studied every runner's times", "reviewed all runners' practice times"),
    ("Yes it is available", "the clerk confirms availability"),
    ("footpath side door", "door beside the footpath"),
    ("compare each jar's contents", "check what every jar holds"),
    ("bring water", "provide drinking water"),
    ("nervously describes the fawn's crossing action", "anxious plank crossing"),
    ("gracefully describes the crane's controlled landing", "smooth controlled landing"),
    ("because", "since"),
    ("shows", "demonstrates"),
    ("reveals", "uncovers"),
    ("helps", "supports"),
    ("first", "at first"),
    ("then", "after that"),
    ("finally", "at the end"),
    ("rather than", "instead of"),
    ("despite", "even though"),
    ("leans against", "is supported by"),
    ("hands it over", "gives it to staff"),
    ("did not buy", "never purchased"),
)
_WORD_ALIAS_REWRITES = (
    ("synchronized", "coordinated"),
    ("oars", "rowing tools"),
    ("organized", "well planned"),
    ("teamwork", "cooperation"),
    ("single", "lone"),
    ("one", "a single"),
    ("two", "both"),
    ("second", "following"),
    ("three", "3"),
    ("third", "final of three"),
    ("four", "4"),
    ("five", "5"),
    ("six", "6"),
    ("each", "every"),
    ("every", "each"),
    ("all", "every"),
    ("both", "the two"),
    ("another", "one more"),
    ("different", "distinct"),
    ("small", "little"),
    ("little", "a small amount"),
    ("weak", "faint"),
    ("separate", "individual"),
    ("same", "matching"),
    ("shared", "used together"),
    ("clear", "easy to understand"),
    ("easy", "simple"),
    ("specific", "exact"),
    ("specialized", "suited to different skills"),
    ("correct", "right"),
    ("incorrect", "wrong"),
    ("next", "following"),
    ("last", "final"),
    ("earlier", "previous"),
    ("later", "future"),
    ("current", "present"),
    ("only", "just"),
    ("without", "with no"),
    ("before", "prior to"),
    ("after", "following"),
    ("beyond", "past"),
    ("while", "during the time that"),
    ("because", "since"),
    ("could", "might be able to"),
    ("may", "might"),
    ("will", "is going to"),
    ("can", "is able to"),
    ("values", "respects"),
    ("value", "importance"),
    ("identifies", "recognizes"),
    ("identify", "recognize"),
    ("identified", "recognized"),
    ("represent", "stand for"),
    ("represents", "stands for"),
    ("symbolizes", "stands for"),
    ("seems", "appears"),
    ("creates", "makes"),
    ("create", "make"),
    ("gives", "provides"),
    ("give", "provide"),
    ("provides", "supplies"),
    ("provide", "supply"),
    ("uses", "applies"),
    ("use", "apply"),
    ("shows", "demonstrates"),
    ("show", "demonstrate"),
    ("states", "says"),
    ("includes", "contains"),
    ("include", "contain"),
    ("explains", "tells why"),
    ("explain", "tell why"),
    ("describes", "tells how"),
    ("describe", "tell how"),
    ("means", "refers to"),
    ("helps", "supports"),
    ("help", "support"),
    ("supports", "strengthens"),
    ("support", "strengthen"),
    ("supported", "helped"),
    ("protects", "keeps safe"),
    ("protect", "keep safe"),
    ("prevents", "stops"),
    ("prevent", "stop"),
    ("allows", "lets"),
    ("allowed", "made possible"),
    ("accepted", "agreed to"),
    ("chooses", "selects"),
    ("prioritizes", "puts first"),
    ("choose", "select"),
    ("compares", "checks against"),
    ("compare", "check against"),
    ("checks", "verifies"),
    ("count", "total"),
    ("check", "verify"),
    ("checking", "reviewing"),
    ("tested", "tried"),
    ("tests", "tries"),
    ("test", "try"),
    ("moves", "shifts"),
    ("drops", "falls"),
    ("falls", "drops"),
    ("loosens", "breaks up"),
    ("stands", "is placed"),
    ("lies", "rests"),
    ("hangs", "is suspended"),
    ("move", "shift"),
    ("moving", "shifting"),
    ("switching", "changing"),
    ("changes", "adjusts"),
    ("delays", "postpones"),
    ("change", "adjust"),
    ("changed", "adjusted"),
    ("repairs", "fixes"),
    ("repair", "fix"),
    ("returns", "brings back"),
    ("returned", "brought back"),
    ("shares", "gives a share of"),
    ("share", "give a share of"),
    ("takes", "uses"),
    ("take", "use"),
    ("keeps", "maintains"),
    ("keep", "maintain"),
    ("adds", "puts in"),
    ("add", "put in"),
    ("starts", "begins"),
    ("blows", "sends air"),
    ("travels", "moves"),
    ("rises", "increases"),
    ("risks", "may suffer"),
    ("start", "begin"),
    ("begins", "starts"),
    ("becomes", "turns"),
    ("begin", "start"),
    ("finishes", "completes"),
    ("finish", "complete"),
    ("completes", "finishes"),
    ("complete", "finish"),
    ("completed", "finished"),
    ("displayed", "posted"),
    ("corrected", "fixed"),
    ("filled", "made full"),
    ("fits", "attaches"),
    ("fills", "makes full"),
    ("collaborated", "worked together"),
    ("reconciled", "settled their differences"),
    ("monitors", "student helpers"),
    ("arranged", "ordered"),
    ("arranges", "orders"),
    ("assign", "give"),
    ("sorting", "organizing"),
    ("spread", "laid out"),
    ("separated", "sorted apart"),
    ("combining", "joining"),
    ("sort", "organize"),
    ("gathered", "collected"),
    ("guided", "led"),
    ("gathers", "collects"),
    ("built", "made"),
    ("builds", "makes"),
    ("bring", "carry"),
    ("brought", "carried"),
    ("tie", "fasten"),
    ("replace", "swap"),
    ("refill", "fill again"),
    ("wait", "remain until"),
    ("waiting", "remaining until"),
    ("reads", "studies"),
    ("reading", "studying"),
    ("research", "study"),
    ("writes", "records"),
    ("printed", "written"),
    ("write", "record"),
    ("records", "logs"),
    ("marks", "records"),
    ("record", "log"),
    ("said", "stated"),
    ("asked", "questioned"),
    ("blaming", "placing fault on"),
    ("replied", "answered"),
    ("answer", "response"),
    ("notice", "see"),
    ("noticed", "saw"),
    ("find", "locate"),
    ("found", "located"),
    ("needs", "requires"),
    ("need", "requirement"),
    ("needed", "required"),
    ("matters", "is important"),
    ("important", "significant"),
    ("success", "achievement"),
    ("advantage", "benefit"),
    ("practical", "usable"),
    ("personal", "individual"),
    ("preference", "choice"),
    ("adjustment", "change"),
    ("safe", "secure"),
    ("safety", "security"),
    ("strong", "powerful"),
    ("defence", "protection"),
    ("safely", "securely"),
    ("gently", "with care"),
    ("fair", "just"),
    ("scarce", "limited"),
    ("fairness", "just treatment"),
    ("honest", "truthful"),
    ("unearned", "not deserved"),
    ("responsibility", "duty"),
    ("responsible", "dependable"),
    ("reliable", "dependable"),
    ("trust", "confidence"),
    ("confidence", "belief"),
    ("effort", "work"),
    ("work", "effort"),
    ("task", "job"),
    ("tasks", "jobs"),
    ("job", "task"),
    ("roles", "jobs"),
    ("group", "team"),
    ("team", "group"),
    ("members", "people in the group"),
    ("people", "community members"),
    ("learner", "pupil"),
    ("learners", "pupils"),
    ("student", "pupil"),
    ("students", "pupils"),
    ("user", "person using it"),
    ("users", "people using it"),
    ("reader", "person reading"),
    ("readers", "people reading"),
    ("visitor", "guest"),
    ("visitors", "guests"),
    ("friend", "classmate"),
    ("owner", "person it belongs to"),
    ("supplier", "seller"),
    ("friends", "classmates"),
    ("partner", "teammate"),
    ("helpers", "assistants"),
    ("actors", "performers"),
    ("players", "team members"),
    ("teacher", "class teacher"),
    ("nurse", "health worker"),
    ("labels", "names"),
    ("labelled", "named"),
    ("cards", "card pieces"),
    ("bracelet", "wrist band"),
    ("bell", "chime"),
    ("label", "name marker"),
    ("signs", "notices"),
    ("sign", "notice"),
    ("marker", "guide mark"),
    ("markers", "guide marks"),
    ("path", "route"),
    ("paths", "routes"),
    ("road", "street"),
    ("footpath", "walking path"),
    ("vehicle", "road vehicle"),
    ("vehicles", "road vehicles"),
    ("car", "motor car"),
    ("door", "entrance"),
    ("room", "space"),
    ("spaces", "sections"),
    ("counter", "worktop"),
    ("cable", "wire"),
    ("coil", "loop"),
    ("beneath", "under"),
    ("above", "over"),
    ("station", "work area"),
    ("sports", "games"),
    ("water", "drinking water"),
    ("food", "meal supply"),
    ("grass", "meadow plants"),
    ("soil", "earth"),
    ("materials", "supplies"),
    ("supplies", "materials"),
    ("bags", "sacks"),
    ("material", "supply"),
    ("tool", "piece of equipment"),
    ("tools", "equipment"),
    ("plan", "method"),
    ("designs", "plans"),
    ("rule", "agreed direction"),
    ("problem", "difficulty"),
    ("barrier", "blocked access"),
    ("solution", "answer to the problem"),
    ("result", "outcome"),
    ("reason", "cause"),
    ("evidence", "proof"),
    ("idea", "main thought"),
    ("message", "note"),
    ("request", "ask"),
    ("procedure", "ordered method"),
    ("sequence", "event order"),
    ("routine", "usual pattern"),
    ("decoration", "finishing touches"),
    ("practice", "rehearsal"),
    ("speed", "quickness"),
    ("access", "ability to use it"),
    ("independently", "without required help"),
    ("tactile", "readable by touch"),
    ("raised", "standing above the surface"),
    ("text", "written words"),
    ("information", "details"),
    ("same", "matching"),
    ("Monday", "on Monday"),
    ("Tuesday", "on Tuesday"),
    ("Wednesday", "on Wednesday"),
    ("Thursday", "on Thursday"),
    ("Friday", "on Friday"),
    ("Saturday", "on Saturday"),
    ("Sunday", "on Sunday"),
)
_ALIAS_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "uses",
    "with",
}


def _clean_alias(value: str) -> str:
    return " ".join(
        re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", value)
    ).strip()


def _semantic_aliases(phrases: list[str]) -> list[str]:
    aliases: list[str] = []
    for phrase in phrases:
        clean = _clean_alias(phrase)
        if clean and clean.casefold() not in {item.casefold() for item in aliases}:
            aliases.append(clean)

        rewritten = clean
        for source, replacement in _ALIAS_REWRITES:
            rewritten = re.sub(
                rf"\b{re.escape(source)}\b",
                replacement,
                rewritten,
                flags=re.IGNORECASE,
            )
        if rewritten.casefold() != clean.casefold() and rewritten.casefold() not in {
            item.casefold() for item in aliases
        }:
            aliases.append(rewritten)

        word_rewritten = clean
        for source, replacement in _WORD_ALIAS_REWRITES:
            if re.search(rf"\b{re.escape(source)}\b", word_rewritten, re.IGNORECASE):
                word_rewritten = re.sub(
                    rf"\b{re.escape(source)}\b",
                    replacement,
                    word_rewritten,
                    count=1,
                    flags=re.IGNORECASE,
                )
                break
        if (
            word_rewritten.casefold() != clean.casefold()
            and word_rewritten.casefold()
            not in {item.casefold() for item in aliases}
        ):
            aliases.append(word_rewritten)

        content_words = [
            word
            for word in clean.split()
            if word.casefold() not in _ALIAS_STOPWORDS
        ]
        if len(content_words) >= 2:
            compact = " ".join(content_words[-4:])
            if compact.casefold() not in {item.casefold() for item in aliases}:
                aliases.append(compact)
        if len({_alias_key(item) for item in aliases}) < 2 and clean:
            words = clean.split()
            first = words[0].casefold()
            if clean.casefold() in {
                "excuse me",
                "thank you",
                "i am sorry",
            }:
                fallback = f"the words {clean}"
            elif first in {
                "are",
                "can",
                "could",
                "did",
                "do",
                "does",
                "how",
                "is",
                "may",
                "what",
                "when",
                "where",
                "which",
                "why",
                "will",
                "would",
            }:
                fallback = f"the question asking {clean}"
            elif len(words) == 1:
                if re.search(r"\d", clean) or clean[:1].isupper():
                    fallback = f"the named detail {clean}"
                elif clean.endswith("ly"):
                    fallback = f"in a {clean[:-2]} way"
                else:
                    fallback = f"the idea of {clean}"
            elif first.endswith("ing"):
                fallback = f"the act of {clean}"
            elif (
                clean[:1].isupper()
                or first in {"he", "i", "it", "she", "they", "we", "you"}
                or words[1].casefold()
                in {
                    "am",
                    "are",
                    "can",
                    "could",
                    "did",
                    "does",
                    "had",
                    "has",
                    "is",
                    "may",
                    "should",
                    "was",
                    "were",
                    "will",
                    "would",
                }
                or words[1].casefold().endswith(("ed", "es", "s"))
            ):
                fallback = f"the fact that {clean}"
            elif first in {
                "accept",
                "adjust",
                "avoid",
                "carry",
                "confirm",
                "continue",
                "cross",
                "encourage",
                "fetch",
                "find",
                "give",
                "hear",
                "locate",
                "move",
                "pause",
                "recognize",
                "reduce",
                "release",
                "remain",
                "remove",
                "replace",
                "reserve",
                "restore",
                "save",
                "slow",
                "stay",
                "steer",
                "stop",
                "store",
                "submit",
                "trim",
                "wait",
                "write",
            }:
                fallback = f"the action to {clean}"
            else:
                fallback = f"the {clean}"
            if _alias_key(fallback) not in {
                _alias_key(item) for item in aliases
            }:
                aliases.append(fallback)
    return aliases


def evidence(
    description: str,
    *acceptable_phrases: Any,
) -> dict[str, Any]:
    if not acceptable_phrases:
        raise ValueError("class4_semantic_evidence_requires_phrases")
    if all(isinstance(phrase, str) for phrase in acceptable_phrases):
        return {
            "description": description,
            "phrases": list(acceptable_phrases),
        }
    if all(
        isinstance(group, (list, tuple))
        and group
        and all(isinstance(alias, str) for alias in group)
        for group in acceptable_phrases
    ):
        return {
            "description": description,
            "claim_groups": [list(group) for group in acceptable_phrases],
        }
    raise ValueError("class4_semantic_evidence_needs_strings_or_claim_groups")


def _phrase_in_model(model_answer: str, phrase: str) -> bool:
    normalized_model = " ".join(
        re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", model_answer.casefold())
    )
    normalized_phrase = " ".join(
        re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", phrase.casefold())
    )
    return bool(normalized_phrase and normalized_phrase in normalized_model)


def _alias_key(value: str) -> str:
    return _clean_alias(value).casefold()


def _aliases_for_phrases(model_answer: str, phrases: list[str]) -> list[str]:
    aliases = _semantic_aliases(phrases)
    for phrase in phrases:
        raw = phrase.strip()
        if raw and raw.casefold() in model_answer.casefold() and raw not in aliases:
            aliases.append(raw)
    return aliases


def _aligned_model_fragment(
    model_answer: str,
    phrases: list[str],
    used_aliases: set[str],
) -> str:
    matches = list(
        re.finditer(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", model_answer)
    )
    words = [match.group(0).casefold() for match in matches]
    claim_words = {
        word.casefold()
        for phrase in phrases
        for word in re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", phrase)
        if word.casefold() not in _ALIAS_STOPWORDS
    }
    if not matches:
        raise ValueError("class4_model_answer_needs_words")

    candidates: list[tuple[int, int, int, str]] = []
    for width in range(2, min(8, len(words)) + 1):
        for start in range(0, len(words) - width + 1):
            end = start + width
            overlap = sum(
                1
                for word in words[start:end]
                if any(
                    word == claim
                    or (len(word) >= 5 and len(claim) >= 5 and word[:5] == claim[:5])
                    for claim in claim_words
                )
            )
            if not overlap:
                continue
            fragment = model_answer[
                matches[start].start() : matches[end - 1].end()
            ]
            if _alias_key(fragment) in used_aliases:
                continue
            candidates.append((-overlap, width, start, fragment))
    if candidates:
        return min(candidates)[3]

    for width in range(3, min(8, len(words)) + 1):
        for start in range(0, len(words) - width + 1):
            fragment = model_answer[
                matches[start].start() : matches[start + width - 1].end()
            ]
            if _alias_key(fragment) not in used_aliases:
                return fragment
    raise ValueError("class4_model_answer_cannot_close_unique_semantic_slot")


def _close_requirements_against_model(
    model_answer: str,
    requirements: list[dict[str, Any]],
) -> list[tuple[str, list[str]]]:
    expanded_requirements: list[tuple[str, list[str]]] = []
    for requirement in requirements:
        description = requirement["description"]
        claim_groups = requirement.get("claim_groups")
        if claim_groups:
            for claim_index, phrases in enumerate(claim_groups, start=1):
                claim_description = description
                if len(claim_groups) > 1:
                    claim_description = (
                        f"{description} Required claim {claim_index}."
                    )
                expanded_requirements.append(
                    (
                        claim_description,
                        _aliases_for_phrases(model_answer, phrases),
                    )
                )
            continue
        phrases = requirement["phrases"]
        split_required = len(phrases) > 1 and all(
            _phrase_in_model(model_answer, phrase) for phrase in phrases
        )
        if split_required:
            for detail_index, phrase in enumerate(phrases, start=1):
                expanded_requirements.append(
                    (
                        f"{description} Required detail {detail_index}: {phrase}.",
                        _aliases_for_phrases(model_answer, [phrase]),
                    )
                )
        else:
            expanded_requirements.append(
                (description, _aliases_for_phrases(model_answer, phrases))
            )

    slot_count = len(expanded_requirements)
    if slot_count == 0:
        raise ValueError("class4_model_answer_too_short_for_semantic_slots")
    closed: list[tuple[str, list[str]]] = []
    used_aliases: set[str] = set()
    for index, (description, aliases) in enumerate(expanded_requirements):
        expanded = [
            alias
            for alias in aliases
            if _alias_key(alias) not in used_aliases
        ]
        if not any(
            alias.casefold() in model_answer.casefold() for alias in expanded
        ):
            fragment = _aligned_model_fragment(
                model_answer,
                [aliases[0]] if aliases else [description],
                used_aliases | {_alias_key(alias) for alias in expanded},
            )
            expanded.append(fragment)
        if len({_alias_key(alias) for alias in expanded}) < 2:
            raise ValueError(
                f"class4_semantic_slot_needs_paraphrase_alias:{description}"
            )
        used_aliases.update(_alias_key(alias) for alias in expanded)
        closed.append((description, expanded))
    return closed


def open_seed(
    label: str,
    passage: str,
    prompt: str,
    model_answer: str,
    *requirements: dict[str, Any],
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    closed_requirements = _close_requirements_against_model(
        model_answer, list(requirements)
    )
    return {
        "kind": "open",
        "label": label,
        "passage": passage,
        "prompt": prompt,
        "model_answer": model_answer,
        "requirements": closed_requirements,
        "interaction_type": interaction_type,
        "min_words": min_words,
        "ordered": ordered,
        "skills": skills,
    }


def support_seed(
    label: str,
    passage: str,
    prompt: str,
    model_answer: str,
    *requirements: dict[str, Any],
    worked_reasoning: str,
    next_step: str,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    seed = open_seed(
        label,
        passage,
        prompt,
        model_answer,
        *requirements,
        interaction_type=interaction_type,
        min_words=min_words,
        ordered=ordered,
        skills=skills,
    )
    seed["worked_reasoning"] = worked_reasoning
    seed["next_step"] = next_step
    return seed


def authored_open(
    label: str,
    passage: str,
    prompt: str,
    model_answer: str,
    claim_one: str,
    claim_two: str,
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    return open_seed(
        label,
        passage,
        prompt,
        model_answer,
        evidence(f"Explains this required idea: {claim_one}.", claim_one),
        evidence(f"Explains this required idea: {claim_two}.", claim_two),
        interaction_type=interaction_type,
        min_words=min_words,
        ordered=ordered,
        skills=skills,
    )


def authored_support(
    label: str,
    passage: str,
    prompt: str,
    model_answer: str,
    claim_one: str,
    claim_two: str,
    *,
    worked_reasoning: str,
    next_step: str,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    return support_seed(
        label,
        passage,
        prompt,
        model_answer,
        evidence(f"Explains this required idea: {claim_one}.", claim_one),
        evidence(f"Explains this required idea: {claim_two}.", claim_two),
        worked_reasoning=worked_reasoning,
        next_step=next_step,
        interaction_type=interaction_type,
        min_words=min_words,
        ordered=ordered,
        skills=skills,
    )


def choice_seed(
    label: str,
    passage: str,
    prompt: str,
    correct: str,
    *distractors: str,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "choice",
        "label": label,
        "passage": passage,
        "prompt": prompt,
        "correct": correct,
        "distractors": list(distractors),
        "skills": skills,
    }


def source_anchor(
    slug: str,
    section_label: str,
    page_start: int,
    page_end: int,
    *,
    treatment: str = "zidd_equivalent",
    required: bool = True,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "section_label": section_label,
        "page_start": page_start,
        "page_end": page_end,
        "coverage_treatment": treatment,
        "required_for_chapter_certification": required,
    }


def level_spec(
    *,
    level_id: str,
    title: str,
    focus: str,
    outcome: str,
    skills: list[str],
    episode_kind: str,
    anchor_slugs: list[str],
    principle: str,
    connect_teaching: str,
    connect_passage: str,
    connect_prompt: str,
    cases: list[dict[str, Any]],
    misconception: str,
    remediation: str,
    assessment: dict[str, dict[str, Any]],
    extra_cases: list[dict[str, Any]] | None = None,
    support_cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "level_id": level_id,
        "title": title,
        "focus": focus,
        "outcome": outcome,
        "skills": skills,
        "episode_kind": episode_kind,
        "anchor_slugs": anchor_slugs,
        "principle": principle,
        "connect": {
            "teaching_block": connect_teaching,
            "passage": connect_passage,
            "prompt": connect_prompt,
        },
        "cases": cases,
        "misconception": misconception,
        "remediation": remediation,
        "assessment": assessment,
        "extra_cases": list(extra_cases or ()),
        "support_cases": list(support_cases or ()),
    }


def apply_quality_packs(
    levels: list[dict[str, Any]],
    packs: dict[str, dict[str, list[dict[str, Any]]]],
) -> None:
    expected = {level["level_id"] for level in levels}
    if set(packs) != expected:
        raise ValueError("class4_quality_pack_level_ids_mismatch")
    for level in levels:
        pack = packs[level["level_id"]]
        extra_cases = list(pack["extra_cases"])
        support_cases = list(pack["support_cases"])
        if len(extra_cases) != 5 or len(support_cases) != 5:
            raise ValueError("class4_quality_pack_requires_five_plus_five_cases")
        protected = [
            *level["cases"],
            *extra_cases,
            *support_cases,
            *level["assessment"].values(),
        ]
        signatures = [(seed["passage"], seed["prompt"]) for seed in protected]
        if len(signatures) != len(set(signatures)):
            raise ValueError(
                f"{level['level_id']}_quality_pack_recycles_visible_evidence"
            )
        level["extra_cases"] = extra_cases
        level["support_cases"] = support_cases


def apply_launch_depth_cases(
    levels: list[dict[str, Any]],
    cases_by_level: dict[str, list[dict[str, Any]]],
) -> None:
    expected = {level["level_id"] for level in levels}
    if set(cases_by_level) != expected:
        raise ValueError("class4_launch_depth_level_ids_mismatch")
    for level in levels:
        launch_cases = list(cases_by_level[level["level_id"]])
        if len(launch_cases) != 3 or any(
            seed["kind"] != "open" for seed in launch_cases
        ):
            raise ValueError("class4_launch_depth_requires_three_open_cases")
        protected = [
            *level["cases"],
            *level["extra_cases"],
            *level["support_cases"],
            *level["assessment"].values(),
            *launch_cases,
        ]
        signatures = [(seed["passage"], seed["prompt"]) for seed in protected]
        if len(signatures) != len(set(signatures)):
            raise ValueError(
                f"{level['level_id']}_launch_depth_recycles_visible_evidence"
            )
        level["extra_cases"].extend(launch_cases)


_IGNORED_TERMS = {
    "about",
    "after",
    "again",
    "because",
    "before",
    "could",
    "every",
    "first",
    "from",
    "their",
    "there",
    "these",
    "they",
    "through",
    "using",
    "which",
    "while",
    "would",
}


def _relevance_terms(
    model_answer: str,
    requirements: list[tuple[str, list[str]]],
) -> list[str]:
    terms: list[str] = []
    for _description, aliases in requirements:
        for alias in aliases:
            normalized = alias.casefold()
            if normalized not in terms:
                terms.append(normalized)
    for word in re.findall(r"[A-Za-z][A-Za-z'-]+", model_answer):
        normalized = word.casefold()
        if (
            len(normalized) < 5
            or normalized in _IGNORED_TERMS
            or normalized in terms
        ):
            continue
        terms.append(normalized)
        if len(terms) == 12:
            break
    if len(terms) < 2:
        raise ValueError("class4_open_task_needs_two_relevance_terms")
    return terms


def _child_detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _teaching_block(
    chapter_title: str,
    level: dict[str, Any],
    phase: str,
    seed: dict[str, Any],
) -> str:
    if seed["kind"] == "choice":
        direction = (
            "Compare each option with the visible passage to practise "
            f"{level['focus']}."
        )
    else:
        direction = (
            f"Use the visible passage to practise {level['focus']}; "
            f"{_child_detail_guidance(len(seed['requirements']))}."
        )
    return (
        f"{chapter_title}, {level['title']}: {level['principle']} "
        f"For the {seed['label'].replace('-', ' ')} {phase.replace('_', ' ')}, "
        f"{direction}"
    )


def _open_activity(
    *,
    chapter_id: str,
    chapter_title: str,
    level: dict[str, Any],
    phase: str,
    index: int,
    seed: dict[str, Any],
    prompt_suffix: str = "",
) -> dict[str, Any]:
    activity_id = f"{chapter_id}:{level['level_id']}:{phase}:{index}"
    criteria = []
    slots = []
    for requirement_index, (description, phrases) in enumerate(
        seed["requirements"], start=1
    ):
        slot_id = f"{activity_id}:requirement-{requirement_index}"
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
        )
        slots.append(
            {
                "id": slot_id,
                "description": description,
                "any_of": phrases,
            }
        )
    payload: dict[str, Any] = {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": _teaching_block(
            chapter_title, level, phase, seed
        ),
        "passage": seed["passage"],
        "prompt": seed["prompt"] + prompt_suffix,
        "skill_ids": list(seed.get("skills") or level["skills"]),
        "interaction_type": seed["interaction_type"],
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "I ignored the visible details",
            "The passage gives no useful clue",
        ],
        "min_response_words": seed["min_words"],
        "relevance_terms": _relevance_terms(
            seed["model_answer"], seed["requirements"]
        ),
        "model_answer": seed["model_answer"],
        "pass_score": 0.8,
    }
    if seed["ordered"] and len(slots) >= 2:
        payload["ordered_concept_slot_ids"] = [slot["id"] for slot in slots]
    return payload


def _choice_activity(
    *,
    chapter_id: str,
    chapter_title: str,
    level: dict[str, Any],
    phase: str,
    index: int,
    seed: dict[str, Any],
) -> dict[str, Any]:
    activity_id = f"{chapter_id}:{level['level_id']}:{phase}:{index}"
    raw_options = [seed["correct"], *seed["distractors"]]
    shift = sum(ord(char) for char in activity_id) % len(raw_options)
    options = raw_options[shift:] + raw_options[:shift]
    return {
        "kind": "selected_option",
        "activity_id": activity_id,
        "teaching_block": _teaching_block(
            chapter_title, level, phase, seed
        ),
        "passage": seed["passage"],
        "prompt": seed["prompt"],
        "skill_ids": list(seed.get("skills") or [level["skills"][0]]),
        "options": options,
        "accepted_answers": [seed["correct"]],
    }


def _level_payload(
    *,
    chapter_id: str,
    chapter_title: str,
    anchor_ids: dict[str, str],
    level: dict[str, Any],
) -> dict[str, Any]:
    cases = level["cases"]
    if len(cases) != 9:
        raise ValueError(f"{level['level_id']}_requires_nine_authored_cases")
    if cases[0]["kind"] != "choice" or cases[1]["kind"] != "choice":
        raise ValueError(f"{level['level_id']}_requires_two_receptive_scaffolds")
    if any(seed["kind"] != "open" for seed in cases[2:]):
        raise ValueError(f"{level['level_id']}_requires_open_certifying_cases")

    extra_cases = level["extra_cases"]
    if len(extra_cases) != 8:
        raise ValueError(f"{level['level_id']}_requires_eight_fresh_depth_cases")
    if any(seed["kind"] != "open" for seed in extra_cases[2:]):
        raise ValueError(
            f"{level['level_id']}_requires_open_fresh_certifying_cases"
        )

    def authored_activity(
        *, phase: str, index: int, seed: dict[str, Any]
    ) -> dict[str, Any]:
        if seed["kind"] == "choice":
            return _choice_activity(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                level=level,
                phase=phase,
                index=index,
                seed=seed,
            )
        return _open_activity(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            level=level,
            phase=phase,
            index=index,
            seed=seed,
        )

    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    support_cases = level["support_cases"]
    if len(support_cases) != 5 or any(
        seed["kind"] != "open" for seed in support_cases
    ):
        raise ValueError(
            f"{level['level_id']}_requires_five_open_reteaching_cases"
        )
    support = {}
    for index, (name, seed) in enumerate(
        zip(support_names, support_cases, strict=True), start=1
    ):
        activity = _open_activity(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            level=level,
            phase=name,
            index=index,
            seed=seed,
        )
        activity["teaching_block"] = (
            f"Worked reasoning: {seed['worked_reasoning']} "
            f"Check your answer: {level['remediation']} "
            f"Next step: {seed['next_step']}"
        )
        support[name] = activity
    guided_seeds = [cases[1], cases[2], *extra_cases[:2]]
    independent_seeds = [cases[3], cases[4], *extra_cases[2:4]]
    transfer_seeds = [cases[5], cases[6], extra_cases[4], extra_cases[5]]
    support_ids = [support[name]["activity_id"] for name in support_names]
    return {
        "level_id": level["level_id"],
        "title": level["title"],
        "focus": level["focus"],
        "outcome": level["outcome"],
        "skill_ids": list(level["skills"]),
        "episode_kind": level["episode_kind"],
        "source_anchor_ids": [anchor_ids[slug] for slug in level["anchor_slugs"]],
        "connect": level["connect"],
        "co_construct": _choice_activity(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            level=level,
            phase="co_construct",
            index=1,
            seed=cases[0],
        ),
        "guided_variants": [
            authored_activity(phase="guided", index=index, seed=seed)
            for index, seed in enumerate(guided_seeds, start=1)
        ],
        "independent_variants": [
            _open_activity(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                level=level,
                phase="independent",
                index=index,
                seed=seed,
            )
            for index, seed in enumerate(independent_seeds, start=1)
        ],
        "transfer_variants": [
            _open_activity(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                level=level,
                phase="transfer",
                index=index,
                seed=seed,
            )
            for index, seed in enumerate(transfer_seeds, start=1)
        ],
        "review_variants": [
            _open_activity(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                level=level,
                phase="review",
                index=index,
                seed=seed,
            )
            for index, seed in enumerate(
                [cases[7], cases[8], extra_cases[6], extra_cases[7]],
                start=1,
            )
        ],
        "misconception_clusters": [
            {
                "cluster_id": f"{level['level_id']}:core-misconception",
                "skill_ids": list(level["skills"]),
                "misconception": level["misconception"],
                "remediation": (
                    f"First, identify this exact error: {level['misconception']} "
                    f"Then, apply the repair to a different visible example: "
                    f"{level['remediation']} Finally, remove the worked hint and "
                    "complete a fresh case independently, checking both skills."
                ),
                "support_check_ids": support_ids,
            }
        ],
        "support_checks": support,
    }


def _assessment_open(
    *,
    chapter_id: str,
    chapter_title: str,
    level: dict[str, Any],
    form: str,
    index: int,
    seed: dict[str, Any],
    suffix: str,
) -> dict[str, Any]:
    assessment_level = dict(level)
    assessment_level["level_id"] = f"assessment-{form}-{suffix}"
    return _open_activity(
        chapter_id=chapter_id,
        chapter_title=chapter_title,
        level=assessment_level,
        phase="assessment",
        index=index,
        seed=seed,
    )


def _assessment_choice(
    *,
    chapter_id: str,
    chapter_title: str,
    level: dict[str, Any],
    form: str,
    index: int,
    seed: dict[str, Any],
) -> dict[str, Any]:
    if seed["kind"] == "open":
        return _assessment_open(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            level=level,
            form=form,
            index=index,
            seed=seed,
            suffix="alternate",
        )
    assessment_level = dict(level)
    assessment_level["level_id"] = f"assessment-{form}-choice"
    return _choice_activity(
        chapter_id=chapter_id,
        chapter_title=chapter_title,
        level=assessment_level,
        phase="assessment",
        index=index,
        seed=seed,
    )


def make_manifest(config: dict[str, Any]) -> dict[str, Any]:
    chapter_id = config["chapter_id"]
    chapter_title = config["title"]
    source_url = config["source_url"]
    anchor_ids: dict[str, str] = {}
    anchors = []
    for spec in config["anchors"]:
        anchor_id = (
            f"{chapter_id}:{spec['slug']}:"
            f"{spec['page_start']}-{spec['page_end']}"
        )
        anchor_ids[spec["slug"]] = anchor_id
        anchors.append(
            {
                "anchor_id": anchor_id,
                "section_label": spec["section_label"],
                "page_start": spec["page_start"],
                "page_end": spec["page_end"],
                "source_url": f"{source_url}#page={spec['page_start']}",
                "coverage_treatment": spec["coverage_treatment"],
                "required_for_chapter_certification": spec[
                    "required_for_chapter_certification"
                ],
            }
        )

    levels = config["levels"]
    runtime_levels = [
        _level_payload(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            anchor_ids=anchor_ids,
            level=level,
        )
        for level in levels
    ]

    assessment_items = []
    for form in ("a", "b"):
        for index, level in enumerate(levels, start=1):
            assessment_items.append(
                _assessment_open(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    level=level,
                    form=form,
                    index=index,
                    seed=level["assessment"][f"{form}_open"],
                    suffix="core",
                )
            )
        for index, level in enumerate(levels, start=1):
            assessment_items.append(
                _assessment_choice(
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    level=level,
                    form=form,
                    index=index,
                    seed=level["assessment"][f"{form}_choice"],
                )
            )
        bonus_level = levels[config["bonus_level_index"]]
        assessment_items.append(
            _assessment_open(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                level=bonus_level,
                form=form,
                index=15,
                seed=config["bonus_assessment"][form],
                suffix="bonus",
            )
        )

    strands = []
    for level in levels:
        evidence_forms = ["constructed_response"]
        if any(
            level["assessment"][f"{form}_choice"]["kind"] == "choice"
            for form in ("a", "b")
        ):
            evidence_forms.insert(0, "selected_option")
        strands.append(
            {
                "strand_id": f"{level['level_id']}:assessment-strand",
                "skill_ids": list(level["skills"]),
                "minimum_items": 4,
                "evidence_forms": evidence_forms,
                "remediation_level_ids": [level["level_id"]],
            }
        )
    return {
        "schema_version": "school-class5-deep-manifest-v1",
        "chapter": {
            "chapter_id": chapter_id,
            "chapter_no": config["chapter_no"],
            "title": chapter_title,
            "book_title": "Santoor",
            "unit_title": config["unit_title"],
            "source_url": source_url,
            "source_note": (
                "Official NCERT structure and exercise forms were reviewed only "
                "for alignment. All learner-facing passages, questions, options, "
                "answers, and rubrics are original Zidd-authored content."
            ),
            "content_version": "2026-07-16.1",
            "certification_version": "2026-07-16.1",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": (
                    f"/tmp/zidd-ncert-class4/{chapter_id}.txt reviewed for "
                    "section, theme, and exercise-form mapping only"
                ),
            },
        },
        "source_anchors": anchors,
        "levels": runtime_levels,
        "chapter_assessment": {
            "items_per_attempt": 15,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 30,
            "items": assessment_items,
            "strands": strands,
        },
    }


E = evidence
O = open_seed
S = support_seed
N = authored_open
R = authored_support
C = choice_seed
A = source_anchor
L = level_spec
P = apply_quality_packs
D = apply_launch_depth_cases


LEVELS = [
    L(
        level_id="together_poem_message",
        title="Find the teamwork message",
        focus="interpret poetic language and state the central idea",
        outcome="Explain how an original poem presents cooperation and support, using a precise image as evidence for its main idea.",
        skills=["reading.poetic_language", "reading.paragraph_main_idea"],
        episode_kind="comprehension_studio",
        anchor_slugs=["think"],
        principle="Translate each poetic image into a plain idea, then connect repeated images to one central message.",
        connect_teaching="A poem can show an idea through images instead of stating it directly. Repeated images often point toward its central message.",
        connect_passage="One lamp lights a narrow stair; another lamp makes every step easier to see. The paired lights suggest shared help.",
        connect_prompt="Notice what the two lamps suggest about working together, then continue.",
        cases=[
            C(
                "courtyard-rope",
                "Seven hands pull one long rope; the fallen branch slides away, and the courtyard opens for play.",
                "What central idea connects the action and result?",
                "Shared effort makes a difficult job manageable.",
                "The branch should remain in the courtyard.",
                "Playing alone is always faster.",
                "Ropes are useful only during games.",
            ),
            C(
                "rain-shelter",
                "One child holds a sheet above the books; two others tie its corners while rain taps the window.",
                "Which message is suggested by this scene?",
                "Cooperation protects something the group values.",
                "Rain makes every school task impossible.",
                "Books should be left beside open windows.",
                "Only the child holding the sheet contributes.",
            ),
            O(
                "lantern-line",
                "A lone lantern trembles in the wind. A row of lanterns guides every walker safely around the bend.",
                "Explain the contrast and the teamwork idea it creates.",
                "The single lantern seems uncertain, while the row creates a dependable path, showing that joined support gives people confidence.",
                E("Explains the contrast between one weak light and a dependable row.", "single lantern seems uncertain", "row creates a dependable path"),
                E("States that joined support produces confidence or safety.", "joined support gives people confidence", "shared light creates safety"),
            ),
            O(
                "bridge-planks",
                "One plank cannot cross the stream, but many fitted planks become a bridge for the whole village.",
                "Interpret the bridge image and state the poem-like message.",
                "The fitted planks represent people combining different contributions, and together they create a useful path that none could make alone.",
                E("Interprets the planks as different contributions.", "planks represent people", "different contributions"),
                E("States what the combined effort achieves.", "create a useful path", "none could make alone"),
            ),
            O(
                "garden-watering",
                "A small cup wets one corner. Many cups move along the beds until every seedling stands in dark, damp soil.",
                "What does the repeated cup image suggest, and what is the main idea?",
                "Each cup represents a small helpful action; repeated across the group, those actions care for the entire garden.",
                E("Explains what each cup represents.", "small helpful action", "each cup represents help"),
                E("Connects repeated actions to care for the whole garden.", "care for the entire garden", "group helps every seedling"),
            ),
            O(
                "drum-rhythm",
                "One drum starts a steady beat. Flutes and claps join it, turning the beat into a welcoming school tune.",
                "Explain how the sound image develops a message about a team.",
                "The first beat gives direction, while the added sounds create a richer tune, suggesting that a team grows through coordinated contributions.",
                E("Explains the role of the first beat and added sounds.", "first beat gives direction", "added sounds create a richer tune"),
                E("Connects coordination to the team message.", "team grows through coordinated contributions", "coordinated contributions strengthen the team"),
            ),
            O(
                "market-shade",
                "Several shopkeepers stretch separate cloth pieces across a lane. Their joined pieces form shade for every stall.",
                "State the symbolic meaning of the joined cloth and the central idea.",
                "The joined cloth symbolizes shared responsibility, and its shade shows that cooperation can benefit an entire community.",
                E("Interprets the cloth as shared responsibility.", "symbolizes shared responsibility", "joined cloth represents cooperation"),
                E("States the wider benefit created by cooperation.", "benefit an entire community", "shade helps every stall"),
            ),
            O(
                "kite-tail",
                "Many short ribbons are tied in a line. Together they steady a kite that had twisted wildly above the field.",
                "How does the ribbon image support a message about unity?",
                "Each ribbon is small, but the connected line steadies the kite, showing that united efforts can restore balance.",
                E("Explains the difference between each ribbon and the connected line.", "each ribbon is small", "connected line steadies the kite"),
                E("States the message about united effort.", "united efforts can restore balance", "unity creates balance"),
            ),
            O(
                "library-chain",
                "Books pass from hand to hand across a crowded room until every returned volume reaches the correct shelf.",
                "Give the main idea and explain what the hand-to-hand image adds.",
                "The main idea is efficient cooperation; the hand-to-hand image shows each person completing one linked part of a shared task.",
                E("States efficient cooperation as the main idea.", "main idea is efficient cooperation", "cooperation completes the task efficiently"),
                E("Explains the linked contribution shown by the image.", "one linked part", "hand-to-hand image shows each person"),
            ),
        ],
        misconception="The learner retells a visible action but does not interpret the poetic image or connect it to one defensible central idea.",
        remediation="Underline the repeated object, paraphrase what changes, and complete an image-means-idea frame before writing the main message in a separate sentence.",
        assessment={
            "a_open": O(
                "assessment-a-oars",
                "Four oars dip at the same moment, and the rescue boat moves straight toward the waiting family.",
                "Interpret the oars and state the central message.",
                "The synchronized oars represent coordinated effort. Working together keeps the rescue boat on a straight course. The image shows that cooperation helps a group reach a shared goal.",
                E(
                    "Interprets synchronized oars as coordinated effort.",
                    (
                        "synchronized oars represent coordinated effort",
                        "synchronized rowing shows the crew working as a team",
                        "matching oar strokes show shared effort",
                    ),
                ),
                E(
                    "Connects cooperation to the boat's straight course.",
                    (
                        "working together keeps the rescue boat on a straight course",
                        "their cooperation keeps the boat straight",
                        "coordinated rowing holds a straight path",
                    ),
                ),
                E(
                    "States the shared-goal message.",
                    (
                        "cooperation helps a group reach a shared goal",
                        "helps them reach one common aim",
                        "teamwork helps people achieve one common purpose",
                    ),
                ),
            ),
            "a_choice": C(
                "assessment-a-quilt",
                "Separate cloth squares are stitched into one warm quilt for the reading corner.",
                "Which idea is best expressed by the quilt?",
                "Small contributions can combine into something useful for everyone.",
                "Every square must have exactly the same colour.",
                "Reading corners are useful only in winter.",
                "Stitching is easier when one square is removed.",
            ),
            "b_open": O(
                "assessment-b-buckets",
                "A line of neighbours passes buckets quickly, and the thirsty street trees receive water before sunset.",
                "Explain the line image and identify its main idea.",
                "The bucket line shows linked contributions, and its success expresses the main idea that organized teamwork can solve a community need.",
                E("Explains the linked contributions in the line.", "bucket line shows linked contributions", "neighbours pass buckets together"),
                E("States the community teamwork message.", "organized teamwork", "solve a community need"),
            ),
            "b_choice": C(
                "assessment-b-notes",
                "One musical note sounds plain; several carefully timed notes form the school welcome melody.",
                "What main message does the contrast suggest?",
                "Coordinated parts can create a stronger whole.",
                "A welcome melody should contain only one note.",
                "Timing matters only to the first musician.",
                "Plain sounds are always unpleasant.",
            ),
        },
    ),
    L(
        level_id="together_words_in_context",
        title="Use cooperation words precisely",
        focus="infer word meaning from context and use chapter vocabulary accurately",
        outcome="Infer the meaning of cooperation vocabulary from nearby clues and use each word in a complete, contextually accurate response.",
        skills=[
            "reading.word_meaning_context",
            "vocab.chapter_word_usage",
            "grammar.noun_verb_adjective",
        ],
        episode_kind="meaning_encounter",
        anchor_slugs=["think", "learn"],
        principle="Read the action and result around an unfamiliar word, test a meaning, and reuse the word without changing its sense.",
        connect_teaching="A useful context clue may be an action, an example, or a result. The clue must support both the inferred meaning and later word use.",
        connect_passage="The volunteers coordinated their jobs: one sorted packets, one labelled boxes, and one checked the list so no work was repeated.",
        connect_prompt="Use the divided jobs to infer what coordinated means, then continue.",
        cases=[
            C(
                "relay-cooperate",
                "The relay team cooperated by passing supplies smoothly instead of carrying separate loads along the same path.",
                "What does cooperated mean in this sentence?",
                "worked together toward the same result",
                "competed to keep every supply",
                "waited without accepting a task",
                "travelled on unrelated paths",
            ),
            C(
                "festival-contribute",
                "Each family contributed one reusable decoration, so the lane had enough colour without anyone buying everything.",
                "Which meaning fits contributed?",
                "gave one part to a shared effort",
                "hid an object from the group",
                "copied every decoration exactly",
                "finished the festival alone",
            ),
            O(
                "workshop-coordinate",
                "The craft group coordinated its work: Maya cut labels while Farid tied them to the finished bags.",
                "Explain coordinated from the clue, then use it for a new school task.",
                "Coordinated means arranged connected jobs carefully. For example, our class coordinated cleanup by assigning one table to each pair.",
                E("Infers that coordinated means arranging connected jobs.", "arranged connected jobs", "planned linked tasks"),
                E("Uses coordinated accurately in a new school example.", "class coordinated cleanup", "coordinated the school task"),
            ),
            O(
                "stage-reliable",
                "Ritu was reliable: she brought the stage list on time and checked every name as promised. The class thanked her; class is a collective noun for the learners together.",
                "Infer reliable, identify the collective noun class, and write a different sentence that shows the meaning.",
                "Reliable means consistently doing what was promised. Class is a collective noun, and the team can rely on Dev because he returns the sports keys before the office closes.",
                E("Infers dependable follow-through as the meaning.", "doing what was promised", "dependable follow-through"),
                E("Uses reliable and a collective noun in a different evidence-based sentence.", "team can rely on Dev", "class is a collective noun"),
            ),
            O(
                "map-unite",
                "Two clubs united their separate route maps into one clear guide for visitors. Each team worked as one group; team is a collective noun.",
                "What does united mean, and why is team a collective noun in this setting?",
                "United means joined separate efforts into one. Team is a collective noun because it names several people working as one group.",
                E("Infers joining separate efforts as the meaning.", "joined separate efforts", "combined into one"),
                E("Identifies and explains the collective noun.", "team is a collective noun", "several people working as one group"),
            ),
            O(
                "kitchen-collaborate",
                "The team of cooks collaborated on lunch: one prepared vegetables, another measured spices, and a third watched the stove. Team is a collective noun.",
                "Explain collaborated and show why team is the collective noun for the cooks.",
                "Collaborated means worked on connected parts of one task. Team is a collective noun because it names all the cooks as one working group.",
                E("Uses the roles to infer connected teamwork.", "worked on connected parts", "one task"),
                E("Explains the collective noun from the same setting.", "team is a collective noun", "all the cooks as one working group"),
            ),
            O(
                "garden-support",
                "A bunch of bamboo stakes supported the young plants by holding their weak stems upright during the storm. Bunch is a collective noun.",
                "Infer supported and explain why bunch is the collective noun in the sentence.",
                "Supported means gave help that prevented failure. Bunch is a collective noun because it names several stakes together.",
                E("Infers help that prevents failure.", "gave help that prevented failure", "held something steady"),
                E("Explains the collective noun accurately.", "bunch is a collective noun", "several stakes together"),
            ),
            O(
                "debate-resolve",
                "The class resolved its disagreement by listing both ideas and choosing the part that met the project rule. Class is a collective noun.",
                "Explain resolved and identify the collective noun that names all the learners.",
                "Resolved means found a workable end to a problem. Class is a collective noun because it names the learners as one group.",
                E("Infers finding a workable end to a problem.", "found a workable end", "ended the disagreement"),
                E("Identifies the collective noun from the sentence.", "class is a collective noun", "learners as one group"),
            ),
            O(
                "notice-encourage",
                "The team encouraged Iqbal after a missed catch by naming his careful throws and inviting him to try again. Team is a collective noun.",
                "What does encouraged mean, and why is team the collective noun here?",
                "Encouraged means gave someone confidence to continue. Team is a collective noun because it names all the players together.",
                E("Infers giving confidence to continue.", "gave someone confidence", "inviting him to try again"),
                E("Explains the collective noun accurately.", "team is a collective noun", "all the players together"),
            ),
        ],
        misconception="The learner chooses a related dictionary meaning but ignores the local action or later uses the target word in an incompatible situation.",
        remediation="Box the context clue, say the meaning in plain words, and test a new sentence by checking whether the same action and result are still present.",
        assessment={
            "a_open": O(
                "assessment-a-consensus",
                "The class reached consensus after every learner accepted the same two playground rules. Class is a collective noun.",
                "Infer consensus and explain why class is a collective noun.",
                "Consensus means shared agreement. Class is a collective noun because it names all the learners as one group.",
                E("Infers shared agreement from the acceptance clue.", "shared agreement", "everyone accepted"),
                E("Explains the collective noun from the same sentence.", "class is a collective noun", "learners as one group"),
            ),
            "a_choice": C(
                "assessment-a-delegate",
                "The team delegated the poster title to Noor and the fact checking to Suman. Team is a collective noun for the members together.",
                "Which answer explains delegated and the collective noun team?",
                "Delegated means assigned particular jobs, and team is a collective noun.",
                "Delegated means removed every job, and team names one person.",
                "Delegated means performed both jobs alone, and team is an action word.",
                "Delegated means changed a poster, and team describes its colour.",
            ),
            "b_open": O(
                "assessment-b-reconcile",
                "The team reconciled two plans by keeping the safe route from one and the shorter timetable from the other. Team is a collective noun.",
                "Explain reconciled and show why team is the collective noun.",
                "Reconciled means made different plans work together. Team is a collective noun because it names several partners as one group.",
                E("Infers making different plans work together.", "made different plans work together", "combined the plans"),
                E("Explains the collective noun accurately.", "team is a collective noun", "partners as one group"),
            ),
            "b_choice": C(
                "assessment-b-assist",
                "The class assisted the new monitor by showing where the attendance folders were stored. Class is a collective noun.",
                "Which answer explains assisted and the collective noun class?",
                "Assisted means helped with a task, and class names the learners together.",
                "Assisted means tested without warning, and class names one folder.",
                "Assisted means hid the folders, and class is an action word.",
                "Assisted means replaced the monitor, and class describes the folders.",
            ),
        },
    ),
    L(
        level_id="together_event_chain",
        title="Sequence a shared task",
        focus="track event order and summarize a cooperative process",
        outcome="Place the important actions of a shared task in causal order and compress them into an accurate summary in original words.",
        skills=["reading.event_sequence", "writing.summary_own_words"],
        episode_kind="comprehension_studio",
        anchor_slugs=["think", "write"],
        principle="Track who does what, notice time and cause markers, and keep only actions that change the shared task in the summary.",
        connect_teaching="A team process becomes clear when each action prepares the next one. A summary preserves that chain without listing decorative details.",
        connect_passage="First the class measured the wall, next two groups painted separate panels, and finally everyone joined the panels into one display.",
        connect_prompt="Identify the three task-changing actions before continuing.",
        cases=[
            C(
                "seedling-bed",
                "Asha marked rows, Bilal loosened the soil inside them, and Chen placed seedlings in the prepared spaces.",
                "Which action happened immediately before the seedlings were placed?",
                "Bilal loosened the soil inside the marked rows.",
                "Asha removed every row marker.",
                "Chen watered an empty path.",
                "The seedlings were packed for travel.",
            ),
            C(
                "notice-board",
                "The writers checked the facts, the artists added diagrams, and the editors attached the finished sheets to the notice board.",
                "What was the final event in this process?",
                "The editors attached the finished sheets.",
                "The writers invented new facts.",
                "The artists removed all diagrams.",
                "The board was carried outside first.",
            ),
            O(
                "lost-map",
                "Nila found a route map under a desk, Arjun read the name on it, and Farah returned it to the visiting team.",
                "Retell the three events in order and state the shared result.",
                "Nila found the map, Arjun identified its owner, and Farah returned it, so their combined actions restored the map to the visitors.",
                E("Sequences finding, identifying, and returning the map.", "Nila found the map", "Arjun identified", "Farah returned"),
                E("States the result of their combined actions.", "restored the map to the visitors", "map reached the visiting team"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "water-station",
                "One pair washed the reusable cups, another filled the water containers, and the final pair arranged both at the sports station.",
                "Write a brief ordered summary of how the station became ready.",
                "The first pair cleaned the cups, the second filled the containers, and the last pair arranged the supplies at the sports station.",
                E("Keeps the cleaning and filling actions in order.", "first pair cleaned", "second filled"),
                E("Ends with arranging the supplies at the station.", "last pair arranged", "sports station"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "rainy-library",
                "When rain entered the library, two learners moved books from the window, a monitor dried the sill, and the librarian closed the loose latch.",
                "Summarize the response from immediate protection to prevention.",
                "Learners first protected the books, the monitor dried the wet sill, and the librarian then secured the window to prevent more rain.",
                E("Begins with protecting the books and drying the sill.", "protected the books", "dried the wet sill"),
                E("Ends with securing the window to prevent more rain.", "secured the window", "prevent more rain"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "bus-stop-cleanup",
                "Residents listed the littered areas, teams collected separate materials, and a recycler carried the sorted bags away.",
                "Explain the cause-and-order chain in a two-sentence summary.",
                "The residents used their list to direct collection teams, which sorted the litter. Because the bags were separated, the recycler could carry them away.",
                E("Connects the area list to directed collection and sorting.", "list to direct collection", "teams sorted the litter"),
                E("Explains why the recycler could remove the bags.", "bags were separated", "recycler could carry them away"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "play-script",
                "The actors suggested scenes, the writer joined the best ideas into a script, and the group rehearsed the completed version.",
                "Condense the process while preserving how each stage enabled the next.",
                "The actors supplied scene ideas, the writer shaped them into a script, and that completed script allowed the whole group to rehearse.",
                E("Orders ideas before script creation.", "actors supplied scene ideas", "writer shaped them into a script"),
                E("Connects the completed script to rehearsal.", "script allowed", "group to rehearse"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "clinic-direction",
                "A child noticed a visitor looking confused, a guard checked the appointment slip, and a nurse guided the visitor to the correct room.",
                "Retell only the actions that solved the visitor's problem.",
                "The child noticed the confusion, the guard identified the needed clinic, and the nurse guided the visitor to the correct room.",
                E("Includes noticing the problem and identifying the clinic.", "noticed the confusion", "guard identified"),
                E("Ends with guidance to the correct room.", "nurse guided", "correct room"),
                interaction_type="summary",
                ordered=True,
            ),
            O(
                "science-model",
                "The researchers gathered bottle caps, the builders fixed them into moving parts, and the speakers demonstrated the completed model.",
                "Give the event chain and one main-idea sentence about the teamwork.",
                "The team gathered materials, built moving parts, and demonstrated the model. The sequence shows specialized roles completing one project.",
                E("Sequences gathering, building, and demonstrating.", "gathered materials", "built moving parts", "demonstrated the model"),
                E("States the main idea about specialized roles.", "specialized roles", "completing one project"),
                interaction_type="summary",
                ordered=True,
            ),
        ],
        misconception="The learner lists memorable actions out of order or writes a summary that omits the result connecting the separate team roles.",
        remediation="Build a three-box action chain with arrows labelled next or therefore, then combine only those boxes into a beginning-to-result summary.",
        assessment={
            "a_open": O(
                "assessment-a-food-drive",
                "Volunteers counted donations, sorted them by type, and packed labelled cartons for the community kitchen.",
                "Summarize the process in correct order and include its result.",
                "Volunteers counted and sorted the donations before packing labelled cartons that were ready for the community kitchen.",
                E("Orders counting and sorting before packing.", "counted and sorted", "before packing"),
                E("Includes the ready-for-kitchen result.", "ready for the community kitchen", "cartons for the kitchen"),
                interaction_type="summary",
                ordered=True,
            ),
            "a_choice": C(
                "assessment-a-costumes",
                "The team measured the actors, cut fabric to those measurements, and stitched the pieces into costumes.",
                "Which event occurred second?",
                "The team cut fabric to the measurements.",
                "The actors wore finished costumes.",
                "The pieces were stitched first.",
                "The team measured the stage lights.",
            ),
            "b_open": O(
                "assessment-b-relay-signs",
                "Learners drafted direction signs, checked each arrow on the actual path, and placed corrected signs before visitors arrived.",
                "Write an ordered summary that explains why checking mattered.",
                "Learners drafted signs, tested their arrows on the path, and displayed corrected versions, so visitors received accurate directions.",
                E("Sequences drafting, testing, and displaying.", "drafted signs", "tested their arrows", "displayed corrected"),
                E("Explains the accurate-directions result.", "visitors received accurate directions", "correct directions for visitors"),
                interaction_type="summary",
                ordered=True,
            ),
            "b_choice": C(
                "assessment-b-blankets",
                "Neighbours collected cloth, washed every piece, and then sewed the clean pieces into blankets.",
                "What happened just before sewing began?",
                "Every cloth piece was washed.",
                "The blankets were delivered.",
                "Neighbours collected finished blankets.",
                "The sewing tools were discarded.",
            ),
        },
    ),
    L(
        level_id="together_inference_and_reason",
        title="Infer how teams repair problems",
        focus="infer motives and justify a response with visible evidence",
        outcome="Infer why a teammate acts or which response will repair a problem, then support the conclusion with two relevant details.",
        skills=["reading.inference_reason", "writing.reason_answer"],
        episode_kind="comprehension_studio",
        anchor_slugs=["think", "write"],
        principle="Separate what the passage states from what it suggests, and join each conclusion to a visible clue with a clear reason.",
        connect_teaching="An inference is not a guess. It combines a stated detail with a reasonable explanation of a person's motive, feeling, or likely next action.",
        connect_passage="Ravi erased his own name from the only available task and wrote both partners' names beside it after noticing Mira had received no role.",
        connect_prompt="Use Ravi's change and Mira's missing role to infer his motive, then continue.",
        cases=[
            C(
                "poster-dispute",
                "Two designers argue over colours. The leader places both samples beside the event rules and asks which one is easier to read from far away.",
                "Why does the leader use the event rules?",
                "to shift the decision from personal preference to shared evidence",
                "to prove that neither designer should contribute",
                "to delay the poster until after the event",
                "to choose the colour used most recently",
            ),
            C(
                "quiet-builder",
                "During planning, Salim notices that Rupa has not spoken. He asks her to explain the model joint she tested earlier.",
                "What is Salim most likely trying to do?",
                "bring Rupa's useful knowledge into the group decision",
                "remove Rupa from the building team",
                "repeat a joint that already failed",
                "finish planning without any discussion",
            ),
            O(
                "missed-pass",
                "Leela misses a pass and looks down. Her teammate says, 'Your earlier passes reached me; try the shorter route this time.'",
                "Infer the teammate's purpose and justify it with two details.",
                "The teammate wants Leela to regain confidence because he recalls her earlier success and offers a practical adjustment instead of blaming her.",
                E("Infers restoring confidence as the purpose.", "regain confidence", "encourage Leela"),
                E("Uses both the earlier success and practical adjustment as evidence.", "earlier success", "practical adjustment"),
            ),
            O(
                "shared-scissors",
                "Only one pair of scissors remains. Dev keeps cutting while Ina waits, so she begins folding pieces that will be needed later.",
                "Why is Ina's choice helpful, and what should Dev do next?",
                "Ina keeps the project moving by completing another needed task; Dev should offer the scissors after his current cut so both can contribute fairly.",
                E("Explains how Ina keeps progress moving.", "keeps the project moving", "another needed task"),
                E("Proposes fair sharing as Dev's next action.", "offer the scissors", "both can contribute fairly"),
            ),
            O(
                "rehearsal-error",
                "The chorus enters too early twice. Instead of pointing at one singer, the group checks the conductor's signal and marks the entry together.",
                "What does the response reveal about the group, and why is it effective?",
                "The group values shared responsibility because it checks a common signal rather than blaming one singer, which directly addresses the repeated timing error.",
                E("Infers shared responsibility from the no-blame response.", "values shared responsibility", "rather than blaming"),
                E("Explains why checking the signal addresses the error.", "common signal", "addresses the timing error"),
            ),
            O(
                "queue-conflict",
                "Two volunteers both begin registering visitors while nobody gives badges. One pauses and suggests that they divide the jobs for ten minutes, then switch.",
                "Explain why the suggestion is likely to improve the welcome desk.",
                "Dividing and later switching jobs prevents duplicated registration, fills the missing badge role, and keeps the workload fair for both volunteers.",
                E("Explains how division removes duplication and fills the gap.", "prevents duplicated registration", "fills the missing badge role"),
                E("Explains how switching supports fairness.", "switching jobs", "workload fair"),
            ),
            O(
                "cracked-model",
                "A bridge model cracks during testing. The builder wants to hide it, but the recorder adds the crack to the results and asks the group to strengthen that joint.",
                "Infer the recorder's priority and support it with the response to the crack.",
                "The recorder prioritizes honest improvement because she documents the failure and turns it into a specific request to strengthen the weak joint.",
                E("Infers honest improvement as the priority.", "prioritizes honest improvement", "documents the failure"),
                E("Uses the request to strengthen the joint as evidence.", "strengthen the weak joint", "specific request"),
            ),
            O(
                "late-teammate",
                "Kamal arrives late with the missing chart. The group first asks whether he is all right, then quickly updates him on the presentation order.",
                "What two team values are shown, and which detail supports each one?",
                "The group shows care by checking Kamal's well-being and responsibility by updating him so the presentation can proceed smoothly.",
                E("Links checking well-being to care.", "shows care", "checking Kamal's well-being"),
                E("Links the update to shared responsibility.", "responsibility by updating", "presentation can proceed"),
            ),
            O(
                "unequal-credit",
                "The certificate lists only the speaker, although three others researched, illustrated, and checked the project. The speaker asks for all four names to be added.",
                "Infer why the speaker requests the change and explain its effect on trust.",
                "The speaker wants credit to match each person's contribution, and recognizing all four members protects trust by showing that hidden work also matters.",
                E("Infers fair recognition as the motive.", "credit to match", "each person's contribution"),
                E("Explains how recognition protects team trust.", "protects trust", "hidden work also matters"),
            ),
        ],
        misconception="The learner offers a sensible opinion but cannot connect it to the exact action, contrast, or consequence supplied in the visible passage.",
        remediation="Use a clue-therefore-conclusion frame, require two different passage details, and reject any reason that could be written without reading the scene.",
        assessment={
            "a_open": O(
                "assessment-a-spilled-paint",
                "A paint jar spills across the shared design. Nori admits she knocked it, fetches cloths, and asks how to redraw the covered section.",
                "Infer what Nori values and justify the inference with two actions.",
                "Nori values responsibility because she admits causing the spill and immediately helps clean and restore the damaged design.",
                E("Infers responsibility as the value.", "values responsibility", "takes responsibility"),
                E("Uses admission and repair actions as evidence.", "admits causing the spill", "helps clean and restore"),
            ),
            "a_choice": O(
                "assessment-a-vote",
                "After a tied vote, the chair asks each side to name one strength in the other proposal before voting again.",
                "Infer why the chair requests a strength first and cite the decision context.",
                "The chair wants both sides to consider evidence beyond personal preference because the first vote ended in a tie.",
                E("Infers a shift from preference to evidence.", "consider evidence", "beyond personal preference"),
                E("Uses the tied vote as the decision context.", "first vote ended in a tie", "tied vote"),
            ),
            "b_open": O(
                "assessment-b-tools",
                "Jaya finishes using the only ruler but sees Arif measuring with a torn paper strip. She passes him the ruler before decorating her page.",
                "Infer Jaya's priority and explain the likely team benefit.",
                "Jaya prioritizes shared progress because she delays decoration to give Arif the proper tool, allowing his essential measurement to continue accurately.",
                E("Infers shared progress as Jaya's priority.", "prioritizes shared progress", "delays decoration"),
                E("Explains the accuracy and progress benefit.", "measurement to continue accurately", "proper tool"),
            ),
            "b_choice": O(
                "assessment-b-feedback",
                "The captain says, 'The opening is clear; now slow the final line so everyone can follow it.'",
                "Explain why the feedback is constructive and support both parts of your answer.",
                "The feedback is constructive because it names the clear opening as a success and gives one specific improvement for the final line.",
                E("Identifies the clear opening as specific positive evidence.", "clear opening", "as a success"),
                E("Identifies slowing the final line as a specific improvement.", "slow the final line", "specific improvement"),
            ),
        },
    ),
    L(
        level_id="together_preposition_sentences",
        title="Place helpers in clear sentences",
        focus="choose precise prepositions and construct complete location sentences",
        outcome="Use visible spatial relationships to select an accurate preposition and write a complete sentence with a clear subject, verb, and location phrase.",
        skills=["grammar.prepositions", "writing.complete_sentence"],
        episode_kind="language_lab",
        anchor_slugs=["learn", "write"],
        principle="Locate the reference object first, test the direction or position word, and place the full phrase after a complete subject and verb.",
        connect_teaching="A preposition explains a relationship, not an object by itself. A complete location sentence names what is placed, where it is, and its reference point.",
        connect_passage="The first-aid box rests on the shelf between the water jar and the folded towels.",
        connect_prompt="Identify the reference objects for on and between, then continue.",
        cases=[
            C(
                "badge-table",
                "The team badge is under the glass table, directly below the centre support.",
                "Which preposition states the badge's relation to the table?",
                "under",
                "through",
                "beside",
                "beyond",
            ),
            C(
                "cones-gate",
                "Two orange cones stand on opposite sides of the school gate, with the gate in the middle.",
                "Which word best completes: The gate is ___ the cones?",
                "between",
                "inside",
                "above",
                "across",
            ),
            O(
                "bookshelf-basket",
                "A green basket sits beside the bookshelf, and a box of labels rests inside the basket.",
                "Write two complete sentences using beside and inside accurately.",
                "The green basket sits beside the bookshelf. The box of labels rests inside the green basket.",
                E("Uses beside for the basket and bookshelf relationship.", "basket sits beside the bookshelf", "beside the bookshelf"),
                E("Uses inside for the labels and basket relationship.", "labels rests inside", "inside the green basket"),
                interaction_type="short_text",
            ),
            O(
                "mural-ladder",
                "The ladder leans against the left wall. Three paint tins are lined up in front of its lowest step.",
                "Describe both positions in complete sentences with precise prepositions.",
                "The ladder leans against the left wall. The three paint tins stand in front of the ladder's lowest step.",
                E("Uses against to locate the ladder.", "ladder leans against", "against the left wall"),
                E("Uses in front of to locate the paint tins.", "tins stand in front of", "in front of the lowest step"),
                interaction_type="short_text",
            ),
            O(
                "courtyard-benches",
                "A notice pole stands in the centre. One bench is to its left, and another bench is to its right.",
                "Write one complete sentence that places the pole relative to both benches.",
                "The notice pole stands between the two benches in the centre of the courtyard.",
                E("Uses between for the pole and benches.", "pole stands between", "between the two benches"),
                E("Writes a complete sentence with a clear location.", "centre of the courtyard", "notice pole stands"),
                interaction_type="short_text",
            ),
            O(
                "parcel-counter",
                "A returned parcel is on the counter. The signed delivery list is pinned above it on the wall.",
                "Describe the list and parcel using on and above in two linked sentences.",
                "The returned parcel is on the counter. The signed list is pinned above the parcel on the wall.",
                E("Uses on for the parcel and counter.", "parcel is on the counter", "on the counter"),
                E("Uses above for the list and parcel.", "list is pinned above the parcel", "above the parcel"),
                interaction_type="short_text",
            ),
            O(
                "garden-path",
                "A narrow path runs through the herb beds. The tool shed stands beyond the final bed near the fence.",
                "Write a clear direction sentence using through and beyond.",
                "Walk through the herb beds along the narrow path; the tool shed stands beyond the final bed near the fence.",
                E("Uses through for movement along the beds.", "through the herb beds", "path runs through"),
                E("Uses beyond for the shed after the final bed.", "shed stands beyond", "beyond the final bed"),
                interaction_type="short_text",
            ),
            O(
                "stage-curtain",
                "The music stand is behind the blue curtain. A coil of cable lies beneath the stand.",
                "Locate both objects in complete sentences without changing the reference points.",
                "The music stand is behind the blue curtain. The cable coil lies beneath the music stand.",
                E("Uses behind for the stand and curtain.", "stand is behind the blue curtain", "behind the curtain"),
                E("Uses beneath for the cable and stand.", "cable coil lies beneath", "beneath the music stand"),
                interaction_type="short_text",
            ),
            O(
                "team-circle",
                "Six learners form a circle around a floor map. Their note cards are spread across the map's edge.",
                "Write one complete sentence for each spatial relationship.",
                "The six learners stand around the floor map. Their note cards are spread across the edge of the map.",
                E("Uses around for the learners and map.", "learners stand around", "around the floor map"),
                E("Uses across for the cards and map edge.", "cards are spread across", "across the edge"),
                interaction_type="short_text",
            ),
        ],
        misconception="The learner names a plausible position word without checking the reference object, or writes only a location fragment instead of a complete sentence.",
        remediation="Mark the located object and reference object in different colours, draw an arrow for their relationship, and expand the phrase into a subject-verb-location sentence.",
        assessment={
            "a_open": O(
                "assessment-a-equipment",
                "The whistle hangs above the equipment cupboard, while the attendance folder lies inside its top drawer.",
                "Write two complete sentences describing both locations.",
                "The whistle hangs above the equipment cupboard. The attendance folder lies inside the cupboard's top drawer.",
                E("Uses above for the whistle and cupboard.", "whistle hangs above", "above the equipment cupboard"),
                E("Uses inside for the folder and drawer.", "folder lies inside", "inside the top drawer"),
                interaction_type="short_text",
            ),
            "a_choice": C(
                "assessment-a-flags",
                "The welcome sign stands in the middle, with one flag on each side.",
                "Which word completes: The sign stands ___ the flags?",
                "between",
                "under",
                "through",
                "outside",
            ),
            "b_open": O(
                "assessment-b-toolbox",
                "A red toolbox rests beneath the workbench. Safety goggles are placed on the bench directly above it.",
                "Describe both positions in complete sentences.",
                "The red toolbox rests beneath the workbench. The safety goggles are placed on the bench above the toolbox.",
                E("Uses beneath for the toolbox and bench.", "toolbox rests beneath", "beneath the workbench"),
                E("Uses on or above accurately for the goggles.", "goggles are placed on", "above the toolbox"),
                interaction_type="short_text",
            ),
            "b_choice": C(
                "assessment-b-tunnel",
                "The runners enter one end of the practice tunnel and emerge from the other end.",
                "Which preposition describes their movement?",
                "through",
                "between",
                "above",
                "beside",
            ),
        },
    ),
    L(
        level_id="together_future_responses",
        title="Promise the next team action",
        focus="use future tense and answer practical questions completely",
        outcome="Use will with an accurate base verb to state a future team action and answer what, who, or why questions in complete English.",
        skills=["grammar.tense_usage", "writing.short_answer"],
        episode_kind="language_lab",
        anchor_slugs=["write"],
        principle="Separate the current problem from the planned action, use will plus a base verb, and include the detail requested by the question.",
        connect_teaching="A future response tells what is planned but has not happened yet. After will, the action word stays in its base form.",
        connect_passage="The art sheets are still loose. Meena will clip them together before the group carries them outside.",
        connect_prompt="Find the current problem and the future action, then continue.",
        cases=[
            C(
                "wet-court",
                "Rain has left a wet patch near the goal. The players will mark it and ask the caretaker for a mop.",
                "Which action is planned for later?",
                "The players will mark the wet patch.",
                "The rain marked the goal yesterday.",
                "The players are ignoring the wet patch.",
                "The caretaker has already dried everything.",
            ),
            C(
                "missing-labels",
                "The display boxes have no labels. Sana says, 'I will write them after lunch.'",
                "Which verb form correctly follows will in Sana's plan?",
                "write",
                "wrote",
                "writes",
                "writing",
            ),
            O(
                "broken-handle",
                "The collection basket has a loose handle. Iqbal has string, and Tara knows how to tie a firm knot.",
                "What will each teammate do next? Answer in two complete sentences.",
                "Iqbal will bring the string to the basket. Tara will tie the loose handle with a firm knot.",
                E("States Iqbal's future action with will and bring.", "Iqbal will bring", "bring the string"),
                E("States Tara's future action with will and tie.", "Tara will tie", "tie the loose handle"),
                interaction_type="short_text",
            ),
            O(
                "visitor-route",
                "Tomorrow, new learners will visit the science room. The current route sign points toward a locked door.",
                "How will the guide team prevent confusion? Give a complete short answer.",
                "The guide team will replace the incorrect sign and will test the new route before the visitors arrive.",
                E("Uses future tense for replacing the sign.", "will replace", "incorrect sign"),
                E("Includes testing the route before visitors arrive.", "will test", "before the visitors arrive"),
                interaction_type="short_text",
            ),
            O(
                "practice-absence",
                "Rohan will miss tomorrow's practice because of an appointment. He has already sent his notes to the captain.",
                "What will the captain do with the notes, and why?",
                "The captain will share Rohan's notes during practice so the team can use his ideas even while he is absent.",
                E("States a future action using will share.", "captain will share", "share Rohan's notes"),
                E("Explains that the team can still use his ideas.", "team can use his ideas", "while he is absent"),
                interaction_type="short_text",
            ),
            O(
                "seed-fair",
                "The eco-club has twelve seed packets and four garden groups. Tomorrow they must distribute the packets fairly.",
                "What will the club do, and what result will that create?",
                "The club will give three packets to each group, so every group will begin with an equal share.",
                E("States the fair future distribution.", "will give three packets", "to each group"),
                E("States the equal-share result.", "every group will begin", "equal share"),
                interaction_type="short_text",
            ),
            O(
                "late-delivery",
                "The recycled paper will arrive after the poster session begins. The team has spare card in the cupboard.",
                "How will the team adjust without stopping the session?",
                "The team will start the first posters on spare card and will use the recycled paper for the later designs.",
                E("States the immediate future use of spare card.", "will start", "on spare card"),
                E("States the later use of recycled paper.", "will use the recycled paper", "later designs"),
                interaction_type="short_text",
            ),
            O(
                "new-member",
                "A new member will join the reading group on Monday. She does not know how the roles rotate.",
                "What will the group explain first, and how will that help her?",
                "The group will explain the role chart first, which will help the new member choose and prepare for her opening job.",
                E("Uses future tense for explaining the role chart.", "will explain", "role chart first"),
                E("Explains the preparation benefit.", "will help", "prepare for her opening job"),
                interaction_type="short_text",
            ),
            O(
                "empty-bottle",
                "After the match, the water bottle rack is empty and several players are still waiting. A refill tap is beside the office.",
                "Write a two-action future response that solves the problem.",
                "Two volunteers will carry the bottles to the refill tap, and another teammate will tell the waiting players when water is ready.",
                E("States the bottle-refill action in future tense.", "will carry the bottles", "refill tap"),
                E("States the communication action in future tense.", "will tell the waiting players", "water is ready"),
                interaction_type="short_text",
            ),
        ],
        misconception="The learner describes a present fact instead of the next action, changes the verb after will, or gives a fragment that misses the requested reason.",
        remediation="Draw a now-next line, place the unsolved fact under now, and rehearse will plus base verb plus required detail before writing the complete response.",
        assessment={
            "a_open": O(
                "assessment-a-library-cart",
                "The return cart is full, and another class will bring books in ten minutes. Two monitors are free now.",
                "What will the monitors do, and why?",
                "The monitors will shelve the current books now so the cart will have space for the next class's returns.",
                E("Uses future tense for shelving the books.", "monitors will shelve", "current books"),
                E("Explains the future space benefit.", "cart will have space", "next class's returns"),
                interaction_type="short_text",
            ),
            "a_choice": C(
                "assessment-a-banner",
                "The banner is unfinished. After recess, the artists will ___ the final border.",
                "Which verb correctly completes the future plan?",
                "paint",
                "painted",
                "paints",
                "painting",
            ),
            "b_open": O(
                "assessment-b-shade",
                "The outdoor reading table receives strong afternoon sun. The team has a cloth canopy and four poles.",
                "How will the team improve the reading place?",
                "The team will raise the canopy over the table, and the cloth will provide shade during afternoon reading.",
                E("States the planned action with will raise.", "team will raise", "canopy over the table"),
                E("States the future shade result.", "cloth will provide shade", "afternoon reading"),
                interaction_type="short_text",
            ),
            "b_choice": C(
                "assessment-b-invitation",
                "The invitation lacks the meeting time. Neha will add it before printing.",
                "Which phrase identifies the future action?",
                "will add it",
                "lacks the meeting time",
                "before printing",
                "the invitation",
            ),
        },
    ),
    L(
        level_id="together_team_procedure",
        title="Build a fair team procedure",
        focus="order instructions and write an actionable cooperative procedure",
        outcome="Arrange necessary actions in a logical order and write a complete procedure with roles, sequence markers, and a check for fair participation.",
        skills=["grammar.sentence_order", "writing.procedure"],
        episode_kind="application_mission",
        anchor_slugs=["learn", "write"],
        principle="Start with preparation, place dependent actions after what they need, assign clear roles, and finish with a result or fairness check.",
        connect_teaching="A useful procedure lets another team act without guessing. Each step uses an action verb and appears only after its materials or information are ready.",
        connect_passage="To prepare a shared reading display, first list the books, next divide the labels, then attach each checked label, and finally review the whole shelf together.",
        connect_prompt="Notice why listing comes before labelling and why review comes last, then continue.",
        cases=[
            C(
                "seed-table",
                "Steps: share the tools; check every pot; place soil in the pots; assign one row to each pair.",
                "Which order creates a workable planting start?",
                "share tools, assign rows, place soil, check pots",
                "check pots, place soil, assign rows, hide tools",
                "place soil, finish planting, assign rows, share tools",
                "assign rows, check empty pots, remove soil, stop",
            ),
            C(
                "welcome-desk",
                "The team must prepare name cards before visitors arrive and hand each card to the correct person at entry.",
                "Which action must occur before cards are handed out?",
                "The team checks names and arranges the cards.",
                "The visitors return the cards after leaving.",
                "The team closes the entrance early.",
                "Every card is mixed into one pile at the door.",
            ),
            O(
                "sports-kit",
                "A group must return balls, cones, and bibs after practice. There are three baskets and a checklist.",
                "Write four ordered steps that assign roles and verify the complete kit.",
                "First assign one equipment type to each pair. Next sort the items into labelled baskets. Then count them against the checklist. Finally report and find anything missing.",
                E("Orders role assignment before sorting and counting.", "First assign", "Next sort", "Then count"),
                E("Ends with a check and response to missing equipment.", "against the checklist", "find anything missing"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "class-garden",
                "The class has one watering can, four beds, and eight helpers. Each bed needs equal attention without a queue around the can.",
                "Design a fair watering procedure with roles, order, and a completion check.",
                "First pair helpers with one bed each. Next one runner fills the can while each pair loosens soil. Then pairs water in turn. Finally mark every completed bed on a shared chart.",
                E("Assigns fair roles and prepares beds before watering.", "pair helpers", "runner fills", "loosens soil"),
                E("Includes turn-taking and a completion check.", "water in turn", "mark every completed bed"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "story-circle",
                "Five learners will create one story. Each has a character idea, but the final story needs a single problem and ending.",
                "Write a procedure that includes every idea without producing five separate stories.",
                "First list all characters. Next agree on one shared problem. Then assign each learner one event that moves that problem forward. Finally read the joined story and revise the ending together.",
                E("Combines ideas around one shared problem and linked events.", "one shared problem", "one event that moves"),
                E("Ends with joining and revising the story together.", "read the joined story", "revise the ending together"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "relief-packets",
                "Volunteers must pack soap, towels, and water bottles into ten identical relief packets. Supplies are in separate cartons.",
                "Create an efficient procedure that prevents missing or unequal items.",
                "First count each supply for ten packets. Next create separate packing stations. Then move every packet through all stations. Finally compare each packet with the three-item checklist.",
                E("Begins with counting and organized packing stations.", "count each supply", "separate packing stations"),
                E("Uses a final checklist to prevent missing items.", "compare each packet", "three-item checklist"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "community-map",
                "Four pairs surveyed different lanes. They must combine landmarks into one map without duplicating the bus stop or clinic.",
                "Write the merging procedure from sharing notes to checking the final map.",
                "First each pair marks its lane on tracing paper. Next overlay the sheets and agree on shared landmarks. Then copy one version onto the main map. Finally compare it with every survey note.",
                E("Orders separate marking before overlaying and agreeing.", "marks its lane", "overlay the sheets", "agree on shared landmarks"),
                E("Ends with one copied map and a complete evidence check.", "copy one version", "compare it with every survey note"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "book-repair",
                "The library team has torn books, tape, clean covers, and a condition log. Repairs must be safe and recorded.",
                "Give a four-step repair procedure with a role split and final check.",
                "First one pair records each damaged page. Next another pair tapes tears carefully. Then a third pair fits clean covers. Finally the recorder checks every repair and updates the condition log.",
                E("Orders recording before repair and assigns separate roles.", "records each damaged page", "another pair tapes", "third pair fits"),
                E("Ends with checking repairs and updating the log.", "checks every repair", "updates the condition log"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            O(
                "team-decision",
                "A project group has three good topics but only one afternoon. Members want a fair way to choose and then divide the work.",
                "Write an ordered decision procedure that protects every member's voice.",
                "First let each member explain one topic benefit. Next compare all topics with the time limit. Then vote after questions are answered. Finally assign research, design, and checking roles fairly.",
                E("Includes equal explanation and comparison before voting.", "each member explain", "compare all topics", "vote after questions"),
                E("Ends with fair, specific role assignment.", "assign research", "design, and checking roles fairly"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
        ],
        misconception="The learner lists useful actions but puts checking before work is complete, omits role ownership, or writes commands that cannot be followed in sequence.",
        remediation="Sort action cards into prepare, do, and verify columns, add a named role to each action, and test whether a new team could follow the procedure without questions.",
        assessment={
            "a_open": O(
                "assessment-a-poster-packs",
                "Six groups need equal poster packs containing paper, two markers, and one ruler. Supplies are mixed in a cupboard.",
                "Write an ordered packing procedure with a fairness check.",
                "First count supplies for all six groups. Next make six labelled spaces. Then place paper, two markers, and one ruler in each space. Finally compare every pack with the same list.",
                E("Orders counting and labelled spaces before packing.", "count supplies", "six labelled spaces", "Then place"),
                E("Uses an equal-item final check.", "compare every pack", "same list"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            "a_choice": C(
                "assessment-a-seed-order",
                "The team must label pots, add soil, plant seeds, and record each planted pot.",
                "Which action should occur before seeds are planted?",
                "The pots should be labelled and filled with soil.",
                "Every planted pot should be emptied.",
                "The final record should be erased.",
                "Seeds should be counted after plants grow.",
            ),
            "b_open": O(
                "assessment-b-stage-reset",
                "After a play, costumes, props, and cables must return to separate storage places before the hall closes.",
                "Create a safe team reset procedure with roles and verification.",
                "First assign costume, prop, and cable teams. Next each team sorts and returns its items. Then the cable team checks clear walkways. Finally the leader checks all three storage lists.",
                E("Assigns categories before sorting and returning items.", "assign costume", "prop, and cable teams", "sorts and returns"),
                E("Includes safety and final storage checks.", "checks clear walkways", "checks all three storage lists"),
                interaction_type="paragraph_text",
                ordered=True,
            ),
            "b_choice": C(
                "assessment-b-interview-order",
                "A team will interview a gardener, but it still needs questions, roles, and a way to record answers.",
                "Which first step best prepares the interview?",
                "Agree on questions and assign interviewer and recorder roles.",
                "Write the report before meeting the gardener.",
                "Delete every question to save time.",
                "Ask all members to speak at once.",
            ),
        },
    ),
]


QUALITY_PACKS = {
    "together_poem_message": {
        "extra_cases": [
            N(
                "well-rope",
                "One hand cannot lift the full water bucket. Four hands pull the rope evenly, and the bucket rises without spilling.",
                "Explain what the four hands represent and state the larger message.",
                "The four hands represent shared strength, and the rising bucket shows that coordinated work can overcome a heavy task.",
                "four hands represent shared strength",
                "coordinated work can overcome a heavy task",
            ),
            N(
                "quilt-pieces",
                "A single cloth square warms no one, but many different squares stitched edge to edge become a blanket for the night shelter.",
                "Interpret the cloth image and give its central idea.",
                "The joined squares show that small different contributions can combine into useful care for the whole group.",
                "small different contributions",
                "useful care for the whole group",
            ),
            N(
                "sandbag-wall",
                "Each sandbag seems ordinary. Placed side by side before the storm, the bags form a wall that keeps water from the clinic door.",
                "State the image meaning and support the teamwork message.",
                "The side-by-side bags stand for people combining ordinary efforts, and together those efforts protect an important shared place.",
                "people combining ordinary efforts",
                "protect an important shared place",
            ),
            N(
                "drum-circle",
                "One beat sounds lonely in the hall. When the drum, claps, and ankle bells keep the same pulse, dancers enter with confidence.",
                "Explain the contrast and the cooperation idea.",
                "The lonely beat becomes a guiding rhythm when different sounds coordinate, showing that varied roles can support one successful performance.",
                "different sounds coordinate",
                "varied roles support one successful performance",
            ),
            N(
                "path-stones",
                "A traveller cannot cross the muddy patch on one stone. Villagers place a line of stones, and every child reaches the bus safely.",
                "Transfer the poetic-image skill to this village scene.",
                "The line of stones represents linked help, and the safe crossing suggests that cooperation creates a path others can use.",
                "line of stones represents linked help",
                "cooperation creates a path others can use",
            ),
        ],
        "support_cases": [
            R(
                "basket-handles",
                "Two separate handles sag, but when both are held together the fruit basket stays level.",
                "Name the literal change first, then explain the shared-help idea.",
                "Holding both handles keeps the basket level, and the image suggests that balanced cooperation prevents the load from falling.",
                "both handles keeps the basket level",
                "balanced cooperation prevents the load from falling",
                worked_reasoning="Separate what happens to the basket from what the paired handles can represent; the physical result supports the larger idea.",
                next_step="write one sentence for the image and one for its teamwork meaning.",
            ),
            R(
                "chalk-arrows",
                "One chalk arrow ends at a wall. Several arrows drawn by the route team guide visitors around the corner to the health desk.",
                "Correct the mistake 'the poem is only about chalk' by using the result.",
                "The arrows do more than mark chalk lines; together they represent shared guidance that helps visitors reach the health desk.",
                "arrows represent shared guidance",
                "helps visitors reach the health desk",
                worked_reasoning="The object is chalk, but the meaningful result is successful guidance; connect that result to people coordinating information.",
                next_step="replace the literal-only answer with an image meaning and its supported message.",
            ),
            R(
                "roof-tiles",
                "One roof tile leaves a wide gap. Rows of fitted tiles keep the reading room dry during heavy rain.",
                "Use both the single-tile problem and the fitted-row result.",
                "A single tile cannot protect the room, while fitted rows show that connected contributions create dependable shelter.",
                "single tile cannot protect the room",
                "connected contributions create dependable shelter",
                worked_reasoning="Contrast the weak single part with the successful joined parts before stating the main cooperation message.",
                next_step="write the contrast without adding a weather fact not given here.",
            ),
            R(
                "thread-knot",
                "Loose threads slide apart. Twisted into one cord, they hold the notice board firmly between two poles.",
                "Repair an answer that says only 'cord is strong.'",
                "The cord is strong because separate threads join, so the image shows that unity can make a group dependable.",
                "separate threads join",
                "unity can make a group dependable",
                worked_reasoning="The missing idea is how the strength is created; trace loose threads to joined cord and then infer unity.",
                next_step="include both the change and the message in a complete response.",
            ),
            R(
                "window-lights",
                "One window light marks a single home. Every window lit along the lane helps the returning rescue team find the village.",
                "Give a final image interpretation with one precise result clue.",
                "The many window lights represent neighbours acting together, and their bright lane guides the rescue team home.",
                "window lights represent neighbours acting together",
                "bright lane guides the rescue team home",
                worked_reasoning="Use the repeated lights as the image and the team's safe return as the clue that proves their shared value.",
                next_step="answer independently in fresh wording while keeping both required ideas.",
            ),
        ],
    },
    "together_words_in_context": {
        "extra_cases": [
            N(
                "steadfast-rope",
                "The old rope stays firm through three practice pulls and never loosens at the knot. The coach calls it steadfast.",
                "Infer steadfast and use it in a new teamwork sentence.",
                "Steadfast means remaining firm and dependable; a steadfast teammate keeps helping even when practice becomes tiring.",
                "remaining firm and dependable",
                "steadfast teammate keeps helping",
            ),
            N(
                "nimble-sorter",
                "Ritu quickly sorts mixed screws into four cups without dropping any. Her nimble fingers keep the repair team moving.",
                "Explain nimble from the action and create another fitting use.",
                "Nimble means quick and skilful in movement; nimble hands can tie the small seed packets neatly.",
                "quick and skilful in movement",
                "nimble hands can tie seed packets",
            ),
            N(
                "scarce-water",
                "Only one jug remains for six garden beds, so the team measures every cup. Water is scarce this afternoon, and team is a collective noun.",
                "State the meaning of scarce and explain why team is a collective noun.",
                "Scarce means available in a very small amount; team is a collective noun because it names the gardeners together.",
                "available in a very small amount",
                "team is a collective noun",
            ),
            N(
                "patient-guide",
                "The class asks several route questions, and the guide repeats each answer slowly without annoyance. Everyone calls her patient; class is a collective noun.",
                "Infer patient and identify the collective noun in the story.",
                "Patient means calm while waiting or explaining; class is a collective noun because it names all the learners together.",
                "calm while waiting or explaining",
                "class is a collective noun",
            ),
            N(
                "sturdy-crate",
                "A bunch of crates holds the books through a bumpy cart ride without bent corners. The crates are sturdy, and bunch is a collective noun.",
                "Explain sturdy and show why bunch is the collective noun.",
                "Sturdy means strong enough to resist damage; bunch is a collective noun because it names several crates together.",
                "strong enough to resist damage",
                "bunch is a collective noun",
            ),
        ],
        "support_cases": [
            R(
                "glimmer-clue",
                "At dusk, a faint glimmer appears through the tent cloth, just bright enough to show the doorway.",
                "Use the brightness clue to explain glimmer, then write a new example.",
                "A glimmer is a small weak light; a glimmer from the torch showed where the key had fallen.",
                "small weak light",
                "glimmer from the torch",
                worked_reasoning="Ignore the tent topic and use the words faint and just bright enough; those clues set the strength of the light.",
                next_step="state the meaning and test it in a different setting.",
            ),
            R(
                "weary-clue",
                "After carrying boxes up four flights, Jai walks slowly, lowers his shoulders, and asks for a rest. He feels weary.",
                "Correct the guess 'weary means busy' with two visible clues.",
                "Weary means very tired, as shown by Jai walking slowly and asking to rest after the climb.",
                "weary means very tired",
                "walking slowly and asking to rest",
                worked_reasoning="Match the target word to the body's change and the request for rest; being busy alone does not explain both clues.",
                next_step="write the corrected meaning with the two supporting details.",
            ),
            R(
                "precious-clue",
                "The class wraps one old letter carefully, keeps it in a dry box, and records who may handle it because it is precious.",
                "Explain precious without merely repeating 'old.'",
                "Precious means highly valued and carefully protected; the handling rules show that the letter matters to the class.",
                "highly valued and carefully protected",
                "letter matters to the class",
                worked_reasoning="Age is background; careful wrapping, dry storage, and handling rules reveal value and protection.",
                next_step="connect the meaning to an action that proves the value.",
            ),
            R(
                "swift-clue",
                "The messenger crosses the courtyard before the second bell and returns almost at once. Her movement is swift.",
                "Distinguish swift from careless and use it correctly.",
                "Swift means very fast, not careless; the swift runner delivered the note quickly without losing it.",
                "swift means very fast",
                "delivered the note quickly without losing it",
                worked_reasoning="The time clues prove speed, while the safe return shows that speed does not require careless action.",
                next_step="give the meaning and a new sentence that keeps speed and control.",
            ),
            R(
                "fragile-clue",
                "Workers place soft cloth around the clay model and carry it with both hands because one small knock could crack it.",
                "Use the risk clue to explain fragile in a fresh sentence.",
                "Fragile means easily damaged; the team marked the fragile model so every carrier would handle it gently.",
                "fragile means easily damaged",
                "handle it gently",
                worked_reasoning="The possible crack is the decisive clue; the soft cloth and two-hand carry show the response to that risk.",
                next_step="write one meaning statement and one accurate new use.",
            ),
        ],
    },
    "together_event_chain": {
        "extra_cases": [
            N(
                "clinic-shelves",
                "Volunteers count medicine boxes, group them by label colour, place each group on a marked shelf, and ask the nurse to verify the arrangement.",
                "Summarize the four-stage chain without losing the final check.",
                "The volunteers first count the boxes, then group and shelve them by labels, and finally have the nurse verify the arrangement.",
                "count then group and shelve",
                "nurse verifies the arrangement",
                ordered=True,
            ),
            N(
                "rain-barrel",
                "A club clears leaves from a gutter, joins a pipe to a barrel, waits through one shower, and measures the collected water for the garden.",
                "Write an ordered summary from preparation to result.",
                "The club clears the gutter before connecting the barrel, then tests it in rain and measures the water collected for the garden.",
                "clears gutter before connecting barrel",
                "tests then measures collected water",
                ordered=True,
            ),
            N(
                "book-drive",
                "Learners collect donated books, remove damaged copies, sort the usable books by reading level, and deliver labelled bundles to three reading corners.",
                "Condense the event chain into one accurate summary.",
                "Learners collect and check the books, sort usable copies by level, and deliver labelled bundles to the reading corners.",
                "collect and check the books",
                "sort then deliver labelled bundles",
                ordered=True,
            ),
            N(
                "shade-frame",
                "The team measures the bench, cuts bamboo to the recorded lengths, ties a frame, stretches cloth across it, and checks that the shade covers every seat.",
                "Summarize the building sequence and its completion check.",
                "The team measures before cutting bamboo, builds and covers the frame, and ends by checking shade across every seat.",
                "measures before cutting bamboo",
                "checks shade across every seat",
                ordered=True,
            ),
            N(
                "seed-exchange",
                "Families list spare seeds, volunteers compare the lists, matching families trade packets, and the recorder marks each completed exchange.",
                "Transfer sequence summarizing to the seed exchange.",
                "After families list spare seeds, volunteers find matches, the families exchange packets, and the recorder marks each trade complete.",
                "list seeds before finding matches",
                "recorder marks each trade complete",
                ordered=True,
            ),
        ],
        "support_cases": [
            R(
                "kite-repair",
                "A torn kite is inspected, a matching paper patch is cut, glue is spread, and the patch is pressed flat before a test flight.",
                "Place inspection, repair, and testing in the correct order.",
                "The kite is inspected first, patched next, and tested only after the paper has been pressed flat.",
                "kite inspected first",
                "tested only after patch pressed flat",
                worked_reasoning="Time words are absent, so use cause: the team must find the tear before patching and finish the patch before testing.",
                next_step="write the chain with clear order markers.",
                ordered=True,
            ),
            R(
                "notice-board",
                "The class drafts a notice, checks the date with the office, corrects one digit, prints copies, and pins them at both gates.",
                "Repair a summary that puts printing before the date check.",
                "The class drafts and verifies the notice before correcting it, printing copies, and posting them at both gates.",
                "verifies notice before correcting it",
                "printing before posting at both gates",
                worked_reasoning="The corrected digit must appear in the copies, so checking and correction necessarily come before printing and posting.",
                next_step="rewrite the summary so the dependency is preserved.",
                ordered=True,
            ),
            R(
                "water-test",
                "A jar is rinsed, pond water is collected, a test strip is dipped, its colour is compared with a chart, and the result is recorded.",
                "Keep every essential stage while removing minor wording.",
                "After rinsing the jar and collecting water, the group tests the sample, compares the colour, and records the result.",
                "rinsing and collecting before testing",
                "compares colour then records result",
                worked_reasoning="Group preparation together, but do not omit comparison because it turns the strip colour into a usable result.",
                next_step="produce a concise chain with the interpretation step intact.",
                ordered=True,
            ),
            R(
                "lost-key",
                "A key is reported missing, volunteers retrace the morning route, one spots it under a mat, and the office logs its return to the owner.",
                "Explain why finding cannot be the first event in the summary.",
                "The missing-key report starts the search, the route check leads to the key, and the office records its return last.",
                "report starts the search",
                "office records return last",
                worked_reasoning="The search has a trigger and the return has a record; starting at the discovery would hide the cause of the search.",
                next_step="write beginning, discovery, and closure in order.",
                ordered=True,
            ),
            R(
                "lamp-check",
                "Workers replace a broken corridor bulb, switch on the circuit, walk to the far end, and record whether the full path is bright.",
                "Write a final independent summary with the verification stage.",
                "Workers replace the bulb, restore power, inspect the whole corridor, and record whether the path is fully lit.",
                "replace bulb then restore power",
                "inspect corridor and record result",
                worked_reasoning="Installation is not the end; the walk and record show whether the repair works along the complete route.",
                next_step="summarize all action stages without adding an unseen fault.",
                ordered=True,
            ),
        ],
    },
    "together_inference_and_reason": {
        "extra_cases": [
            N(
                "quiet-saw",
                "Mohan stops sawing when the reading circle begins beside the workshop and moves the wood cutting to the rear yard.",
                "Infer what Mohan values and justify it from his change.",
                "Mohan values the readers' concentration because he moves the noisy work away when their circle begins.",
                "values the readers' concentration",
                "moves noisy work away",
            ),
            N(
                "shared-umbrella",
                "Tia reaches the gate first, notices a younger child without cover, and waits so they can walk under her wide umbrella together.",
                "What quality does Tia show, and which clue proves it?",
                "Tia shows consideration because she gives up a faster departure to share shelter with the younger child.",
                "Tia shows consideration",
                "gives up faster departure to share shelter",
            ),
            N(
                "tool-return",
                "Aarav needs the only spanner again tomorrow, yet he returns it to the common cabinet before leaving and writes his next booking on the sheet.",
                "Infer why Aarav returns the tool instead of keeping it.",
                "Aarav respects shared access because returning and booking the spanner lets others use it fairly tonight.",
                "respects shared access",
                "lets others use it fairly",
            ),
            N(
                "extra-seat",
                "The bus group has counted every seat. When an injured player arrives, two children move their bags and sit closer without being asked.",
                "Infer the children's goal and support it with the voluntary action.",
                "The children want the injured player included, shown by making room immediately without waiting for an instruction.",
                "want the injured player included",
                "making room without instruction",
            ),
            N(
                "garden-credit",
                "The prize card names only Neel, but he asks the judge to add the classmates who watered seedlings during his illness.",
                "Transfer inference to explain Neel's request and its fairness.",
                "Neel values honest credit because he makes sure the classmates whose work sustained the garden are also recognized.",
                "values honest credit",
                "classmates are also recognized",
            ),
        ],
        "support_cases": [
            R(
                "closed-window",
                "Before painting, Lata closes the library window and covers the nearby books, although nobody reminds her.",
                "Use the preventive actions to infer Lata's concern.",
                "Lata cares about protecting the books because she blocks paint dust and covers them before work starts.",
                "cares about protecting the books",
                "blocks dust and covers them",
                worked_reasoning="Do not label Lata merely careful; identify what her two actions protect and connect that object to the inferred value.",
                next_step="state the value and cite both preventive clues.",
            ),
            R(
                "queue-marker",
                "Imran notices two visitors miss the faint queue line, so he places a clear marker and stands aside instead of taking the first place.",
                "Correct the unsupported inference that Imran wants attention.",
                "Imran wants the queue to be fair and clear because he improves the marker and does not claim the first place.",
                "wants queue fair and clear",
                "does not claim first place",
                worked_reasoning="His action benefits all visitors and costs him an advantage, which contradicts the attention-seeking guess.",
                next_step="replace the guess with a reason tied to both actions.",
            ),
            R(
                "saved-portion",
                "The lunch team sets aside one labelled portion before serving because a volunteer is returning late from the clinic.",
                "Infer the team's purpose without inventing a medical detail.",
                "The team wants the late volunteer to receive a fair meal, so it reserves a labelled portion before serving others.",
                "late volunteer receives fair meal",
                "reserves portion before serving",
                worked_reasoning="The label and timing prove planned inclusion; the passage gives no reason to diagnose or describe the clinic visit.",
                next_step="give the supported purpose and omit unseen causes.",
            ),
            R(
                "recount-votes",
                "Priya's choice appears to win by one vote, but she requests a recount after noticing two folded slips stuck together.",
                "Explain why her action shows fairness rather than doubt alone.",
                "Priya values an accurate result because she risks losing her advantage to make sure every vote is counted separately.",
                "values an accurate result",
                "risks advantage for every vote",
                worked_reasoning="Compare her current advantage with the recount request; accepting that risk reveals commitment to accurate counting.",
                next_step="link the risk she accepts to the value you infer.",
            ),
            R(
                "drying-rack",
                "Ravi finishes his poster early but leaves space on the drying rack for three groups still carrying wet work.",
                "Write the inference and the decisive clue independently.",
                "Ravi considers the other groups' needs because he protects rack space even after his own poster is complete.",
                "considers other groups' needs",
                "protects rack space after finishing",
                worked_reasoning="His own task is done, so the reserved space can only be explained by attention to the groups that still need it.",
                next_step="answer with one supported quality and one exact action clue.",
            ),
        ],
    },
    "together_preposition_sentences": {
        "extra_cases": [
            N(
                "map-drawer",
                "The route map lies inside the top drawer. A compass rests beside the drawer handle.",
                "Describe both locations in complete sentences with precise prepositions.",
                "The route map is inside the top drawer. The compass is beside the drawer handle.",
                "map is inside the top drawer",
                "compass is beside the drawer handle",
                interaction_type="short_text",
            ),
            N(
                "bench-crates",
                "Two supply crates stand beneath the long bench, while the first-aid bag hangs above its right end.",
                "Write two complete position sentences from the visible facts.",
                "The supply crates are beneath the bench. The first-aid bag hangs above the bench's right end.",
                "crates are beneath the bench",
                "bag hangs above the right end",
                interaction_type="short_text",
            ),
            N(
                "gate-sign",
                "A welcome sign is fixed between the two gateposts. The visitor book sits on a stand in front of the gate.",
                "Use between and in front of in complete sentences.",
                "The welcome sign is between the gateposts. The visitor book is in front of the gate.",
                "sign is between the gateposts",
                "book is in front of the gate",
                interaction_type="short_text",
            ),
            N(
                "shelf-jars",
                "The blue jar is behind the seed packets. A measuring cup is next to the blue jar.",
                "Construct two unambiguous location sentences.",
                "The blue jar is behind the seed packets. The measuring cup is next to the blue jar.",
                "jar is behind seed packets",
                "cup is next to blue jar",
                interaction_type="short_text",
            ),
            N(
                "stage-positions",
                "The drum stands near the curtain. Three microphones are across from the front row of chairs.",
                "Transfer position language to describe both stage objects.",
                "The drum stands near the curtain. The microphones are across from the front row.",
                "drum stands near the curtain",
                "microphones are across from front row",
                interaction_type="short_text",
            ),
        ],
        "support_cases": [
            R(
                "cup-tray",
                "A steel cup is on the tray, and a folded cloth is under the tray.",
                "Choose a different preposition for each object and write complete sentences.",
                "The steel cup is on the tray. The folded cloth is under the tray.",
                "cup is on the tray",
                "cloth is under the tray",
                worked_reasoning="Ask where each object is compared with the tray; one touches its upper surface and the other is lower than it.",
                next_step="write both subject-verb-location sentences.",
                interaction_type="short_text",
            ),
            R(
                "cones-path",
                "Orange cones stand along the path, not inside it. The water point is at the end of the path.",
                "Repair the sentence 'The cones are in the path.'",
                "The orange cones stand along the path. The water point is at the end of the path.",
                "cones stand along the path",
                "water point at the end",
                worked_reasoning="The contrast word not rules out in; along follows the path's side, while at the end names the water point's exact place.",
                next_step="replace the wrong position word and add the second location.",
                interaction_type="short_text",
            ),
            R(
                "flag-poles",
                "A small flag hangs between two poles. A coil of rope lies behind the left pole.",
                "Name both relationships without dropping the sentence subjects.",
                "The flag hangs between the poles. The rope lies behind the left pole.",
                "flag hangs between poles",
                "rope lies behind left pole",
                worked_reasoning="Between requires two reference points; behind compares the rope with one named pole. Each needs its own subject and verb.",
                next_step="produce two complete location statements.",
                interaction_type="short_text",
            ),
            R(
                "notice-door",
                "The notice is beside the door rather than on it. The umbrella stand is opposite the notice.",
                "Use the contrast to correct both positions.",
                "The notice is beside the door. The umbrella stand is opposite the notice.",
                "notice is beside the door",
                "stand is opposite the notice",
                worked_reasoning="Rather than on blocks surface contact; opposite describes the stand facing the notice across the space.",
                next_step="write the two corrected relationships exactly.",
                interaction_type="short_text",
            ),
            R(
                "ladder-bucket",
                "A ladder leans against the wall. The paint bucket remains below its lowest step.",
                "Complete the final location check with against and below.",
                "The ladder leans against the wall. The paint bucket remains below the lowest step.",
                "ladder leans against wall",
                "bucket remains below lowest step",
                worked_reasoning="Against shows contact with the wall, while below places the bucket lower than the step; neither means inside.",
                next_step="answer independently with both complete sentences.",
                interaction_type="short_text",
            ),
        ],
    },
    "together_future_responses": {
        "extra_cases": [
            N(
                "morning-pickup",
                "Tomorrow, the guide team plans to collect name cards at the east gate and sort them before assembly.",
                "Answer what the guide team will do tomorrow in one complete sentence.",
                "The guide team will collect the name cards at the east gate and sort them before assembly.",
                "will collect name cards at east gate",
                "will sort them before assembly",
                interaction_type="short_text",
            ),
            N(
                "next-week-repair",
                "Next week, two volunteers plan to tighten the loose bench bolts while one adult checks the tools.",
                "Write the planned actions with correct future helpers.",
                "Two volunteers will tighten the bench bolts, and an adult will check the tools next week.",
                "volunteers will tighten bench bolts",
                "adult will check tools next week",
                interaction_type="short_text",
            ),
            N(
                "evening-cover",
                "This evening, rain is expected. The book team intends to move the boxes indoors and cover the handcart.",
                "Give a complete future response to the weather plan.",
                "This evening, the book team will move the boxes indoors and will cover the handcart before the rain.",
                "will move boxes indoors",
                "will cover handcart before rain",
                interaction_type="short_text",
            ),
            N(
                "Saturday-count",
                "On Saturday, Mina plans to count the sports kits, and her partners plan to record every missing item.",
                "Use will to state both Saturday actions clearly.",
                "On Saturday, Mina will count the sports kits, and her partners will record every missing item.",
                "Mina will count sports kits",
                "partners will record missing items",
                interaction_type="short_text",
            ),
            N(
                "festival-route",
                "For next month's festival, the route group intends to mark quiet lanes and place a helper at each crossing.",
                "Transfer future-tense planning to the festival route.",
                "The route group will mark the quiet lanes and will place a helper at each crossing for the festival.",
                "will mark quiet lanes",
                "will place helper at each crossing",
                interaction_type="short_text",
            ),
        ],
        "support_cases": [
            R(
                "tomorrow-labels",
                "Tomorrow, the class plans to label three storage boxes and check each spelling.",
                "Change the plan into one future-tense answer.",
                "Tomorrow, the class will label three storage boxes and will check each spelling.",
                "class will label storage boxes",
                "will check each spelling",
                worked_reasoning="The word tomorrow requires a future helper; place will before each planned action without changing the plan.",
                next_step="write the full answer with the time clue and both actions.",
                interaction_type="short_text",
            ),
            R(
                "next-hour-water",
                "In the next hour, Ravi plans to fill the clean can while his friends plan to carry it to the saplings.",
                "Repair the answer 'Ravi filled the can and friends carry it.'",
                "In the next hour, Ravi will fill the can, and his friends will carry it to the saplings.",
                "Ravi will fill the can",
                "friends will carry it",
                worked_reasoning="Both actions are planned for a later hour, so both verbs need will plus the base form; do not mix past and present.",
                next_step="replace both mismatched verbs with future forms.",
                interaction_type="short_text",
            ),
            R(
                "Monday-display",
                "On Monday, the art team intends to hang the finished panels and invite families to view them.",
                "Write the Monday plan without using will followed by an ing form.",
                "On Monday, the art team will hang the panels and will invite families to view them.",
                "will hang the panels",
                "will invite families",
                worked_reasoning="After will, use the base verbs hang and invite; hanging and inviting would need a different helper structure.",
                next_step="form both future actions with will plus base verb.",
                interaction_type="short_text",
            ),
            R(
                "later-message",
                "Later today, the office plans to send the route change, and every group plans to confirm that it arrived.",
                "State who will act and what each will do.",
                "Later today, the office will send the route change, and every group will confirm its arrival.",
                "office will send route change",
                "every group will confirm arrival",
                worked_reasoning="Keep the two subjects clear: the office sends, while the groups confirm. The later time puts both actions in the future.",
                next_step="write one complete sentence with both subject-action pairs.",
                interaction_type="short_text",
            ),
            R(
                "next-season-seeds",
                "Next season, the garden club intends to save bean seeds and share packets with two nearby schools.",
                "Give the final independent future response.",
                "Next season, the garden club will save bean seeds and will share packets with two nearby schools.",
                "club will save bean seeds",
                "will share packets with schools",
                worked_reasoning="The time clue next season controls both planned verbs; preserve the objects so the answer remains complete.",
                next_step="answer with the time, actor, and both future actions.",
                interaction_type="short_text",
            ),
        ],
    },
    "together_team_procedure": {
        "extra_cases": [
            N(
                "lost-item-desk",
                "Goal: run a lost-item desk. Materials: numbered tags, register, trays. Every returned item must be matched to the owner's description.",
                "Write an ordered desk procedure with a final identity check.",
                "First label each item and enter it in the register. Next place it on the matching tray. Finally compare the claimant's description with the record before returning the item.",
                "label and register each item first",
                "compare claimant description before return",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
            N(
                "seed-packets",
                "Goal: prepare seed packets. Materials: dry seeds, envelopes, name labels, scale. Each packet must contain the stated weight.",
                "Create a usable preparation procedure and completion check.",
                "First match each label to the dry seeds. Next weigh the stated amount, fill the envelope, and seal it. Finally compare the sealed packet's weight and label with the list.",
                "match label before weighing and filling",
                "check packet weight and label at end",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
            N(
                "reading-corner",
                "Goal: reset a reading corner. Materials: shelf chart, returned books, cloth, floor marker. The exit path must remain clear.",
                "Write the ordered reset steps with a safety check.",
                "First move the floor marker away from the exit path. Next wipe the shelves and return each book by the shelf chart. Finally walk the exit path and correct any blockage.",
                "clear exit before cleaning and shelving",
                "walk exit path and correct blockage",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
            N(
                "water-station",
                "Goal: prepare drinking water for a match. Materials: clean containers, lids, cups, count sheet. Cups must be enough for both teams.",
                "Construct a procedure from cleaning through the count check.",
                "First rinse the containers and cups. Next fill and cover the containers, then arrange the cups in two team groups. Finally count the cups against the sheet and replace any shortage.",
                "rinse before filling and arranging",
                "count cups and replace shortage",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=22,
            ),
            N(
                "rain-shelter-plan",
                "Goal: protect waiting families from rain. Materials: poles, tied sheet, ground markers, dry-rope box. The sheet must drain away from the walkway.",
                "Transfer procedure writing to build and test the shelter.",
                "First mark a clear walkway and place the poles outside it. Next tie the sheet so its lower edge drains away from the path. Finally pour a small test cup on the sheet and adjust any unsafe runoff.",
                "mark walkway before placing poles",
                "test drainage and adjust unsafe runoff",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=24,
            ),
        ],
        "support_cases": [
            R(
                "badge-table",
                "Materials: blank badges, verified name list, pens, two trays. Goal: give each visitor the correct badge.",
                "Order the badge steps and include the handover check.",
                "First copy names from the verified list onto badges. Next sort finished badges into the two trays. Finally ask each visitor to confirm the name before handover.",
                "copy from verified list first",
                "visitor confirms name before handover",
                worked_reasoning="Verification controls the writing step, and the visitor check must occur after sorting but before the badge is handed over.",
                next_step="write the three stages with clear sequence words.",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=18,
            ),
            R(
                "tool-cart",
                "Materials: tool list, cart, cloth, return boxes. Goal: prepare only safe listed tools for a repair group.",
                "Repair a plan that loads tools before checking them.",
                "First match each tool to the list and inspect it. Next clean and load the safe tools. Finally place damaged tools in return boxes and record them.",
                "match and inspect tools before loading",
                "record damaged tools in return boxes",
                worked_reasoning="A safety decision must precede loading; separating damaged tools at the end prevents them from reaching the repair group.",
                next_step="move inspection first and preserve the damage record.",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=18,
            ),
            R(
                "notice-delivery",
                "Materials: approved notices, route list, waterproof folder, delivery record. Goal: reach every named building.",
                "Write a repeatable delivery procedure with proof of completion.",
                "First arrange approved notices in route order and place them in the waterproof folder. Next deliver one at each listed building. Finally mark every delivery and investigate any blank record.",
                "arrange notices in route order",
                "mark delivery and investigate blanks",
                worked_reasoning="Route order reduces missed stops, while the final record reveals whether every named building actually received a notice.",
                next_step="include preparation, delivery, and record checking.",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
            R(
                "sports-bibs",
                "Materials: clean bibs, team list, size labels, spare basket. Goal: fit every player without mixing teams.",
                "Explain the order and use the spare basket correctly.",
                "First separate bibs by team and size. Next match each player to the list and issue one bib. Finally place unused bibs in the spare basket and count them.",
                "separate bibs before issuing",
                "count unused bibs in spare basket",
                worked_reasoning="Sorting prevents team mixing, matching protects fair issue, and the spare count closes the equipment record.",
                next_step="write the procedure without skipping the final count.",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
            R(
                "community-map",
                "Materials: street list, blank map, pencils, checker card. Goal: mark a safe walking route to the clinic.",
                "Complete the final procedure independently with a route check.",
                "First compare the street list with the blank map. Next draw the route and mark every crossing. Finally follow the route with the checker card and correct any missing turn.",
                "compare street list before drawing",
                "follow route and correct missing turn",
                worked_reasoning="The source list controls the drawing, and physically tracing each turn checks whether another walker can follow the finished map.",
                next_step="give all ordered actions and the correction step.",
                ordered=True,
                interaction_type="paragraph_text",
                min_words=20,
            ),
        ],
    },
}


P(LEVELS, QUALITY_PACKS)


LAUNCH_DEPTH_CASES = {
    "together_poem_message": [
        N(
            "harvest-crates-verse",
            "At a rooftop garden harvest, a card reads: 'One crate waits beside the wall; four careful arms become one steady lift; tomatoes reach the table without a fall.'",
            "Explain the picture created by 'four careful arms become one steady lift' and state the verse's main message.",
            "The image shows four helpers combining their strength as if they made one steady lift. The main message is that coordinated effort moves a difficult load safely.",
            "four helpers combining their strength",
            "coordinated effort moves a difficult load safely",
        ),
        N(
            "mural-colours-verse",
            "During a corridor mural project, learners write: 'A single colour marks one square; many colours meet and make the whole wall sing.' Each learner paints a different planned section.",
            "Interpret how the wall can 'sing' and give the message of the lines.",
            "The singing wall is a playful image for the lively mural made when many colours meet. The lines show that separate contributions can join into one joyful result.",
            "lively mural made when many colours meet",
            "separate contributions can join into one joyful result",
        ),
        N(
            "bus-shelter-tarp-verse",
            "Neighbours secure a loose rain cover over a bus shelter. Their note says: 'Each knot is small, yet knot beside knot teaches the roof to stand against the wind.'",
            "Explain what the roof 'learns' in this image and state the central idea.",
            "The roof does not really learn; the image shows that many small, secure knots make the cover strong. The central idea is that careful shared tasks can protect a whole community space.",
            "many small, secure knots make the cover strong",
            "careful shared tasks can protect a whole community space",
        ),
    ],
    "together_words_in_context": [
        N(
            "radio-repair-coordinate",
            "At the school radio desk, Sana reads the checklist while Kabir tests each cable and Meera records the sound. Their coordinated work finds the loose plug before assembly.",
            "Use the context to explain coordinated, then identify one noun, one verb, and one adjective from the passage.",
            "Coordinated means arranged so the different jobs work together. Sana is a noun, tests is a verb, and loose is an adjective describing the plug.",
            "different jobs work together",
            "Sana is a noun, tests is a verb, and loose is an adjective",
        ),
        N(
            "compost-team-resourceful",
            "The garden club runs out of plant labels. A resourceful group washes used ice-cream sticks, writes seed names on them, and places the clean markers in each bed.",
            "Explain resourceful from the actions and classify group, washes, and clean by their word jobs.",
            "Resourceful means finding a useful solution with materials already available. Group is a noun, washes is a verb, and clean is an adjective describing the markers.",
            "finding a useful solution with materials already available",
            "Group is a noun, washes is a verb, and clean is an adjective",
        ),
        N(
            "catalogue-assist",
            "In the reading room, Vihaan assists a new pupil by checking the catalogue and walking with her to the correct shelf. The helpful guide then returns to his desk.",
            "Work out the meaning of assists and identify the word jobs of Vihaan, checking, and helpful.",
            "Assists means helps someone complete a task. Vihaan is a noun, checking is a verb, and helpful is an adjective describing the guide.",
            "helps someone complete a task",
            "Vihaan is a noun, checking is a verb, and helpful is an adjective",
        ),
    ],
    "together_event_chain": [
        N(
            "drain-leaf-blockage",
            "Leaves cover the courtyard drain before a storm. The eco-club gathers them into a compost sack, water begins flowing through the grate, and the caretaker marks a weekly clearing turn.",
            "Write the event chain in order and explain how the final step prevents the problem from returning.",
            "First leaves block the drain, and then the club removes them for compost so water can flow. Finally, a weekly clearing turn prevents another leaf blockage from building up.",
            "club removes them for compost so water can flow",
            "weekly clearing turn prevents another leaf blockage",
            ordered=True,
            interaction_type="summary",
        ),
        N(
            "library-window-rescue",
            "A sudden shower enters through an open library window. Two pupils move the book trolley away, another closes the window, and the librarian spreads the damp covers under a fan.",
            "Summarize the response from first protection to final drying in the correct order.",
            "The pupils first move the trolley away from the rain and close the window. The librarian then places the damp covers under a fan so they can dry.",
            "move the trolley away from the rain and close the window",
            "places the damp covers under a fan",
            ordered=True,
            interaction_type="summary",
        ),
        N(
            "seed-swap-labels",
            "Families bring unmarked seed packets to a neighbourhood swap. Volunteers sort the seeds, gardeners identify each kind from saved notes, and children attach new labels before the packets are exchanged.",
            "Retell the sequence and show why labelling must happen before the exchange.",
            "Volunteers first sort the packets, and gardeners use their notes to identify the seeds. Children label each packet before the exchange so families know what they are taking home.",
            "gardeners use their notes to identify the seeds",
            "label each packet before the exchange",
            ordered=True,
            interaction_type="summary",
        ),
    ],
    "together_inference_and_reason": [
        N(
            "quiet-screw-check",
            "During a model-car test, everyone watches the wheels. Rehan silently points to a loose screw near the battery holder, and the team tightens it before the next run. The car then completes the track.",
            "What does Rehan's action reveal about teamwork, and why did it affect the result?",
            "Rehan shows careful teamwork because he notices and shares a problem others missed. Tightening the loose screw before testing helps the car complete the track.",
            "notices and shares a problem others missed",
            "Tightening the loose screw before testing helps the car complete the track",
        ),
        N(
            "reusable-cup-choice",
            "The class picnic committee can buy disposable cups or wash the steel cups stored at school. Aditi offers to lead a washing team, and the committee chooses the stored cups, leaving no cup waste after lunch.",
            "Infer what Aditi values and explain how her offer changes the group's choice.",
            "Aditi values reducing waste because she makes the reusable option practical. Her offer to lead washing helps the committee choose steel cups and avoid disposable rubbish.",
            "values reducing waste",
            "offer to lead washing helps the committee choose steel cups",
        ),
        N(
            "stage-credit-list",
            "After a shadow play wins praise, the announcer names only the actors. Nila asks him to add the pupils who cut the figures, managed the lamp, and played the music before the notice is printed.",
            "What quality does Nila show, and how can her request strengthen the team?",
            "Nila shows fairness by seeking credit for the unseen jobs as well as the actors. Naming every contribution can make team members feel respected and willing to work together again.",
            "shows fairness by seeking credit for the unseen jobs",
            "make team members feel respected and willing to work together again",
        ),
    ],
    "together_preposition_sentences": [
        N(
            "first-aid-shelf",
            "The first-aid box is on the middle shelf, below the emergency chart, and beside the office door. A torch hangs above the box.",
            "Write two complete sentences that place the box and torch using at least three visible prepositions.",
            "The first-aid box rests on the middle shelf below the emergency chart and beside the office door. The torch hangs above the box.",
            "box rests on the middle shelf below the emergency chart",
            "torch hangs above the box",
            interaction_type="short_text",
        ),
        N(
            "art-display-route",
            "Visitors enter through the blue arch, walk between two clay displays, and stop in front of the student mural. The feedback table stands behind them.",
            "Describe the route and final table position in two correctly ordered sentences.",
            "Visitors walk through the blue arch and between the clay displays before stopping in front of the mural. The feedback table is behind the visitors.",
            "through the blue arch and between the clay displays",
            "feedback table is behind the visitors",
            interaction_type="short_text",
        ),
        N(
            "recycling-station-map",
            "The paper bin stands to the left of the water tap. The metal bin is under the shade roof, opposite the paper bin, while the glass crate sits inside the locked store.",
            "Use the map details to write one sentence for the metal bin and one for the glass crate.",
            "The metal bin stands under the shade roof opposite the paper bin. The glass crate remains inside the locked store.",
            "metal bin stands under the shade roof opposite the paper bin",
            "glass crate remains inside the locked store",
            interaction_type="short_text",
        ),
    ],
    "together_future_responses": [
        N(
            "tomorrow-garden-mulch",
            "The weather report predicts a hot day tomorrow, and the class garden soil is already dry. The watering cans are full, and a sack of leaf mulch is beside the beds.",
            "What will the garden team do tomorrow? Give two connected future actions.",
            "Tomorrow the team will water the beds early and will spread leaf mulch to keep moisture in the soil.",
            "will water the beds early",
            "will spread leaf mulch",
            interaction_type="short_text",
        ),
        N(
            "next-friday-reading-stall",
            "The reading stall opens next Friday. Anaya has finished the book list, but the price cards and table signs are still blank.",
            "State what Anaya and her partner will complete before the stall opens.",
            "Anaya will check the finished book list, and her partner will write the price cards and table signs before next Friday.",
            "Anaya will check the finished book list",
            "partner will write the price cards and table signs",
            interaction_type="short_text",
        ),
        N(
            "later-rain-cover",
            "Dark clouds are moving toward the sports field. The bibs are dry on a line, and the equipment trolley has an empty waterproof cover.",
            "What will the helpers do later if rain begins?",
            "If rain begins later, the helpers will collect the dry bibs and will pull the waterproof cover over the equipment trolley.",
            "will collect the dry bibs",
            "will pull the waterproof cover over the equipment trolley",
            interaction_type="short_text",
        ),
    ],
    "together_team_procedure": [
        N(
            "refill-station-setup",
            "Materials: a clean water container, a low table, two cups, a drip tray, and a refill sign. The station must be stable and easy for younger pupils to reach.",
            "Write an ordered procedure for setting up and checking the refill station.",
            "First place the low table on level ground and set the drip tray on it. Next put the clean container and cups on the tray, attach the refill sign, and finally test that pupils can reach the tap safely.",
            "place the low table on level ground and set the drip tray on it",
            "test that pupils can reach the tap safely",
            ordered=True,
            interaction_type="summary",
        ),
        N(
            "lost-property-labels",
            "A lost-property team has three trays, date cards, pencils, and a cupboard key. Wet items must dry before they enter the cupboard.",
            "Give the steps for recording, sorting, and storing a newly found item.",
            "First write the date and place on a card. Next place the item with its card in the correct tray, let any wet item dry, and finally lock the sorted items in the cupboard.",
            "write the date and place on a card",
            "let any wet item dry and finally lock the sorted items in the cupboard",
            ordered=True,
            interaction_type="summary",
        ),
        N(
            "shadow-play-stage",
            "The shadow-play group has a white sheet, two stands, clips, a lamp, paper figures, and floor tape. The hot lamp must stay behind a marked line.",
            "Write a safe team procedure from building the screen to testing one figure.",
            "First clip the white sheet tightly between the stands. Then mark the lamp line, place the lamp behind it, assign one pupil to each paper figure, and test a single shadow before the show.",
            "clip the white sheet tightly between the stands",
            "mark the lamp line and place the lamp behind it",
            ordered=True,
            interaction_type="summary",
        ),
    ],
}


D(LEVELS, LAUNCH_DEPTH_CASES)


CONFIG = {
    "chapter_id": "eng_c4_ch01",
    "chapter_no": 1,
    "title": "Together We Can",
    "unit_title": "My Land",
    "source_url": "https://ncert.nic.in/textbook/pdf/desa101.pdf",
    "anchors": [
        A("recite", "Let us Recite", 1, 1, treatment="textbook_companion", required=False),
        A("think", "Let us Think", 2, 2),
        A("speak", "Let us Speak", 2, 3, treatment="offline_group_activity", required=False),
        A("learn", "Let us Learn", 3, 5),
        A("write", "Let us Write", 6, 7),
        A("do", "Let us Do", 7, 8, treatment="optional_creative", required=False),
    ],
    "levels": LEVELS,
    "bonus_level_index": 3,
    "bonus_assessment": {
        "a": O(
            "assessment-a-bonus-captain",
            "The fastest runner asks a slower teammate to choose the relay order because that teammate has tracked everyone's practice times.",
            "Infer why the runner gives this responsibility and justify the choice.",
            "The runner values relevant evidence over speed because the teammate has studied every runner's times and can arrange the order fairly.",
            E("Infers respect for relevant evidence.", "values relevant evidence", "over speed"),
            E("Uses tracked practice times to justify the responsibility.", "studied every runner's times", "arrange the order fairly"),
        ),
        "b": O(
            "assessment-b-bonus-credit",
            "After receiving praise for a model, Om points to the hidden support frame and tells the teacher that Kavya designed it.",
            "What does Om's action reveal, and how may it affect the team?",
            "Om values fair credit because he identifies Kavya's unseen design work, which can strengthen trust among the team members.",
            E("Infers fair credit as Om's value.", "values fair credit", "identifies Kavya's"),
            E("Explains the likely trust benefit.", "strengthen trust", "team members"),
        ),
    },
}


MANIFEST = make_manifest(CONFIG)
