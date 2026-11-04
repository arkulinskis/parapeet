"""The languages Parapeet teaches: French (the original), Spanish and Italian. Plain Python (no Anvil imports): the
browser and the server share it (tools/testing/test_server.py copies it next to the server modules).

Every phrase has the same LineID in every language, so one English translation (FrenchSentences_translation) serves
all three. The text tables are FrenchSentences, SpanishSentences and ItalianSentences (same columns); the recorded
voices VoiceFiles, VoiceFiles_spanish and VoiceFiles_italian (server_code/Phrases.py, TABLES).

In the browser a phrase is {"id", "cat", "lang", "fr": {mood: text}, "en": {mood: text}}: the "fr" key holds the text
in the language being learned, whichever it is (the name is historical: Parapeet started with French only), and
phrase["lang"] says which language that is. The same goes for the card's "fr" side and drills' "lang": "fr".
"""

CODES = ["fr", "es", "it"]
DEFAULT = "fr"

LANGS: dict = {
    "fr": {
        "name": "French", "native": "Français", "short": "FR", "tts": "fr-FR", "asr": "fr-CA",
        "flag": ["#1f4fa8", "#ffffff", "#e0303b"], "stripes": "v",
        "formal": "vous", "familiar": "tu", "we": "nous", "love": "mon amour",
        "formal_words": ["vous", "votre", "vos"], "formal_cased": [], "formal_clitics": False,
        "familiar_words": ["tu", "te", "toi", "ton", "ta", "tes"], "familiar_prefixes": ["t'"],
        "formal_weak": [], "formal_suffixes": [], "familiar_suffixes": [], "suffix_exceptions": [],
        "praise": ["Très bien !", "Bravo !", "Super !", "Parfait !"],
        "very_good": "Très bien !", "perfect": "Parfait !", "well_done": "Bien joué !", "bye": "À bientôt !",
        "places": "Montréal, Paris, Brussels or Geneva",
        "variety": "Standard, everyday French that works in France and in Québec. The speech check listens for "
                   "Canadian French and understands a French accent too.",
    },
    "es": {
        "name": "Spanish", "native": "Español", "short": "ES", "tts": "es-ES", "asr": "es-ES",
        "flag": ["#c60b1e", "#ffc400", "#c60b1e"], "stripes": "h",
        "formal": "usted", "familiar": "tú", "we": "nosotros", "love": "mi amor",
        "formal_words": ["usted", "ustedes", "ud", "uds"], "formal_cased": [], "formal_clitics": False,
        "familiar_words": ["tú", "tu", "tus", "te", "ti", "contigo", "tuyo", "tuya", "tuyos", "tuyas"],
        "familiar_prefixes": [],
        "formal_weak": ["le", "les"], "formal_suffixes": ["rle", "rles", "ndole", "ndoles"],
        "familiar_suffixes": ["arte", "erte", "irte", "ndote"],  # verte, ayudarte, escucharte, recordándote
        "suffix_exceptions": ["parte", "aparte", "arte", "comparte", "reparte", "descarte", "baluarte", "estandarte", "marte",
                              "suerte", "fuerte", "muerte", "inerte", "advierte", "divierte", "convierte",
                              "invierte", "vierte", "despierte", "pervierte"],
        "praise": ["¡Muy bien!", "¡Bravo!", "¡Genial!", "¡Perfecto!"],
        "very_good": "¡Muy bien!", "perfect": "¡Perfecto!", "well_done": "¡Bien hecho!", "bye": "¡Hasta pronto!",
        "places": "Madrid, Mexico City, Bogotá or Buenos Aires",
        "variety": "Neutral, everyday Spanish that works in Spain and in Latin America (\"ustedes\" for a group, no "
                   "\"vosotros\"). The speech check listens for Spanish from Spain and understands other accents too.",
    },
    "it": {
        "name": "Italian", "native": "Italiano", "short": "IT", "tts": "it-IT", "asr": "it-IT",
        "flag": ["#009246", "#ffffff", "#ce2b37"], "stripes": "v",
        "formal": "Lei", "familiar": "tu", "we": "noi", "love": "amore mio",
        "formal_words": [], "formal_cased": ["Lei", "Suo", "Sua", "Suoi", "Sue"], "formal_clitics": True,
        "familiar_words": ["tu", "ti", "te", "tuo", "tua", "tuoi", "tue"], "familiar_prefixes": ["t'"],
        "formal_weak": [], "formal_suffixes": [], "familiar_suffixes": [], "suffix_exceptions": [],
        "praise": ["Molto bene!", "Bravo!", "Ottimo!", "Perfetto!"],
        "very_good": "Molto bene!", "perfect": "Perfetto!", "well_done": "Ben fatto!", "bye": "A presto!",
        "places": "Rome, Milan, Naples or Lugano",
        "variety": "Standard, everyday Italian. Formal \"Lei\" is written with a capital L (aiutarLa, la Sua "
                   "domanda), so you can spot it. The speech check listens for Italian from Italy.",
    },
}


