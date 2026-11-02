"""This learner's progress (seeds, streak, daily goal, mastery, lesson stars, badges).

Members: kept in their account (server: Progress.py). Guests: kept in this browser only, with the very same rules
(gamerules.py), and folded into the account when they sign up or sign in (merge_guest).
"""
import json

import anvil.js
import anvil.server
from anvil.js import window

from . import gamerules as G
from . import state

_g = {"p": None}
GUEST_KEY = "guest_progress"


def today():
    """The learner's own date, YYYY-MM-DD (streaks follow their midnight, not the server's)."""
    d = anvil.js.new(window.Date)
    return "%04d-%02d-%02d" % (d.getFullYear(), d.getMonth() + 1, d.getDate())


def _guest():
    raw = state.store_get(GUEST_KEY)
    try:
        return json.loads(raw) if isinstance(raw, str) else {}
    except Exception:
        return {}


def _keep_guest(p):
    state.store_set(GUEST_KEY, json.dumps(p))
    _g["p"] = p


def progress():
    if _g["p"] is None:
        if state.me():
            _g["p"] = G.normal(anvil.server.call("get_progress", today()))
        else:
            _g["p"] = G.normal(_guest())
    return _g["p"]


def reset():
    _g["p"] = None


def record_lesson(kind, key, results):
    """A finished lesson -> the summary for the end screen (seeds, stars, new badges, goal/streak events)."""
    if state.me():
        r = anvil.server.call("record_lesson", kind, key, results, today())
        _g["p"] = G.normal(r["progress"])
        return r["result"]
    p, res = G.apply_lesson(progress(), kind, key, results, today())
    _keep_guest(p)
    return res


def mark(line_id, mood, what, on=True):
    """what = "known" (Got it) or "said" (said right out loud). Returns {seeds, events, badges}."""
    if state.me():
        r = anvil.server.call("mark_card", int(line_id), mood, what, bool(on), today())
        _g["p"] = G.normal(r["progress"])
        return r["result"]
    p, res = G.mark(progress(), line_id, mood, what, on, today())
    _keep_guest(p)
    return res


def set_goal(n):
    if state.me():
        _g["p"] = G.normal(state.call("set_daily_goal", int(n))["progress"])
    else:
        p = progress()
        p["daily_goal"] = int(n)
        _keep_guest(G.normal(p))


def set_adventurer(name):
    name = (name or "").strip()[:40]
    if state.me():
        anvil.server.call("set_adventurer", name)
        progress()["adventurer"] = name
    else:
        p = progress()
        p["adventurer"] = name
        _keep_guest(p)


def adventurer():
    p = progress()
    if p.get("adventurer"):
        return p["adventurer"]
    me = state.me()
    return (me.get("name") or "").split(" ")[0] if me else ""


def merge_guest():
    """Right after signing in or up: move what this browser learned as a guest into the account."""
    local = _guest()
    if local and (local.get("seeds") or local.get("mastery") or local.get("adventurer")):
        try:
            anvil.server.call("merge_guest_progress", local, today())
            state.store_set(GUEST_KEY, None)
        except Exception:
            pass  # keep it in the browser and try again next time
    reset()


def known(line_id, mood):
    m = progress()["mastery"].get("%d:%s" % (int(line_id), mood)) or {}
    return bool(m.get("k"))


def said(line_id, mood):
    m = progress()["mastery"].get("%d:%s" % (int(line_id), mood)) or {}
    return bool(m.get("v"))


def summary():
    """Everything the header chip, the trail and the progress page show."""
    p = progress()
    t = today()
    _touch = p["today"] == t
    today_seeds = p["today_seeds"] if _touch else 0
    i, name, line, at, nxt = G.stage(p["seeds"])
    return {"seeds": p["seeds"], "streak": G.live_streak(p, t), "best_streak": p["best_streak"],
            "today_seeds": today_seeds, "goal": p["daily_goal"], "goal_pct": min(100, int(100 * today_seeds / max(1, p["daily_goal"]))),
            "goal_done": today_seeds >= p["daily_goal"], "stage": i, "stage_name": name, "stage_line": line,
            "stage_at": at, "stage_next": nxt, "catch": G.CATCH, "badges": list(p["badges"]),
            "lessons_done": int(p["stats"].get("lessons") or 0), "said": int(p["stats"].get("said") or 0)}
