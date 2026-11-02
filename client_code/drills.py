"""Builds the exercises of a lesson from phrases (plain Python, no Anvil imports, so it's easy to test).

Exercise types (each is a dict the Lesson page shows):
  meaning  French in a mood -> pick the English (4 choices)
  mood     French -> which mood is it? (4 moods): the heart of Parapeet, hearing the feeling
  build    English + mood -> tap the French words in order (word tiles, with a few extra words)
  listen   hear French -> pick what you heard among three moods of the same phrase
  switch   the neutral French -> "say it to your boss": pick the right version among three moods
  say      read the French out loud (speech check; only when the browser can listen)
"""
import random

from . import gamerules as G
from . import tones

MAX_BUILD_WORDS = 12


def _words(text):
    return [w for w in (text or "").replace("/", " / ").split() if w]


def _fr(p, mood):
    return (p["fr"].get(mood) or "").strip()


def _en(p, mood):
    return (p["en"].get(mood) or "").strip()


def _distinct(options, key):
    seen, out = set(), []
    for o in options:
        k = (o.get(key) or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(o)
    return out


def _pick_moods(p, progress, rnd, n=2):
    """Neutral first (it's the base), then the moods this learner knows least for this phrase."""
    others = [k for k in tones.KEYS[1:] if _fr(p, k)]
    rnd.shuffle(others)
    others.sort(key=lambda k: G.strength(progress, p["id"], k))
    return (["Basic"] if _fr(p, "Basic") else []) + others[:max(0, n - 1)]


def meaning(p, mood, pool, rnd):
    right = _en(p, mood)
    if not right:
        return None
    cands = [{"text": _en(q, k)} for q in pool for k in tones.KEYS if (q["id"], k) != (p["id"], mood) and _en(q, k)]
    rnd.shuffle(cands)
    same = [{"text": _en(p, k)} for k in tones.KEYS if k != mood and _en(p, k)]
    rnd.shuffle(same)
    wrong = _distinct([o for o in same[:1] + cands if o["text"].strip().lower() != right.lower()], "text")[:3]
    if len(wrong) < 2:
        return None
    opts = [{"text": right, "value": "right"}] + [{"text": o["text"], "value": "wrong%d" % i} for i, o in enumerate(wrong)]
    rnd.shuffle(opts)
    return {"type": "meaning", "title": "What does this mean?", "prompt": _fr(p, mood), "lang": "fr",
            "options": opts, "answer": "right", "solution": right}


def mood_quiz(p, mood, rnd):
    others = [k for k in tones.KEYS if k != mood]
    rnd.shuffle(others)
    keys = [mood] + others[:3]
    rnd.shuffle(keys)
    opts = [{"text": tones.label(k), "value": k, "mood": k} for k in keys]
    return {"type": "mood", "title": "Which mood is this?", "prompt": _fr(p, mood), "lang": "fr", "options": opts,
            "answer": mood, "solution": "%s: %s" % (tones.label(mood), tones.TONES[mood]["blurb"]), "hide_mood": True}


def build(p, mood, pool, rnd):
    words = _words(_fr(p, mood))
    if not words or len(words) > MAX_BUILD_WORDS or not _en(p, mood):
        return None
    extra = []
    others = [q for q in pool if q["id"] != p["id"]] or pool
    q = rnd.choice(others)
    lower = set(w.lower() for w in words)
    for w in _words(_fr(q, rnd.choice(tones.KEYS))):
        if w.lower() not in lower and w not in extra:
            extra.append(w)
    rnd.shuffle(extra)
    tiles = [{"word": w, "n": i} for i, w in enumerate(words + extra[:3])]
    rnd.shuffle(tiles)
    return {"type": "build", "title": "Write this in French", "prompt": _en(p, mood), "lang": "en", "tiles": tiles,
            "answer": " ".join(words), "solution": " ".join(words)}


def listen(p, mood, rnd):
    others = [k for k in tones.KEYS if k != mood and _fr(p, k) and _fr(p, k) != _fr(p, mood)]
    rnd.shuffle(others)
    if len(others) < 2:
        return None
    keys = [mood] + others[:2]
    rnd.shuffle(keys)
    opts = [{"text": _fr(p, k), "value": k} for k in keys]
    return {"type": "listen", "title": "What did you hear?", "prompt": "", "lang": "fr", "audio": _fr(p, mood),
            "options": opts, "answer": mood, "solution": _fr(p, mood)}


def switch(p, mood, rnd):
    if mood == "Basic" or not _fr(p, "Basic"):
        return None
    others = [k for k in tones.KEYS if k not in (mood, "Basic") and _fr(p, k)]
    rnd.shuffle(others)
    keys = [mood] + others[:2]
    rnd.shuffle(keys)
    opts = [{"text": _fr(p, k), "value": k} for k in keys]
    return {"type": "switch", "title": "Now say it to %s" % tones.TONES[mood]["who"], "prompt": _fr(p, "Basic"),
            "lang": "fr", "options": opts, "answer": mood, "solution": _fr(p, mood), "prompt_mood": "Basic"}


def say(p, mood):
    text = _fr(p, mood)
    if not text or len(_words(text)) > 16:
        return None
    return {"type": "say", "title": "Say it out loud", "prompt": text, "lang": "fr", "answer": text, "solution": text}


ORDER = ["meaning", "mood", "build", "switch", "listen", "mood", "meaning", "say", "switch", "build", "mood", "listen"]


def make(kind, p, mood, pool, rnd, can_say):
    if kind == "meaning":
        return meaning(p, mood, pool, rnd)
    if kind == "mood":
        return mood_quiz(p, mood, rnd)
    if kind == "build":
        return build(p, mood, pool, rnd)
    if kind == "listen":
        return listen(p, mood, rnd)
    if kind == "switch":
        return switch(p, mood, rnd)
    if kind == "say" and can_say:
        return say(p, mood)
    return None


def lesson(lesson_phrases, pool, progress, size=10, can_say=False, seed=None, cards=None):
    """~size exercises. cards = [(phrase, mood)] to use (a review); otherwise two moods per phrase."""
    rnd = random  # the module itself (the browser's Python has no random.Random class)
    if seed is not None:
        random.seed(seed)
    if cards is None:
        cards = []
        for p in lesson_phrases:
            for mood in _pick_moods(p, progress, rnd, 2):
                cards.append((p, mood))
        rnd.shuffle(cards)
    pool = pool or lesson_phrases
    out, n = [], 0
    while len(out) < size and n < size * 4 and cards:
        p, mood = cards[n % len(cards)]
        kinds = ORDER[len(out) % len(ORDER):] + ORDER[:len(out) % len(ORDER)]
        for kind in kinds:
            ex = make(kind, p, mood, pool, rnd, can_say)
            if ex:
                ex.update({"id": p["id"], "mood": mood, "show_mood": ex.get("prompt_mood") or mood})
                out.append(ex)
                break
        n += 1
    return out


def check(ex, answer):
    """Is this answer right? (build answers are compared without capitals and spacing before punctuation)"""
    if ex["type"] == "build":
        a = " ".join((answer or "").split()).lower().replace(" ?", "?").replace(" !", "!")
        b = " ".join(ex["answer"].split()).lower().replace(" ?", "?").replace(" !", "!")
        return a == b
    return answer == ex["answer"]
