"""Parapeet's game rules: seeds, the daily goal, streaks, mastery per phrase and mood, lesson stars and badges.

Plain Python with no Anvil imports, shared by the browser (guests keep their progress in this browser) and the server
(members' progress lives in the `progress` table). Both call the same functions, so the numbers always agree.

A progress dict looks like blank() below. Days are the learner's local date as "YYYY-MM-DD".
mastery[ckey(LineID, mood, lang)] = {"s": strength 0..5, "d": day number last practised, "k": marked known,
"v": said out loud correctly}. French keys are "<LineID>:<mood>" (as before Spanish and Italian came), the others
"<lang>:<LineID>:<mood>"; lesson stars likewise ("u1-2" for French, "es:u1-2"). Seeds, streak, goal and badges are
shared: one parakeet to catch, whichever language you practise.
"""
from . import langs, tones

SEEDS = {"first_try": 2, "second_try": 1, "lesson": 5, "perfect": 5, "said": 3, "known": 1, "goal": 10}
GOALS = [(10, "Casual"), (20, "Regular"), (40, "Serious"), (80, "Intense")]
CATCH = 3000  # the old app's promise: "Just 3000 seeds to catch Parapeet!"
STAGES = [
    (0, "Parapeet spotted", "He flew off with your {lang}. Follow the trail of seeds."),
    (100, "On his trail", "You found feathers by the water cooler. Keep going."),
    (400, "Feather in hand", "You can hear him squawking in {lang} now."),
    (1000, "Closing in", "He's tired. Your {lang} is coming back."),
    (2000, "Cage ready", "One more push and he's yours."),
    (CATCH, "Caught him!", "Parapeet is caught, and your {lang} is back. Keep him happy with daily practice."),
]
BADGES = [
    ("first", "First flight", "Finish your first lesson", "feather"),
    ("perfect", "Flawless", "Finish a lesson with no mistakes", "sparkle"),
    ("streak3", "On fire", "Practise 3 days in a row", "flame"),
    ("streak7", "Week on the trail", "Practise 7 days in a row", "calendar"),
    ("streak30", "Unstoppable", "Practise 30 days in a row", "trophy"),
    ("seeds100", "Seed collector", "Collect 100 seeds", "seed"),
    ("seeds1000", "Seed hoarder", "Collect 1,000 seeds", "seed"),
    ("caught", "Caught Parapeet", "Collect 3,000 seeds", "crown"),
    ("moods", "Mood ring", "Get a right answer in all 10 moods", "palette"),
    ("diplomat", "Diplomat", "25 right answers for clients and bosses", "handshake"),
    ("peacemaker", "Peacemaker", "25 right answers calming hotheads and tense moments", "dove"),
    ("comforter", "Shoulder to cry on", "15 right answers comforting someone sad", "umbrella"),
    ("romantic", "Romantic", "15 right answers in the Lover mood", "heart"),
    ("clown", "Class clown", "15 right answers in the Silly mood", "party"),
    ("voice", "Out loud", "Say 10 phrases right with your voice", "mic"),
]
BADGE_INFO = dict((b[0], b) for b in BADGES)
LESSON_SIZE = 5  # phrases per lesson on the trail


def blank():
    return {"seeds": 0, "streak": 0, "best_streak": 0, "last_day": "", "today": "", "today_seeds": 0,
            "daily_goal": 20, "mastery": {}, "lessons": {}, "badges": [], "stats": {}, "adventurer": ""}


def normal(p):
    """A full progress dict (missing keys filled in), as a fresh copy that's safe to change."""
    out = blank()
    for k, v in (p or {}).items():
        if k in out and v is not None:
            out[k] = v
    out["mastery"] = dict(out["mastery"])
    out["lessons"] = dict(out["lessons"])
    out["badges"] = list(out["badges"])
    st = dict(out["stats"])
    st["days"] = dict(st.get("days") or {})
    out["stats"] = st
    for k in ("seeds", "streak", "best_streak", "today_seeds", "daily_goal"):
        out[k] = int(out[k] or 0)
    if out["daily_goal"] not in [g for g, _ in GOALS]:
        out["daily_goal"] = 20
    return out


