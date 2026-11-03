"""Members' progress: one `progress` row each (seeds, streak, daily goal, mastery, lesson stars, badges, stats).

The rules live in client_code/gamerules.py, shared with the browser (guests use the same functions locally).
The first time someone who used the old Parapeet opens the new one, their likes and "spoken" marks from UserPoints
become mastery and seeds, so nobody starts from zero.
"""
import datetime as dt
import re

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import gamerules as G
from . import langs, tones

COLUMNS = ["seeds", "streak", "best_streak", "last_day", "today", "today_seeds", "daily_goal", "mastery", "lessons",
           "badges", "stats", "adventurer"]


def _today(value):
    """The learner's date if it's sane (within a day or two of the server's), else the server's UTC date."""
    server = C.now().date()
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        try:
            d = dt.date(int(value[:4]), int(value[5:7]), int(value[8:10]))
            if abs((d - server).days) <= 2:
                return value
        except ValueError:
            pass
    return server.isoformat()


def _from_userpoints(user):
    """The old app's per-user digits: 0 nothing, 1 liked, 2 said right, 3 both. Index = LineID."""
    p = G.blank()
    old = app_tables.userpoints.get(user=user["email"]) if user["email"] else None
    if old is None:
        return p
    said = 0
    for mood in tones.KEYS:
        digits = old[mood] or ""
        for line_id, ch in enumerate(digits):
            if ch not in "123":
                continue
            liked, spoken = ch in "13", ch in "23"
            p["mastery"]["%d:%s" % (line_id, mood)] = {"s": 2 if liked else 1, "d": 0, "k": liked, "kp": liked, "v": spoken}
            p["seeds"] += int(liked) + int(spoken)
            said += int(spoken)
    p["stats"]["said"] = said
    p["stats"]["imported"] = True
    G.check_badges(p)
    return p


def _row(user):
    row = app_tables.progress.get(user=user)
    if row is None:
        p = _from_userpoints(user)
        row = app_tables.progress.add_row(user=user, created=C.now(), updated=C.now(), **dict((k, p[k]) for k in COLUMNS))
    return row


def _load(row):
    return G.normal(dict((k, row[k]) for k in COLUMNS))


def _save(row, p):
    row.update(updated=C.now(), **dict((k, p[k]) for k in COLUMNS))


@anvil.server.callable(require_user=True)
def get_progress(today=None):
    user = C.require_user()
    return _load(_row(user))


def _clean_results(results):
    out = []
    for r in (results or [])[:60]:
        if not isinstance(r, dict):
            continue
        try:
            line_id = int(r.get("id"))
        except Exception:
            continue
        mood = r.get("tone")
        if mood not in tones.KEYS:
            continue
        out.append({"id": line_id, "tone": mood, "type": C.text(r.get("type"), 20), "ok": bool(r.get("ok")),
                    "first": bool(r.get("first"))})
    return out


@anvil.server.callable(require_user=True)
def record_lesson(kind, lesson_key, results, today=None, lang="fr"):
    """A finished lesson in one language ("fr", "es", "it"): seeds, stars and mastery."""
    user = C.require_user()
    row = _row(user)
    key = C.text(lesson_key, 40)
    if key and not re.match(r"^[a-z0-9\-]+$", key):
        key = ""
    p, res = G.apply_lesson(_load(row), C.text(kind, 20), key, _clean_results(results), _today(today), langs.valid(lang))
    _save(row, p)
    return {"progress": p, "result": res}


@anvil.server.callable(require_user=True)
def mark_card(line_id, mood, what, on=True, today=None, lang="fr"):
    user = C.require_user()
    if mood not in tones.KEYS or what not in ("known", "said"):
        return C.fail("Unknown card.")
    try:
        line_id = int(line_id)
    except Exception:
        return C.fail("Unknown card.")
    row = _row(user)
    p, res = G.mark(_load(row), line_id, mood, what, bool(on), _today(today), langs.valid(lang))
    _save(row, p)
    return {"ok": True, "progress": p, "result": res}


@anvil.server.callable(require_user=True)
def set_daily_goal(goal):
    user = C.require_user()
    if goal not in [g for g, _ in G.GOALS]:
        return C.fail("Pick one of the daily goals.")
    row = _row(user)
    p = _load(row)
    p["daily_goal"] = goal
    _save(row, p)
    return C.ok(progress=p)


@anvil.server.callable(require_user=True)
def set_adventurer(name):
    user = C.require_user()
    row = _row(user)
    row["adventurer"] = C.text(name, 40)
    return C.ok()


@anvil.server.callable(require_user=True)
def merge_guest_progress(local, today=None):
    """Fold what a guest learned in this browser into their account (once: the browser forgets it afterwards)."""
    user = C.require_user()
    if not isinstance(local, dict):
        return C.fail("Nothing to add.")
    row = _row(user)
    guest = G.normal(local)
    guest["seeds"] = min(guest["seeds"], G.CATCH)
    guest["mastery"] = dict(list(guest["mastery"].items())[:3000])
    p = G.merge(_load(row), guest)
    _save(row, p)
    return C.ok(progress=p)


def summary_counts():
    rows = app_tables.progress.search()
    lessons = sum(int((r["stats"] or {}).get("lessons") or 0) for r in rows)
    return {"learners": len(rows), "lessons": lessons}
