"""My phrasebook: phrases a member saved (UserNotes: French = the phrase, in whichever language Lang says; Comment =
the meaning or a note; Lang = "fr", "es" or "it", empty for French saved before Spanish and Italian came; Level 0-5
from the quiz; User = the owner's email). Each language has its own phrasebook. Members only; everyone only ever sees
and changes their own rows.
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import langs

MAX_NOTES = 1000


def _email(user):
    return user["email"] or ""


def _lang(r):
    """The note's language. Safe before the Lang column exists (until the Schema Mismatch alert is accepted)."""
    try:
        return langs.valid(r["Lang"] or langs.DEFAULT)
    except Exception:
        return langs.DEFAULT


def _dict(r):
    return {"id": r.get_id(), "fr": r["French"] or "", "en": r["Comment"] or "", "level": int(r["Level"] or 0),
            "lang": _lang(r)}


def _mine(note_id, user):
    r = C.row_by_id(app_tables.usernotes, note_id)
    if r is None or r["User"] != _email(user):
        return None
    return r


@anvil.server.callable(require_user=True)
def list_notes(lang="fr"):
    """This member's saved phrases in one language, newest first."""
    user = C.require_user()
    lang = langs.valid(lang)
    rows = [_dict(r) for r in app_tables.usernotes.search(User=_email(user)) if _lang(r) == lang]
    rows.reverse()  # newest first
    return {"notes": rows}


@anvil.server.callable(require_user=True)
def add_note(fr, en, lang="fr"):
    user = C.require_user()
    lang = langs.valid(lang)
    fr, en = C.text(fr, 400), C.text(en, 600, multiline=True)
    if not fr or not en:
        return C.fail("Fill in both the %s and what it means." % langs.name(lang))
    same = [r for r in app_tables.usernotes.search(User=_email(user), French=fr) if _lang(r) == lang]
    if same:
        same[0]["Comment"] = en
        return C.ok(note=_dict(same[0]), existed=True)
    if len(app_tables.usernotes.search(User=_email(user))) >= MAX_NOTES:
        return C.fail("Your phrasebook is full (%d phrases). Remove a few first." % MAX_NOTES)
    try:
        r = app_tables.usernotes.add_row(User=_email(user), French=fr, Comment=en, Level=0, Lang=lang)
    except Exception:  # no Lang column yet (Schema Mismatch not accepted): keep it anyway
        r = app_tables.usernotes.add_row(User=_email(user), French=fr, Comment=en, Level=0)
    return C.ok(note=_dict(r), existed=False)


@anvil.server.callable(require_user=True)
def edit_note(note_id, fr, en):
    user = C.require_user()
    r = _mine(note_id, user)
    if r is None:
        return C.fail("That phrase isn't in your phrasebook any more.")
    fr, en = C.text(fr, 400), C.text(en, 600, multiline=True)
    if not fr or not en:
        return C.fail("Fill in both the %s and what it means." % langs.name(_lang(r)))
    r.update(French=fr, Comment=en)
    return C.ok(note=_dict(r))


@anvil.server.callable(require_user=True)
def remove_note(note_id):
    user = C.require_user()
    r = _mine(note_id, user)
    if r is not None:
        r.delete()
    return C.ok()


@anvil.server.callable(require_user=True)
def note_result(note_id, right):
    """The phrasebook quiz: a right answer raises the phrase's level (max 5), a wrong one lowers it."""
    user = C.require_user()
    r = _mine(note_id, user)
    if r is None:
        return C.fail("That phrase isn't in your phrasebook any more.")
    level = int(r["Level"] or 0)
    r["Level"] = min(5, level + 1) if right else max(0, level - 1)
    return C.ok(note=_dict(r))


def count():
    return len(app_tables.usernotes.search())
