"""Sample content for an empty database (local tests, or a fresh copy of the app), and the first Spanish and Italian
phrases for the live app.

ensure_loaded() fills FrenchSentences and FrenchSentences_translation only when BOTH are completely empty (the live
app has its own library, so there it never adds French). ensure_languages() then fills SpanishSentences and
ItalianSentences from sample_phrases.py while one of them is empty, but only with phrases whose French in the database
is word for word the sample's French, so a translation can never land on a different phrase.
"""
import typing

from anvil.tables import app_tables

from . import common as C
from . import langs, sample_phrases, tones

OTHER = ("es", "it")


def ensure_loaded():
    if not C.get_setting("sample_checked", False):
        if len(app_tables.frenchsentences.search()) == 0 and len(app_tables.frenchsentences_translation.search()) == 0:
            load()
        C.set_setting("sample_checked", True)
    if not C.get_setting("sample_langs_checked", False):
        if ensure_languages():
            C.set_setting("sample_langs_checked", True)


def load():
    """Add the sample phrases (only into empty tables). Returns the library's counts."""
    if len(app_tables.frenchsentences.search()) or len(app_tables.frenchsentences_translation.search()):
        return counts()
    for row in sample_phrases.PHRASES:
        p: typing.Any = row
        fr = dict(zip(tones.KEYS, p["fr"]))
        en = dict(zip(tones.KEYS, p["en"]))
        app_tables.frenchsentences.add_row(LineID=p["id"], CategoryID=p["cat"], Availability=p["avail"], **fr)
        app_tables.frenchsentences_translation.add_row(LineID=p["id"], CategoryID=p["cat"], Availability=p["avail"], **en)
    ensure_languages()
    return counts()


def _same(a, b):
    return " ".join((a or "").replace("’", "'").split()) == " ".join((b or "").replace("’", "'").split())


def ensure_languages():
    """Sample Spanish and Italian for each empty language table. Returns False while a table doesn't exist yet
    (before the Schema Mismatch alert is accepted), so it's tried again on the next visit."""
    from . import Phrases
    done, french = True, None
    for code in OTHER:
        t = Phrases.table(code)
        if t is None:
            done = False
            continue
        try:
            if len(t.search()):
                continue
            if french is None:
                french = dict((int(r["LineID"]), r["Basic"]) for r in app_tables.frenchsentences.search()
                              if r["LineID"] is not None)
            for row in sample_phrases.PHRASES:
                p: typing.Any = row
                if code in p and _same(french.get(p["id"]), p["fr"][0]):
                    t.add_row(LineID=p["id"], CategoryID=p["cat"], Availability=p["avail"],
                              **dict(zip(tones.KEYS, p[code])))
        except Exception:
            done = False
    return done


def counts():
    """{"by_access": {"basic": n, ...}, "by_unit": {"1": n, ...}, "voices_fr": n, "voices_en": n,
    "languages": [{code, name, phrases, voices, missing, ready}]} (missing = French phrases not translated yet,
    ready = the language's table exists)."""
    from . import Phrases
    access, units = {}, {}
    french_ids = set()
    for r in app_tables.frenchsentences.search():
        a = (r["Availability"] or "?").strip().lower()
        access[a] = access.get(a, 0) + 1
        u = str(int(r["CategoryID"] or 0))
        units[u] = units.get(u, 0) + 1
        if r["LineID"] is not None:
            french_ids.add(int(r["LineID"]))
    languages = []
    for code in langs.CODES:
        ids = set(int(r["LineID"]) for r in Phrases.rows(code) if r["LineID"] is not None)
        voices = Phrases.voice_table(code)
        try:
            n_voices = len(voices.search()) if voices is not None else 0
        except Exception:
            n_voices = 0
        languages.append({"code": code, "name": langs.name(code), "phrases": len(ids), "voices": n_voices,
                          "missing": len(french_ids - ids), "ready": Phrases.table(code) is not None})
    return {"by_access": access, "by_unit": units, "voices_fr": len(app_tables.voicefiles.search()),
            "voices_en": len(app_tables.voicefiles_english.search()), "languages": languages}
