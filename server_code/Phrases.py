"""The phrase library and its recorded voices, read-only here (the content is edited in the Anvil data tables, or
uploaded as a CSV file on Admin -> Phrases: PhraseFiles.py).

One table of texts per language (TABLES): FrenchSentences, SpanishSentences, ItalianSentences, same columns: one row
per phrase (LineID), CategoryID = the unit, Availability = "basic" (everyone, even signed out), "free" (any account)
or "premium" (customer_type "premium"), and one text column per mood (tones.KEYS). A phrase keeps its LineID in every
language, so FrenchSentences_translation holds the English for all three. A Spanish or Italian row with no
CategoryID / Availability of its own takes the French row's. Voices: a recording per LineID (stored as text) and mood
(Type) in VoiceFiles (French), VoiceFiles_spanish, VoiceFiles_italian and VoiceFiles_english.
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import DemoData, langs, tones

LEVELS = {"basic": ["basic"], "free": ["basic", "free"], "premium": ["basic", "free", "premium"]}
TABLES = {"fr": ("frenchsentences", "voicefiles"), "es": ("spanishsentences", "voicefiles_spanish"),
          "it": ("italiansentences", "voicefiles_italian")}


def table(code):
    """The text table of a language, or None while it doesn't exist yet (new tables appear once the Schema Mismatch
    alert is accepted in the Anvil editor)."""
    try:
        return getattr(app_tables, TABLES[langs.valid(code)][0])
    except Exception:
        return None


def voice_table(code):
    try:
        return getattr(app_tables, "voicefiles_english" if code == "en" else TABLES[langs.valid(code)][1])
    except Exception:
        return None


def rows(code):
    t = table(code)
    if t is None:
        return []
    try:
        return list(t.search())
    except Exception:
        return []


def level_of(user):
    if user is None:
        return "basic"
    kind = (user["customer_type"] or "").strip().lower()
    return "premium" if kind == "premium" else "free"


def _avail(row):
    return (row["Availability"] or "").strip().lower()


def _texts(row):
    return dict((k, (row[k] or "").strip() if row is not None else "") for k in tones.KEYS)


def _meta(row, french):
    """(unit, availability) of a phrase: its own, else the French row's. No availability at all = locked, as before."""
    cat = row["CategoryID"] if row["CategoryID"] is not None else (french["CategoryID"] if french is not None else None)
    avail = _avail(row) or (_avail(french) if french is not None else "")
    return int(cat or 1), avail


def counts():
    """{"fr": phrases, "es": ..., "it": ...}, for the language picker."""
    return dict((c, len(rows(c))) for c in langs.CODES)


@anvil.server.callable
def get_phrases(lang="fr"):
    """Every phrase this person may use in one language, side by side with the English, plus how many are still
    locked per unit ("signup": an account unlocks them, "premium": not available yet) and how many phrases each
    language has."""
    DemoData.ensure_loaded()
    lang = langs.valid(lang)
    level = level_of(C.me())
    allowed = LEVELS[level]
    english, french = {}, {}
    for r in app_tables.frenchsentences_translation.search():
        if r["LineID"] is not None:
            english[int(r["LineID"])] = r
    if lang != "fr":
        for r in app_tables.frenchsentences.search():
            if r["LineID"] is not None:
                french[int(r["LineID"])] = r
    phrases, locked = [], {"signup": {}, "premium": {}}
    for r in rows(lang):
        if r["LineID"] is None:
            continue
        line_id = int(r["LineID"])
        cat, avail = _meta(r, french.get(line_id))
        if avail not in allowed:
            group = "signup" if (level == "basic" and avail == "free") else "premium"
            locked[group][str(cat)] = locked[group].get(str(cat), 0) + 1
            continue
        texts = _texts(r)
        if not texts["Basic"]:
            continue
        phrases.append({"id": line_id, "cat": cat, "lang": lang, "fr": texts, "en": _texts(english.get(line_id))})
    phrases.sort(key=lambda p: (p["cat"], p["id"]))
    return {"level": level, "lang": lang, "phrases": phrases, "locked": locked, "counts": counts()}


def _first(found):
    for r in found:
        return r
    return None


@anvil.server.callable
def voice_url(line_id, mood, lang="fr"):
    """A temporary link to the recorded voice of this phrase in this mood ("fr", "es", "it" or "en"), or None (then
    the browser's voice reads it)."""
    if mood not in tones.KEYS or lang not in langs.CODES + ["en"]:
        return None
    try:
        line_id = int(line_id)
    except Exception:
        return None
    text_lang = "fr" if lang == "en" else lang
    t = table(text_lang)
    row = _first(t.search(LineID=line_id)) if t is not None else None
    if row is None:
        return None
    french = _first(app_tables.frenchsentences.search(LineID=line_id)) if text_lang != "fr" else row
    if _meta(row, french)[1] not in LEVELS[level_of(C.me())]:
        return None
    voices = voice_table(lang)
    if voices is None:
        return None
    try:
        voice = _first(voices.search(LineID=str(line_id), Type=mood))
        if voice is None or voice["VoiceFile"] is None:
            return None
        return voice["VoiceFile"].get_url()
    except Exception:
        return None
