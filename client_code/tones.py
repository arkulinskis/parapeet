"""The ten moods every Parapeet phrase comes in. Plain Python (no Anvil imports): the browser and the server share it.

The keys are the database column names of FrenchSentences / FrenchSentences_translation (spelling kept, including
"Agressive"). Most columns describe WHO you are talking to or the situation (a client, your boss, someone angry,
a sad friend, your partner), not your own feelings. The labels below say that in plain words.
"""

KEYS = ["Basic", "Colleague", "Client", "Boss", "Agressive", "Frustrated", "Sad", "Lover", "Impressed", "Stupid"]

TONES = {
    "Basic": {
        "label": "Neutral", "icon": "leaf", "colour": "#3f9a3a", "ink": "#ffffff",
        "who": "anyone",
        "blurb": "Plain, everyday French. The version you could say to anyone, and the one the other moods start from.",
        "listen": "The core sentence. Compare every other mood with this one.",
        "fr": "Neutre",
    },
    "Colleague": {
        "label": "Colleague", "icon": "users", "colour": "#2f7fe0", "ink": "#ffffff",
        "who": "a colleague",
        "blurb": "Team talk at work: friendly, practical, often with \"nous\". It moves the work forward.",
        "listen": "Plans and next steps: \"je voulais\", \"nous devons\", \"assurez-vous\".",
        "fr": "Collègue",
    },
    "Client": {
        "label": "Client", "icon": "handshake", "colour": "#0e9a9a", "ink": "#ffffff",
        "who": "a client",
        "blurb": "Your service voice: polite \"vous\", offers to help, reassures, never blames.",
        "listen": "Offers and promises: \"je suis là pour\", \"je vais vérifier\", \"nous nous excusons\".",
        "fr": "Client",
    },
    "Boss": {
        "label": "Boss", "icon": "crown", "colour": "#26346f", "ink": "#ffffff",
        "who": "your boss",
        "blurb": "Speaking up the ladder: respectful \"vous\", careful, constructive.",
        "listen": "Careful framing: \"j'ai besoin de m'assurer\", \"veuillez\", \"je suis là pour vous aider\".",
        "fr": "Patron",
    },
    "Agressive": {
        "label": "Hothead", "icon": "flame", "colour": "#d93d43", "ink": "#ffffff",
        "who": "someone who's angry",
        "blurb": "Calming someone who is upset: name their feeling first, then steer back to the point.",
        "listen": "The pattern \"je comprends que tu sois énervé, mais...\": acknowledge, then \"mais\".",
        "fr": "Tête brûlée",
    },
    "Frustrated": {
        "label": "Frustrated", "icon": "storm", "colour": "#e07b22", "ink": "#ffffff",
        "who": "a tense situation",
        "blurb": "When it's getting tense: stay firm and constructive without snapping back.",
        "listen": "Firm but fair: \"je ne cherche qu'à\", \"malgré\", \"je sais que tu es contrarié\".",
        "fr": "Frustré",
    },
    "Sad": {
        "label": "Comfort", "icon": "umbrella", "colour": "#4f74b0", "ink": "#ffffff",
        "who": "someone who's sad",
        "blurb": "Gentle with someone who's down: soft openers, no pressure, an offer to help.",
        "listen": "Soft openers: \"je sais que tu es triste\", \"prends ton temps\", \"je suis là pour toi\".",
        "fr": "Réconfort",
    },
    "Lover": {
        "label": "Lover", "icon": "heart", "colour": "#d44a8f", "ink": "#ffffff",
        "who": "your partner",
        "blurb": "Soft and tender: \"tu\", warmth, sometimes a \"mon amour\". The same request, said with love.",
        "listen": "Tenderness: \"tu\" instead of \"vous\", \"mon amour\", softer requests.",
        "fr": "Amoureux",
    },
    "Impressed": {
        "label": "Admiring", "icon": "star", "colour": "#c48a00", "ink": "#1d1600",
        "who": "someone you admire",
        "blurb": "Warm praise and enthusiasm: you're impressed, or you want to impress.",
        "listen": "Praise words: \"ravi\", \"excellente\", \"impressionnant\", \"je t'en serais reconnaissant\".",
        "fr": "Admiratif",
    },
    "Stupid": {
        "label": "Silly", "icon": "party", "colour": "#8a55d6", "ink": "#ffffff",
        "who": "a friend, for a laugh",
        "blurb": "Goofy and playful: wild pictures (dragons, potions, hamsters in wheels). Friends only!",
        "listen": "Fun images and slang: \"pigé\", \"la panse\", \"le grand chef\", \"la grotte des données\".",
        "fr": "Rigolo",
    },
}

UNITS = {
    1: {"name": "Water cooler", "icon": "coffee", "blurb": "Small talk, favours and everyday office life."},
    2: {"name": "Presentation", "icon": "presentation", "blurb": "Presenting, explaining and taking questions."},
    3: {"name": "Board room", "icon": "crown", "blurb": "Meetings, decisions and delicate conversations."},
}


def label(key):
    return TONES.get(key, {}).get("label", key)


def index_of(key):
    return KEYS.index(key) if key in KEYS else 0


def key_for_label(text):
    """'boss', 'Hothead', 'Agressive' -> the column key, or None."""
    t = (text or "").strip().lower()
    for k in KEYS:
        if t in (k.lower(), TONES[k]["label"].lower()):
            return k
    return None


def as_list():
    """What the JavaScript card engine needs: [{key, label, icon, colour, ink}] in column order."""
    return [{"key": k, "label": TONES[k]["label"], "icon": TONES[k]["icon"], "colour": TONES[k]["colour"],
             "ink": TONES[k]["ink"]} for k in KEYS]


_PUNCT = ".,;:!?()\"«»“”…"


def tokens(text):
    s = (text or "").lower().replace("’", "'")
    for ch in _PUNCT:
        s = s.replace(ch, " ")
    return [w for w in s.split() if w]


TU = {"tu", "te", "toi", "ton", "ta", "tes"}
VOUS = {"vous", "votre", "vos"}


def register(text):
    """'vous' (formal), 'tu' (familiar) or '' when the sentence uses neither."""
    has_tu = has_vous = False
    for w in tokens(text):
        if w in VOUS:
            has_vous = True
        elif w in TU or w.startswith("t'"):
            has_tu = True
    if has_vous and not has_tu:
        return "vous"
    if has_tu and not has_vous:
        return "tu"
    return "mixed" if (has_tu and has_vous) else ""


REGISTER_TEXT = {"vous": "vous · formal", "tu": "tu · familiar", "mixed": "tu + vous", "": "no tu / vous"}
