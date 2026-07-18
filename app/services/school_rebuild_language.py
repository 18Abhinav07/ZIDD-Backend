"""Deterministic Hindi/Hinglish strategy scaffolds for English learning."""

from __future__ import annotations

from collections.abc import Iterable


_HINGLISH_SUPPORT = {
    "reading.dialogue_attribution": "Har line ke saath dekho kisne kaha, kisne suna, aur reply ne kya nayi baat jodi.",
    "grammar.prepositions": "Object kahan hai ya kis direction mein ja raha hai, us relation ko dekhkar in, on, under, behind jaise word chuno.",
    "vocab.spelling": "Word ko chhote sound ya letter parts mein bolo, phir har part ko sahi order mein likhkar dobara padho.",
    "reading.poetic_language": "Poem mein jo picture, comparison, ya special sound banta hai use imagine karo aur line ke words se meaning jodo.",
    "vocab.attribute_ordering": "Pehle quality pakdo, jaise size ya speed, phir har item ko usi ek quality se compare karke order banao.",
    "reading.word_meaning_context": "Mushkil word ke aas-paas ke words padho. Jo ho raha hai, usse meaning ka clue milega.",
    "reading.sentence_comprehension": "Sentence mein pehle kaun ya kya hai, phir uske saath kya ho raha hai, ye dhoondo.",
    "reading.paragraph_main_idea": "Har sentence ka chhota point socho. Jo idea baar-baar saath aa raha hai, wahi main idea hai.",
    "reading.inference_reason": "Kyun ka jawab seedha na mile to action aur result ka clue jodo.",
    "reading.event_sequence": "First, next, aur last wale events dhoondo. Time aur cause clues se unka sahi order banao.",
    "vocab.chapter_word_usage": "Naye word ka meaning yaad karke dekho ki woh is sentence mein sahi jagah fit hota hai ya nahi.",
    "vocab.antonyms": "Sentence ka meaning samjho, phir aisa word chuno jo usi context mein target word ka opposite bataye.",
    "vocab.word_formation": "Word ko base words, prefix, suffix, ya compound parts mein todo aur dekho har part final meaning mein kya jodta hai.",
    "grammar.noun_verb_adjective": "Naming word batata hai kaun ya kya; action word batata hai kya hua; describing word batata hai kaisa.",
    "grammar.tense_usage": "Time clue pehle pakdo: ab, pehle, ya baad mein. Phir verb ka form chuno.",
    "grammar.connectors_because_and_but": "Because reason jodta hai, and ek aur baat, aur but ulta ya alag idea.",
    "grammar.sentence_order": "Kaun ya kya pehle rakho, action uske baad, phir baaki detail jodo.",
    "grammar.subject_verb_agreement": "Subject ek hai ya ek se zyada, ye pehle dekho; phir uske saath match karta verb form chuno.",
    "grammar.question_formation": "Question word ya helping verb se shuru karo, phir subject aur action rakho, aur end mein question mark lagao.",
    "grammar.adverbs": "Word frequency, time, ya manner mein se kya batata hai ye pehchano, phir use action ke paas sahi jagah rakho.",
    "grammar.pronouns": "He, she, it, they jaise pronoun ko us clear noun se jodo jiska woh naam dobara lene se bachata hai.",
    "grammar.punctuation_capitalization": "Sentence aur proper name ko capital letter se shuru karo; meaning ke hisaab se full stop, comma, ya question mark lagao.",
    "writing.complete_sentence": "Sentence mein kaun ya kya aur ek clear action ya description dono hone chahiye.",
    "writing.short_answer": "Question ke main words pakdo aur ek ya do seedhe, relevant sentences likho.",
    "writing.reason_answer": "Apna point bolo, phir because ke saath passage ka reason ya clue jodo.",
    "writing.summary_own_words": "Sabse important event ya idea chuno aur use chhote apne words mein batao; line copy mat karo.",
    "writing.compare_contrast": "Pehle ek same baat, phir ek different baat dhoondo. Dono ko clear words se jodo.",
    "writing.friendly_message": "Greeting se shuru karo, zaroori baat aur ek useful reply likho, phir friendly closing do.",
    "writing.dialogue": "Har turn ka speaker clear rakho, speech punctuation lagao, aur har reply ko pichhli line ka relevant response banao.",
    "writing.paragraph": "Topic sentence se main point bolo, connected details ko order mein rakho, aur ek closing sentence se paragraph complete karo.",
    "writing.procedure": "Steps ko first, next, then, aur last ke order mein likho; har step mein clear action do.",
    "research.information_selection": "Question ke kaam ki facts hi chuno, har fact ko supplied source se check karo, aur unrelated details hatao.",
    "speaking.multilingual_expression": "Idea pehle comfortable language mein clear karo, phir usi meaning ko chhote simple English words mein bolo.",
    "speaking.recitation": "Punctuation par pause lo, words clearly bolo, aur poem ya passage ka rhythm aur meaning saath rakho.",
    "listening.sound_discrimination": "Dono words ko dheere bolo ya suno aur jis sound se woh alag hote hain us part par dhyan do.",
}

