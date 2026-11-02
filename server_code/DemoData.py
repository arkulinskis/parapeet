"""Sample content for an empty database (local tests, or a fresh copy of the app). The live app has its own phrase
library, so on parapeet.com this never does anything: ensure_loaded() only fills FrenchSentences and
FrenchSentences_translation when BOTH are completely empty.
"""
import typing

from anvil.tables import app_tables

from . import common as C
from . import sample_phrases, tones


def ensure_loaded():
    if C.get_setting("sample_checked", False):
        return
    if len(app_tables.frenchsentences.search()) == 0 and len(app_tables.frenchsentences_translation.search()) == 0:
        load()
    C.set_setting("sample_checked", True)


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
    return counts()


def counts():
    """{"by_access": {"basic": n, ...}, "by_unit": {"1": n, ...}, "voices_fr": n, "voices_en": n}"""
    access, units = {}, {}
    for r in app_tables.frenchsentences.search():
        a = (r["Availability"] or "?").strip().lower()
        access[a] = access.get(a, 0) + 1
        u = str(int(r["CategoryID"] or 0))
        units[u] = units.get(u, 0) + 1
    return {"by_access": access, "by_unit": units, "voices_fr": len(app_tables.voicefiles.search()),
            "voices_en": len(app_tables.voicefiles_english.search())}