def valid(code):
    return code if code in LANGS else DEFAULT


def info(code):
    return LANGS[valid(code)]


def name(code):
    return info(code)["name"]


def names_list():
    """'French, Spanish and Italian'."""
    n = [LANGS[c]["name"] for c in CODES]
    return ", ".join(n[:-1]) + " and " + n[-1] if len(n) > 1 else n[0]


_PUNCT = ".,;:!?()\"«»“”…¿¡"
_ENDS = ".!?…"


def _sentences(text):
    """The text split into sentences, each a list of words with their case kept (apostrophes made straight)."""
    s = (text or "").replace("’", "'")
    out, cur = [], ""
    for ch in s:
        if ch in _ENDS:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    result = []
    for part in out:
        for ch in _PUNCT:
            part = part.replace(ch, " ")
        words = [w for w in part.split() if w]
        if words:
            result.append(words)
    return result


def _formal_clitic(word):
    """Italian formal pronouns glued to a verb keep their capital: aiutarLa, darLe, offrirLe, ringraziarLa."""
    for end in ("La", "Le", "Lo", "Gli"):
        if len(word) > len(end) + 2 and word.endswith(end) and word[:-len(end)].islower():
            return True
    return False


def _ends(word, endings, exceptions):
    return word not in exceptions and any(len(word) > len(e) and word.endswith(e) for e in endings)


def register(text, code=DEFAULT):
    """'formal' (vous / usted / Lei), 'familiar' (tu / tú / tu), 'mixed', or '' when the sentence shows neither.
    Spanish and Italian often leave the pronoun out, so a sentence can be formal without showing it. Spanish "le"
    and verbs ending in -rle (ayudarle) only count as formal when nothing in the sentence is familiar ("le" can
    also mean him or her)."""
    L = info(code)
    formal_words, familiar_words, exc = set(L["formal_words"]), set(L["familiar_words"]), set(L["suffix_exceptions"])
    formal = familiar = weak = False
    for words in _sentences(text):
        for i, w in enumerate(words):
            lw = w.lower()
            if lw in formal_words or w in L["formal_cased"]:
                formal = True
            elif L["formal_clitics"] and (_formal_clitic(w) or (i > 0 and w in ("La", "Le"))):
                formal = True
            elif (lw in familiar_words or any(lw.startswith(p) for p in L["familiar_prefixes"])
                  or _ends(lw, L["familiar_suffixes"], exc)):
                familiar = True
            elif lw in L["formal_weak"] or _ends(lw, L["formal_suffixes"], exc):
                weak = True
    if formal and familiar:
        return "mixed"
    if formal or (weak and not familiar):
        return "formal"
    return "familiar" if familiar else ""


def register_text(reg, code=DEFAULT):
    L = info(code)
    return {"formal": "%s · formal" % L["formal"], "familiar": "%s · familiar" % L["familiar"],
            "mixed": "%s + %s" % (L["familiar"], L["formal"]), "": ""}.get(reg or "", "")


def flag_css(code):
    """A little flag drawn with CSS (no emoji: Windows shows emoji flags as two letters)."""
    L = info(code)
    a, b, c = L["flag"]
    if L["stripes"] == "h":
        return "linear-gradient(180deg, %s 0 25%%, %s 25%% 75%%, %s 75%%)" % (a, b, c)
    return "linear-gradient(90deg, %s 0 33.4%%, %s 33.4%% 66.6%%, %s 66.6%%)" % (a, b, c)


def for_js(code):
    """What the card engine (pp-card.js, PP.setLang) needs to label and read the cards."""
    L = info(code)
    return {"code": valid(code), "name": L["name"], "short": L["short"], "tts": L["tts"], "asr": L["asr"],
            "formal": L["formal"], "familiar": L["familiar"], "formalWords": list(L["formal_words"]),
            "formalCased": list(L["formal_cased"]), "formalClitics": bool(L["formal_clitics"]),
            "familiarWords": list(L["familiar_words"]), "familiarPrefixes": list(L["familiar_prefixes"]),
            "formalWeak": list(L["formal_weak"]), "formalSuffixes": list(L["formal_suffixes"]),
            "familiarSuffixes": list(L["familiar_suffixes"]), "suffixExceptions": list(L["suffix_exceptions"])}
