"""The phrase library and its recorded voices, read-only (the content is edited in the Anvil data tables).

FrenchSentences / FrenchSentences_translation: one row per phrase (LineID), CategoryID = the unit, Availability =
"basic" (everyone, even signed out), "free" (any account) or "premium" (customer_type "premium"), and one text column
per mood (tones.KEYS). VoiceFiles / VoiceFiles_english: a recording per LineID (stored as text) and mood (Type).
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import DemoData, tones

LEVELS = {"basic": ["basic"], "free": ["basic", "free"], "premium": ["basic", "free", "premium"]}


def level_of(user):
    if user is None:
        return "basic"
    kind = (user["customer_type"] or "").strip().lower()
    return "premium" if kind == "premium" else "free"


def _avail(row):
    return (row["Availability"] or "").strip().lower()


def _texts(row):
    return dict((k, (row[k] or "").strip() if row is not None else "") for k in tones.KEYS)


@anvil.server.callable
def get_phrases():
    """Every phrase this person may use, French and English side by side, plus how many are still locked per unit
    ("signup": an account unlocks them, "premium": not available yet)."""
    DemoData.ensure_loaded()
    level = level_of(C.me())
    allowed = LEVELS[level]
    english = {}
    for r in app_tables.frenchsentences_translation.search():
        if r["LineID"] is not None:
            english[int(r["LineID"])] = r
    phrases, locked = [], {"signup": {}, "premium": {}}
    for r in app_tables.frenchsentences.search():
        if r["LineID"] is None:
            continue
        cat = int(r["CategoryID"] or 1)
        avail = _avail(r)
        if avail not in allowed:
            group = "signup" if (level == "basic" and avail == "free") else "premium"
            locked[group][str(cat)] = locked[group].get(str(cat), 0) + 1
            continue
        line_id = int(r["LineID"])
        fr = _texts(r)
        if not fr["Basic"]:
            continue
        phrases.append({"id": line_id, "cat": cat, "fr": fr, "en": _texts(english.get(line_id))})
    phrases.sort(key=lambda p: (p["cat"], p["id"]))
    return {"level": level, "phrases": phrases, "locked": locked}


def _first(rows):
    for r in rows:
        return r
    return None


@anvil.server.callable
def voice_url(line_id, mood, lang="fr"):
    """A temporary link to the recorded voice of this phrase in this mood, or None (the browser's voice is used)."""
    if mood not in tones.KEYS or lang not in ("fr", "en"):
        return None
    try:
        line_id = int(line_id)
    except Exception:
        return None
    row = _first(app_tables.frenchsentences.search(LineID=line_id))
    if row is None or _avail(row) not in LEVELS[level_of(C.me())]:
        return None
    table = app_tables.voicefiles if lang == "fr" else app_tables.voicefiles_english
    voice = _first(table.search(LineID=str(line_id), Type=mood))
    if voice is None or voice["VoiceFile"] is None:
        return None
    try:
        return voice["VoiceFile"].get_url()
    except Exception:
        return None
