"""The ten moods every Parapeet phrase comes in. Plain Python (no Anvil imports): the browser and the server share it.

The keys are the database column names of the phrase tables (FrenchSentences, SpanishSentences, ItalianSentences and
FrenchSentences_translation; spelling kept, including "Agressive"). Most columns describe WHO you are talking to or
the situation (a client, your boss, someone angry, a sad friend, your partner), not your own feelings. The labels
below say that in plain words. Blurbs use {lang}, {formal}, {familiar}, {we} and {love} from langs.py; the "listen"
hints quote real words from each language's phrases, so they're written per language.
"""
from . import langs

KEYS = ["Basic", "Colleague", "Client", "Boss", "Agressive", "Frustrated", "Sad", "Lover", "Impressed", "Stupid"]

TONES: dict = {
    "Basic": {
        "label": "Neutral", "icon": "leaf", "colour": "#3f9a3a", "ink": "#ffffff",
        "who": "anyone",
        "blurb": "Plain, everyday {lang}. The version you could say to anyone, and the one the other moods start from.",
        "listen": {"fr": "The core sentence. Compare every other mood with this one.",
                   "es": "The core sentence. Compare every other mood with this one.",
                   "it": "The core sentence. Compare every other mood with this one."},
        "names": {"fr": "Neutre", "es": "Neutro", "it": "Neutro"},
    },
    "Colleague": {
        "label": "Colleague", "icon": "users", "colour": "#2f7fe0", "ink": "#ffffff",
        "who": "a colleague",
        "blurb": "Team talk at work: friendly, practical, often with \"{we}\". It moves the work forward.",
        "listen": {"fr": "Plans and next steps: \"je voulais\", \"nous devons\", \"assurez-vous\".",
                   "es": "Plans and next steps: \"quería\", \"debemos\", \"asegúrese\".",
                   "it": "Plans and next steps: \"volevo\", \"dobbiamo\", \"si assicuri\"."},
        "names": {"fr": "Collègue", "es": "Colega", "it": "Collega"},
    },
    "Client": {
        "label": "Client", "icon": "handshake", "colour": "#0e9a9a", "ink": "#ffffff",
        "who": "a client",
        "blurb": "Your service voice: polite \"{formal}\", offers to help, reassures, never blames.",
        "listen": {"fr": "Offers and promises: \"je suis là pour\", \"je vais vérifier\", \"nous nous excusons\".",
                   "es": "Offers and promises: \"estoy aquí para\", \"voy a verificar\", \"le pedimos disculpas\".",
                   "it": "Offers and promises: \"sono qui per\", \"verifico subito\", \"ci scusiamo\"."},
        "names": {"fr": "Client", "es": "Cliente", "it": "Cliente"},
    },
    "Boss": {
        "label": "Boss", "icon": "crown", "colour": "#26346f", "ink": "#ffffff",
        "who": "your boss",
        "blurb": "Speaking up the ladder: respectful \"{formal}\", careful, constructive.",
        "listen": {"fr": "Careful framing: \"j'ai besoin de m'assurer\", \"veuillez\", \"je suis là pour vous aider\".",
                   "es": "Careful framing: \"necesito asegurarme\", \"por favor, revíselo\", \"con su permiso\".",
                   "it": "Careful framing: \"devo assicurarmi\", \"La prego di\", \"con il Suo permesso\"."},
        "names": {"fr": "Patron", "es": "Jefe", "it": "Capo"},
    },
    "Agressive": {
        "label": "Hothead", "icon": "flame", "colour": "#d93d43", "ink": "#ffffff",
        "who": "someone who's angry",
        "blurb": "Calming someone who is upset: name their feeling first, then steer back to the point.",
        "listen": {"fr": "The pattern \"je comprends que tu sois énervé, mais...\": acknowledge, then \"mais\".",
                   "es": "The pattern \"entiendo que estés molesto, pero...\": acknowledge, then \"pero\".",
                   "it": "The pattern \"capisco che tu sia arrabbiato, ma...\": acknowledge, then \"ma\"."},
        "names": {"fr": "Tête brûlée", "es": "Cabeza caliente", "it": "Testa calda"},
    },
    "Frustrated": {
        "label": "Frustrated", "icon": "storm", "colour": "#e07b22", "ink": "#ffffff",
        "who": "a tense situation",
        "blurb": "When it's getting tense: stay firm and constructive without snapping back.",
        "listen": {"fr": "Firm but fair: \"je ne cherche qu'à\", \"malgré\", \"je sais que tu es contrarié\".",
                   "es": "Firm but fair: \"solo intento\", \"a pesar de\", \"sé que estás molesto\".",
                   "it": "Firm but fair: \"cerco solo di\", \"nonostante\", \"so che sei contrariato\"."},
        "names": {"fr": "Frustré", "es": "Frustrado", "it": "Frustrato"},
    },
    "Sad": {
        "label": "Comfort", "icon": "umbrella", "colour": "#4f74b0", "ink": "#ffffff",
        "who": "someone who's sad",
        "blurb": "Gentle with someone who's down: soft openers, no pressure, an offer to help.",
        "listen": {"fr": "Soft openers: \"je sais que tu es triste\", \"prends ton temps\", \"je suis là pour toi\".",
                   "es": "Soft openers: \"sé que estás triste\", \"tómate tu tiempo\", \"estaré ahí para ti\".",
                   "it": "Soft openers: \"so che sei triste\", \"prenditi il tuo tempo\", \"ci sarò per te\"."},
        "names": {"fr": "Réconfort", "es": "Consuelo", "it": "Conforto"},
    },
    "Lover": {
        "label": "Lover", "icon": "heart", "colour": "#d44a8f", "ink": "#ffffff",
        "who": "your partner",
        "blurb": "Soft and tender: \"{familiar}\", warmth, sometimes a \"{love}\". The same request, said with love.",
        "listen": {"fr": "Tenderness: \"tu\" instead of \"vous\", \"mon amour\", softer requests.",
                   "es": "Tenderness: \"tú\" instead of \"usted\", \"mi amor\", softer requests.",
                   "it": "Tenderness: \"tu\" instead of \"Lei\", \"amore mio\", softer requests."},
        "names": {"fr": "Amoureux", "es": "Enamorado", "it": "Innamorato"},
    },
    "Impressed": {
        "label": "Admiring", "icon": "star", "colour": "#c48a00", "ink": "#1d1600",
        "who": "someone you admire",
        "blurb": "Warm praise and enthusiasm: you're impressed, or you want to impress.",
        "listen": {"fr": "Praise words: \"ravi\", \"excellente\", \"impressionnant\", \"je t'en serais reconnaissant\".",
                   "es": "Praise words: \"me alegra\", \"excelente\", \"impresionante\", \"te lo agradecería\".",
                   "it": "Praise words: \"felicissimo\", \"ottimo\", \"impressionante\", \"te ne sarei grato\"."},
        "names": {"fr": "Admiratif", "es": "Admirado", "it": "Ammirato"},
    },
    "Stupid": {
        "label": "Silly", "icon": "party", "colour": "#8a55d6", "ink": "#ffffff",
        "who": "a friend, for a laugh",
        "blurb": "Goofy and playful: wild pictures (dragons, potions, hamsters in wheels). Friends only!",
        "listen": {"fr": "Fun images and slang: \"pigé\", \"la panse\", \"le grand chef\", \"la grotte des données\".",
                   "es": "Fun images: \"los engranajes de tu cerebro\", \"llenar la panza\", \"el gran jefe\", \"la cueva de los datos\".",
                   "it": "Fun images: \"le rotelle nel tuo cervello\", \"riempirmi la pancia\", \"il grande capo\", \"la grotta dei dati\"."},
        "names": {"fr": "Rigolo", "es": "Payaso", "it": "Buffone"},
    },
}

UNITS = {
    1: {"name": "Water cooler", "icon": "coffee", "blurb": "Small talk, favours and everyday office life."},
    2: {"name": "Presentation", "icon": "presentation", "blurb": "Presenting, explaining and taking questions."},
    3: {"name": "Board room", "icon": "crown", "blurb": "Meetings, decisions and delicate conversations."},
}


def label(key):
    return TONES.get(key, {}).get("label", key)


def blurb(key, code=langs.DEFAULT):
    """The mood explained, with this language's words filled in ("polite usted")."""
    L = langs.info(code)
    text = TONES.get(key, {}).get("blurb", "")
    for k, v in (("{lang}", L["name"]), ("{formal}", L["formal"]), ("{familiar}", L["familiar"]), ("{we}", L["we"]),
                 ("{love}", L["love"])):
        text = text.replace(k, v)
    return text


def listen_hint(key, code=langs.DEFAULT):
    hints = TONES.get(key, {}).get("listen") or {}
    return hints.get(langs.valid(code)) or hints.get(langs.DEFAULT, "")


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