def day_no(day):
    """'2026-11-02' -> a day number (days since 1970-01-01), or None for anything else."""
    try:
        y, m, d = int(day[0:4]), int(day[5:7]), int(day[8:10])
    except Exception:
        return None
    if len(day) != 10 or not (1 <= m <= 12 and 1 <= d <= 31):
        return None
    if m <= 2:
        y -= 1
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    mp = m - 3 if m > 2 else m + 9
    doy = (153 * mp + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _bump(stats, key, n=1):
    stats[key] = int(stats.get(key) or 0) + n


def _touch(p, today):
    if p["today"] != today:
        p["today"] = today
        p["today_seeds"] = 0


def _streak(p, today):
    """Any seeds earned today count for the streak (once per day)."""
    if p["last_day"] == today:
        return
    a, b = day_no(p["last_day"]), day_no(today)
    if a is not None and b is not None and b - a == 1:
        p["streak"] += 1
    elif a is None or b is None or b != a:
        p["streak"] = 1
    p["last_day"] = today
    p["best_streak"] = max(p["best_streak"], p["streak"])


def live_streak(p, today):
    """The streak to show today: it only breaks once a whole day was missed."""
    a, b = day_no(p.get("last_day") or ""), day_no(today)
    if a is None or b is None:
        return 0
    return int(p.get("streak") or 0) if b - a <= 1 else 0


def add_seeds(p, n, today, events):
    """Seeds for anything learned; the daily goal bonus once a day; the streak; the 30-day history."""
    _touch(p, today)
    before = p["today_seeds"]
    p["seeds"] += n
    p["today_seeds"] += n
    if before < p["daily_goal"] <= p["today_seeds"]:
        p["seeds"] += SEEDS["goal"]
        events.append("goal")
    old = p["streak"]
    _streak(p, today)
    if p["streak"] > old:
        events.append("streak")
    days = p["stats"]["days"]
    days[today] = int(days.get(today) or 0) + n
    for d in sorted(days.keys())[:-30]:
        del days[d]


def ckey(line_id, tone, lang=langs.DEFAULT):
    """The mastery key of one card (phrase + mood) in one language."""
    base = "%d:%s" % (int(line_id), tone)
    return base if langs.valid(lang) == langs.DEFAULT else "%s:%s" % (langs.valid(lang), base)


def lkey(lesson_key, lang=langs.DEFAULT):
    """Where a lesson's stars are kept ("u1-2" in French, "es:u1-2" in Spanish)."""
    return lesson_key if langs.valid(lang) == langs.DEFAULT else "%s:%s" % (langs.valid(lang), lesson_key)


def _card(p, line_id, tone, lang=langs.DEFAULT):
    key = ckey(line_id, tone, lang)
    m = dict(p["mastery"].get(key) or {})
    m["s"] = int(m.get("s") or 0)
    return key, m


def apply_lesson(p, kind, lesson_key, results, today, lang=langs.DEFAULT):
    """A finished lesson in one language. results = [{"id": LineID, "tone": mood key, "type": exercise type,
    "ok": right in the end, "first": right on the first try}]. Returns (new progress, summary for the end screen)."""
    p = normal(p)
    events, stats = [], p["stats"]
    day = day_no(today) or 0
    first = later = 0
    clean = []
    for r in (results or [])[:60]:
        tone = r.get("tone") if isinstance(r, dict) else None
        try:
            line_id = int(r.get("id"))
        except Exception:
            continue
        if tone not in tones.KEYS:
            continue
        clean.append(r)
        key, m = _card(p, line_id, tone, lang)
        if r.get("first"):
            first += 1
            m["s"] = min(5, m["s"] + 1)
            _bump(stats, "c_" + tone)
        else:
            m["s"] = max(0, m["s"] - 1)
            if r.get("ok"):
                later += 1
        if r.get("type") == "say" and r.get("ok") and not m.get("v"):
            m["v"] = True
            _bump(stats, "said")
        m["d"] = day
        p["mastery"][key] = m
    answered = len(clean)
    if not answered:
        return p, {"seeds": 0, "stars": 0, "accuracy": 0, "correct": 0, "answered": 0, "events": [], "badges": []}
    acc = first / float(answered)
    stars = 3 if acc >= 0.9 else (2 if acc >= 0.7 else 1)
    if lesson_key:
        lk = lkey(lesson_key, lang)
        p["lessons"][lk] = max(int(p["lessons"].get(lk) or 0), stars)
    seeds = first * SEEDS["first_try"] + later * SEEDS["second_try"] + SEEDS["lesson"]
    if first == answered:
        seeds += SEEDS["perfect"]
        _bump(stats, "perfect")
    _bump(stats, "lessons")
    _bump(stats, "answers", answered)
    _bump(stats, "right", first)
    add_seeds(p, seeds, today, events)
    new = check_badges(p)
    return p, {"seeds": seeds, "stars": stars, "accuracy": acc, "correct": first, "answered": answered,
               "events": events, "badges": new, "kind": kind}


def mark(p, line_id, tone, what, on, today, lang=langs.DEFAULT):
    """what = "known" (the Got it toggle) or "said" (spoken right in the phrasebook). Seeds only the first time."""
    p = normal(p)
    events = []
    if tone not in tones.KEYS or what not in ("known", "said"):
        return p, {"seeds": 0, "events": events, "badges": []}
    key, m = _card(p, line_id, tone, lang)
    seeds = 0
    if what == "known":
        m["k"] = bool(on)
        if on and not m.get("kp"):
            m["kp"] = True
            seeds = SEEDS["known"]
            m["s"] = max(m["s"], 2)
    elif on and not m.get("v"):
        m["v"] = True
        seeds = SEEDS["said"]
        m["s"] = min(5, m["s"] + 1)
        _bump(p["stats"], "said")
        _bump(p["stats"], "c_" + tone)
    m["d"] = day_no(today) or m.get("d") or 0
    p["mastery"][key] = m
    if seeds:
        add_seeds(p, seeds, today, events)
    return p, {"seeds": seeds, "events": events, "badges": check_badges(p)}


def check_badges(p):
    """Award every badge that's now earned. Returns the new badge ids."""
    st, have = p["stats"], set(p["badges"])
    c = lambda k: int(st.get("c_" + k) or 0)  # noqa: E731
    earned = {
        "first": int(st.get("lessons") or 0) >= 1,
        "perfect": int(st.get("perfect") or 0) >= 1,
        "streak3": p["best_streak"] >= 3,
        "streak7": p["best_streak"] >= 7,
        "streak30": p["best_streak"] >= 30,
        "seeds100": p["seeds"] >= 100,
        "seeds1000": p["seeds"] >= 1000,
        "caught": p["seeds"] >= CATCH,
        "moods": all(c(k) > 0 for k in tones.KEYS),
        "diplomat": c("Client") + c("Boss") >= 25,
        "peacemaker": c("Agressive") + c("Frustrated") >= 25,
        "comforter": c("Sad") >= 15,
        "romantic": c("Lover") >= 15,
        "clown": c("Stupid") >= 15,
        "voice": int(st.get("said") or 0) >= 10,
    }
    new = [b for b, _, _, _ in BADGES if earned.get(b) and b not in have]
    p["badges"] = p["badges"] + new
    return new


def merge(server_p, guest_p):
    """A guest signs in: fold this browser's progress into the account (nothing is lost, nothing doubles twice)."""
    a, b = normal(server_p), normal(guest_p)
    a["seeds"] += min(b["seeds"], CATCH)
    for k, m in b["mastery"].items():
        old = a["mastery"].get(k) or {}
        new = dict(old)
        new["s"] = max(int(old.get("s") or 0), int(m.get("s") or 0))
        new["d"] = max(int(old.get("d") or 0), int(m.get("d") or 0))
        for flag in ("k", "kp", "v"):
            if m.get(flag) or old.get(flag):
                new[flag] = True
        a["mastery"][k] = new
    for k, s in b["lessons"].items():
        a["lessons"][k] = max(int(a["lessons"].get(k) or 0), int(s or 0))
    for k, v in b["stats"].items():
        if k == "days":
            for d, n in v.items():
                a["stats"]["days"][d] = int(a["stats"]["days"].get(d) or 0) + int(n or 0)
        elif isinstance(v, (int, float)):
            _bump(a["stats"], k, int(v))
    if (day_no(b["last_day"]) or 0) > (day_no(a["last_day"]) or 0) and b["streak"] >= a["streak"]:
        a["streak"], a["last_day"] = b["streak"], b["last_day"]
    if b["today"] == a["today"]:
        a["today_seeds"] += b["today_seeds"]
    elif (day_no(b["today"]) or 0) > (day_no(a["today"]) or 0):
        a["today"], a["today_seeds"] = b["today"], b["today_seeds"]
    a["best_streak"] = max(a["best_streak"], b["best_streak"], a["streak"])
    a["adventurer"] = a["adventurer"] or b["adventurer"]
    check_badges(a)
    return a


def stage(seeds, lang=langs.DEFAULT):
    """(index, name, line, seeds where it starts, seeds where the next one starts or None)."""
    i = 0
    for n, (at, _, _) in enumerate(STAGES):
        if seeds >= at:
            i = n
    nxt = STAGES[i + 1][0] if i + 1 < len(STAGES) else None
    return i, STAGES[i][1], STAGES[i][2].replace("{lang}", langs.name(lang)), STAGES[i][0], nxt


def strength(p, line_id, tone, lang=langs.DEFAULT):
    m = p["mastery"].get(ckey(line_id, tone, lang)) or {}
    return int(m.get("s") or 0)


def mood_mastery(p, cards_by_mood, lang=langs.DEFAULT):
    """{mood: percent of its cards at strength 3+} for the moods' progress bars. cards_by_mood = {mood: [LineIDs]}."""
    out = {}
    for mood, ids in cards_by_mood.items():
        if not ids:
            out[mood] = 0
            continue
        good = len([i for i in ids if strength(p, i, mood, lang) >= 3])
        out[mood] = int(round(100.0 * good / len(ids)))
    return out


def due(p, cards, today, limit=10, lang=langs.DEFAULT):
    """The weakest and most overdue (LineID, mood) pairs first, for a 'practise weak spots' lesson."""
    day = day_no(today) or 0
    scored = []
    for line_id, mood in cards:
        m = p["mastery"].get(ckey(line_id, mood, lang)) or {}
        s, last = int(m.get("s") or 0), int(m.get("d") or 0)
        if not m:
            scored.append((-50, 0, line_id, mood))  # never seen: after the overdue ones
            continue
        wait = 2 ** s  # 1, 2, 4, 8, 16, 32 days
        overdue = (day - last) - wait if last else 99
        scored.append((-overdue, s, line_id, mood))
    scored.sort()
    return [(line_id, mood) for _, _, line_id, mood in scored[:limit]]