_HINDI_SUPPORT = {
    "reading.dialogue_attribution": "हर पंक्ति में पहचानिए कि किसने कहा, किसने सुना और उत्तर ने कौन-सी नई बात जोड़ी।",
    "grammar.prepositions": "वस्तु कहाँ है या किस दिशा में जा रही है, यह संबंध देखकर in, on, under, behind जैसे शब्द चुनिए।",
    "vocab.spelling": "शब्द को छोटे ध्वनि या अक्षर भागों में बोलिए, फिर हर भाग को सही क्रम में लिखकर दोबारा पढ़िए।",
    "reading.poetic_language": "कविता में बनी तस्वीर, तुलना या विशेष ध्वनि की कल्पना कीजिए और पंक्ति के शब्दों से उसका अर्थ जोड़िए।",
    "vocab.attribute_ordering": "पहले एक गुण पहचानिए, जैसे आकार या गति, फिर सभी वस्तुओं की उसी गुण से तुलना करके क्रम बनाइए।",
    "reading.word_meaning_context": "कठिन शब्द के आगे-पीछे के शब्द पढ़िए। जो घटना हो रही है, उससे अर्थ का संकेत खोजिए।",
    "reading.sentence_comprehension": "पहले पहचानिए कि वाक्य किसके बारे में है, फिर देखिए उसके साथ क्या हो रहा है।",
    "reading.paragraph_main_idea": "हर वाक्य की छोटी बात समझिए। जो विचार पूरे अनुच्छेद को जोड़ता है, वही मुख्य विचार है।",
    "reading.inference_reason": "यदि ‘क्यों’ का उत्तर सीधे न मिले, तो काम और उसके परिणाम के संकेत जोड़िए।",
    "reading.event_sequence": "पहली, अगली और अंतिम घटना खोजिए। समय और कारण के संकेतों से उनका सही क्रम बनाइए।",
    "vocab.chapter_word_usage": "नए शब्द का अर्थ सोचिए और जाँचिए कि वह इस वाक्य में सही जगह और अर्थ में आया है।",
    "vocab.antonyms": "वाक्य का अर्थ समझकर ऐसा शब्द चुनिए जो उसी संदर्भ में दिए गए शब्द का विपरीत अर्थ बताए।",
    "vocab.word_formation": "शब्द को मूल शब्द, उपसर्ग, प्रत्यय या संयुक्त भागों में तोड़िए और देखिए हर भाग अंतिम अर्थ में क्या जोड़ता है।",
    "grammar.noun_verb_adjective": "नाम वाला शब्द बताता है कौन या क्या, क्रिया बताती है क्या हुआ, और विशेषता वाला शब्द बताता है कैसा।",
    "grammar.tense_usage": "पहले समय का संकेत खोजिए—अभी, पहले या बाद में—फिर क्रिया का सही रूप चुनिए।",
    "grammar.connectors_because_and_but": "Because कारण जोड़ता है, and एक और बात जोड़ता है, और but अलग या उलटा विचार जोड़ता है।",
    "grammar.sentence_order": "पहले कौन या क्या रखें, उसके बाद क्रिया, फिर बाकी जानकारी सही क्रम में जोड़ें।",
    "grammar.subject_verb_agreement": "पहले देखिए कर्ता एक है या एक से अधिक, फिर उससे मेल खाने वाला क्रिया रूप चुनिए।",
    "grammar.question_formation": "प्रश्नवाचक शब्द या सहायक क्रिया से शुरू करें, फिर कर्ता और क्रिया रखें और अंत में प्रश्नचिह्न लगाएँ।",
    "grammar.adverbs": "पहचानिए कि शब्द बारंबारता, समय या ढंग में से क्या बताता है, फिर उसे क्रिया के पास सही जगह रखें।",
    "grammar.pronouns": "He, she, it, they जैसे सर्वनाम को उस स्पष्ट नाम वाले शब्द से जोड़िए जिसकी जगह वह आया है।",
    "grammar.punctuation_capitalization": "वाक्य और विशेष नाम को बड़े अक्षर से शुरू करें; अर्थ के अनुसार पूर्ण विराम, अल्पविराम या प्रश्नचिह्न लगाएँ।",
    "writing.complete_sentence": "पूरे वाक्य में कौन या क्या और एक साफ़ क्रिया या विशेषता दोनों होने चाहिए।",
    "writing.short_answer": "प्रश्न के मुख्य शब्द पहचानिए और एक या दो सीधे, उपयोगी वाक्य लिखिए।",
    "writing.reason_answer": "पहले अपना उत्तर दीजिए, फिर because के साथ पाठ का कारण या संकेत जोड़िए।",
    "writing.summary_own_words": "सबसे ज़रूरी घटना या विचार चुनकर उसे अपने छोटे वाक्यों में लिखिए; पंक्ति की नकल न करें।",
    "writing.compare_contrast": "पहले एक समानता और फिर एक अंतर खोजिए। दोनों को साफ़ तुलना वाले शब्दों से जोड़िए।",
    "writing.friendly_message": "अभिवादन से शुरू करें, ज़रूरी बात और उपयोगी उत्तर लिखें, फिर मित्रतापूर्ण समापन करें।",
    "writing.dialogue": "हर संवाद-पंक्ति का वक्ता साफ़ रखें, सही विराम-चिह्न लगाएँ और हर उत्तर को पिछली पंक्ति से जोड़ें।",
    "writing.paragraph": "विषय-वाक्य में मुख्य बात लिखें, जुड़ी हुई जानकारियाँ क्रम में रखें और समापन वाक्य से अनुच्छेद पूरा करें।",
    "writing.procedure": "कदमों को पहले, फिर, उसके बाद और अंत में के क्रम में लिखें; हर कदम में साफ़ क्रिया दें।",
    "research.information_selection": "प्रश्न के लिए उपयोगी तथ्य ही चुनें, हर तथ्य को दिए गए स्रोत से जाँचें और असंबंधित जानकारी हटाएँ।",
    "speaking.multilingual_expression": "विचार को पहले अपनी सहज भाषा में साफ़ करें, फिर उसी अर्थ को छोटे और सरल अंग्रेज़ी शब्दों में बोलें।",
    "speaking.recitation": "विराम-चिह्न पर रुकें, शब्द साफ़ बोलें और कविता या पाठ की लय तथा अर्थ दोनों बनाए रखें।",
    "listening.sound_discrimination": "दोनों शब्द धीरे बोलकर या सुनकर उस ध्वनि-भाग पर ध्यान दें जहाँ वे अलग होते हैं।",
}

_CERTIFYING_STAGES = frozenset({
    "independent_check",
    "independent_application",
    "transfer_check",
    "transfer",
    "review",
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
