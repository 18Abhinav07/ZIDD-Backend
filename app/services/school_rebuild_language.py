"""Deterministic Hindi/Hinglish strategy scaffolds for English learning."""

from __future__ import annotations

from collections.abc import Iterable


_HINGLISH_SUPPORT = {
    "reading.word_meaning_context": "Mushkil word ke aas-paas ke words padho. Jo ho raha hai, usse meaning ka clue milega.",
    "reading.sentence_comprehension": "Sentence mein pehle kaun ya kya hai, phir uske saath kya ho raha hai, ye dhoondo.",
    "reading.paragraph_main_idea": "Har sentence ka chhota point socho. Jo idea baar-baar saath aa raha hai, wahi main idea hai.",
    "reading.inference_reason": "Kyun ka jawab seedha na mile to action aur result ka clue jodo.",
    "vocab.chapter_word_usage": "Naye word ka meaning yaad karke dekho ki woh is sentence mein sahi jagah fit hota hai ya nahi.",
    "grammar.noun_verb_adjective": "Naming word batata hai kaun ya kya; action word batata hai kya hua; describing word batata hai kaisa.",
    "grammar.tense_usage": "Time clue pehle pakdo: ab, pehle, ya baad mein. Phir verb ka form chuno.",
    "grammar.connectors_because_and_but": "Because reason jodta hai, and ek aur baat, aur but ulta ya alag idea.",
    "grammar.sentence_order": "Kaun ya kya pehle rakho, action uske baad, phir baaki detail jodo.",
    "writing.complete_sentence": "Sentence mein kaun ya kya aur ek clear action ya description dono hone chahiye.",
    "writing.short_answer": "Question ke main words pakdo aur ek ya do seedhe, relevant sentences likho.",
    "writing.reason_answer": "Apna point bolo, phir because ke saath passage ka reason ya clue jodo.",
    "writing.summary_own_words": "Sabse important event ya idea chuno aur use chhote apne words mein batao; line copy mat karo.",
    "writing.compare_contrast": "Pehle ek same baat, phir ek different baat dhoondo. Dono ko clear words se jodo.",
    "writing.friendly_message": "Greeting se shuru karo, zaroori baat aur ek useful reply likho, phir friendly closing do.",
}

_HINDI_SUPPORT = {
    "reading.word_meaning_context": "कठिन शब्द के आगे-पीछे के शब्द पढ़िए। जो घटना हो रही है, उससे अर्थ का संकेत खोजिए।",
    "reading.sentence_comprehension": "पहले पहचानिए कि वाक्य किसके बारे में है, फिर देखिए उसके साथ क्या हो रहा है।",
    "reading.paragraph_main_idea": "हर वाक्य की छोटी बात समझिए। जो विचार पूरे अनुच्छेद को जोड़ता है, वही मुख्य विचार है।",
    "reading.inference_reason": "यदि ‘क्यों’ का उत्तर सीधे न मिले, तो काम और उसके परिणाम के संकेत जोड़िए।",
    "vocab.chapter_word_usage": "नए शब्द का अर्थ सोचिए और जाँचिए कि वह इस वाक्य में सही जगह और अर्थ में आया है।",
    "grammar.noun_verb_adjective": "नाम वाला शब्द बताता है कौन या क्या, क्रिया बताती है क्या हुआ, और विशेषता वाला शब्द बताता है कैसा।",
    "grammar.tense_usage": "पहले समय का संकेत खोजिए—अभी, पहले या बाद में—फिर क्रिया का सही रूप चुनिए।",
    "grammar.connectors_because_and_but": "Because कारण जोड़ता है, and एक और बात जोड़ता है, और but अलग या उलटा विचार जोड़ता है।",
    "grammar.sentence_order": "पहले कौन या क्या रखें, उसके बाद क्रिया, फिर बाकी जानकारी सही क्रम में जोड़ें।",
    "writing.complete_sentence": "पूरे वाक्य में कौन या क्या और एक साफ़ क्रिया या विशेषता दोनों होने चाहिए।",
    "writing.short_answer": "प्रश्न के मुख्य शब्द पहचानिए और एक या दो सीधे, उपयोगी वाक्य लिखिए।",
    "writing.reason_answer": "पहले अपना उत्तर दीजिए, फिर because के साथ पाठ का कारण या संकेत जोड़िए।",
    "writing.summary_own_words": "सबसे ज़रूरी घटना या विचार चुनकर उसे अपने छोटे वाक्यों में लिखिए; पंक्ति की नकल न करें।",
    "writing.compare_contrast": "पहले एक समानता और फिर एक अंतर खोजिए। दोनों को साफ़ तुलना वाले शब्दों से जोड़िए।",
    "writing.friendly_message": "अभिवादन से शुरू करें, ज़रूरी बात और उपयोगी उत्तर लिखें, फिर मित्रतापूर्ण समापन करें।",
}

_CERTIFYING_STAGES = frozenset({
    "independent_check",
    "transfer_check",
    "chapter_check",
})


def localized_teaching_support(
    *,
    preferred_language: str,
    skill_ids: Iterable[str],
    stage: str,
    en_production_confidence: float = 0.0,
) -> str:
    """Return one strategy scaffold; never a translated passage or answer."""

    language = str(preferred_language or "en").strip().lower()
    if language == "en":
        return ""
    if stage == "chapter_check":
        return ""
    bank = _HINDI_SUPPORT if language == "hi" else _HINGLISH_SUPPORT
    support = next(
        (bank[skill_id] for skill_id in skill_ids if skill_id in bank),
        "",
    )
    if not support:
        return ""
    confidence = max(0.0, min(1.0, float(en_production_confidence)))
    if confidence >= 0.85 and stage not in _CERTIFYING_STAGES:
        return ""
    if stage in _CERTIFYING_STAGES:
        requirement = (
            "रणनीति याद रखें, लेकिन अपना उत्तर अंग्रेज़ी में स्वयं लिखें।"
            if language == "hi"
            else "Strategy yaad rakho, lekin apna answer English mein likho."
        )
        return f"{support} {requirement}"
    return support
