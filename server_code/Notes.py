"""My phrasebook: phrases a member saved (UserNotes: French, Comment = the meaning or a note, Level 0-5 from the
quiz, User = the owner's email). Members only; everyone only ever sees and changes their own rows.
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C

MAX_NOTES = 1000


def _email(user):
    return user["email"] or ""


def _dict(r):
    return {"id": r.get_id(), "fr": r["French"] or "", "en": r["Comment"] or "", "level": int(r["Level"] or 0)}


def _mine(note_id, user):
    r = C.row_by_id(app_tables.usernotes, note_id)
    if r is None or r["User"] != _email(user):
        return None
    return r


@anvil.server.callable(require_user=True)
def list_notes():
    user = C.require_user()
    rows = [_dict(r) for r in app_tables.usernotes.search(User=_email(user))]
    rows.reverse()  # newest first
    return {"notes": rows}


@anvil.server.callable(require_user=True)
def add_note(fr, en):
    user = C.require_user()
    fr, en = C.text(fr, 400), C.text(en, 600, multiline=True)
    if not fr or not en:
        return C.fail("Fill in both the French and what it means.")
    same = app_tables.usernotes.get(User=_email(user), French=fr) if fr else None
    if same is not None:
        same["Comment"] = en
        return C.ok(note=_dict(same), existed=True)
    if len(app_tables.usernotes.search(User=_email(user))) >= MAX_NOTES:
        return C.fail("Your phrasebook is full (%d phrases). Remove a few first." % MAX_NOTES)
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
        return C.fail("Fill in both the French and what it means.")
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
