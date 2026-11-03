"""The phrases this person can use, loaded once per visit, the trail of units and lessons built from them, and their
voices (a recorded file when the database has one, the browser's voice otherwise).

A phrase is {"id": LineID, "cat": unit number, "lang": "fr" | "es" | "it", "fr": {mood: text}, "en": {mood: text}}:
"fr" holds the text in the language being learned (state.lang(); the key name is historical, see langs.py).
Guests get the free sample ("basic" rows); members get the "free" rows too; "premium" rows stay locked (none yet).
"""
import anvil.server

from . import gamerules as G
from . import langs, pp, state, tones

_c: dict = {"data": None}
_voices: dict = {}


def data():
    if _c["data"] is None or _c["data"].get("lang") != state.lang():
        _c["data"] = anvil.server.call("get_phrases", state.lang())
    return _c["data"]


def lang():
    return state.lang()


def lang_name():
    return langs.name(state.lang())


def switch(code):
    """Learn another language from now on (this browser remembers it). The next page loads its phrases."""
    state.set_lang(code)
    pp.set_lang(state.lang())
    reset()


def counts():
    """How many phrases each language has: {"fr": n, "es": n, "it": n} (from the last load)."""
    return dict((data().get("counts") or {}))


def reset():
    """After signing in or out: the next page loads the phrases this person may see."""
    _c["data"] = None
    _voices.clear()


def all_phrases():
    return data()["phrases"]


def find(line_id):
    try:
        line_id = int(line_id)
    except Exception:
        return None
    for p in all_phrases():
        if p["id"] == line_id:
            return p
    return None


def in_unit(unit):
    return [p for p in all_phrases() if p["cat"] == unit]


def unit_numbers():
    d = data()
    nums = set(p["cat"] for p in d["phrases"])
    for group in ("signup", "premium"):
        for k in (d.get("locked") or {}).get(group, {}).keys():
            nums.add(int(k))
    return sorted(nums) or [1]


def unit_info(unit):
    u = tones.UNITS.get(unit) or {"name": "Unit %d" % unit, "icon": "book", "blurb": "More phrases."}
    return dict(u, number=unit)


def lessons(unit, progress):
    """The trail of one unit: playable lessons (5 phrases each), a mood challenge, then the locked ones."""
    ids = [p["id"] for p in in_unit(unit)]
    out = []
    for n in range(0, len(ids), G.LESSON_SIZE):
        key = "u%d-%d" % (unit, n // G.LESSON_SIZE + 1)
        out.append({"key": key, "unit": unit, "n": n // G.LESSON_SIZE + 1, "ids": ids[n:n + G.LESSON_SIZE],
                    "kind": "lesson", "stars": int(progress["lessons"].get(key) or 0), "locked": ""})
    if len(ids) >= 2:
        key = "u%d-mix" % unit
        out.append({"key": key, "unit": unit, "n": len(out) + 1, "ids": ids, "kind": "challenge",
                    "stars": int(progress["lessons"].get(key) or 0), "locked": ""})
    locked = data().get("locked") or {}
    for group in ("signup", "premium"):
        count = int(locked.get(group, {}).get(str(unit)) or 0)
        for n in range((count + G.LESSON_SIZE - 1) // G.LESSON_SIZE):
            out.append({"key": "u%d-%s%d" % (unit, group, n), "unit": unit, "n": len(out) + 1, "ids": [],
                        "kind": "lesson", "stars": 0, "locked": group, "count": count})
    current = None
    for lesson in out:
        if not lesson["locked"] and lesson["stars"] == 0 and current is None:
            current = lesson["key"]
    for lesson in out:
        lesson["current"] = lesson["key"] == current
    return out


def lesson_by_key(key, progress):
    try:
        unit = int(key.split("-")[0][1:])
    except Exception:
        return None
    for lesson in lessons(unit, progress):
        if lesson["key"] == key and not lesson["locked"]:
            return lesson
    return None


def locked_total(group):
    return sum(int(v or 0) for v in ((data().get("locked") or {}).get(group) or {}).values())


def voice_url(line_id, mood, lang):
    """A recorded voice for this phrase and mood, or None (then the browser's voice reads it).
    lang "en" = the English, anything else = the language being learned."""
    lang = "en" if lang == "en" else state.lang()
    k = "%s|%s|%s" % (line_id, mood, lang)
    if k not in _voices:
        try:
            _voices[k] = anvil.server.call_s("voice_url", int(line_id), mood, lang)
        except Exception:
            _voices[k] = None
    return _voices[k]


def speak(phrase, mood, lang="fr"):
    """Say a phrase in a mood and wait until it's done (hands-free lessons)."""
    text = (phrase.get(lang) or {}).get(mood) or ""
    url = voice_url(phrase["id"], mood, lang)
    if url and pp.play(url, 1 if lang == "fr" else 0.7) in ("ok", "silent"):
        return
    pp.say(text, lang, mood)


def speak_bg(phrase, mood, lang="fr", done=None):
    """Say a phrase without waiting; done(result) afterwards."""
    text = (phrase.get(lang) or {}).get(mood) or ""
    url = voice_url(phrase["id"], mood, lang)

    def after_file(result):
        if result in ("ok", "silent"):
            if done:
                done(result)
        else:
            pp.fire("say", [text, lang, mood], done)

    if url:
        pp.fire("play", [url, 1 if lang == "fr" else 0.7], after_file)
    else:
        pp.fire("say", [text, lang, mood], done)
