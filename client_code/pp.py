"""Python face of Parapeet's JavaScript engines (theme/assets/pp-card.js and pp-audio.js, window.PP).

Forms never touch window.PP directly; they call these functions (or use Components.PhraseCard, which wraps the card).
Functions that wait (say, play, listen, record_stop) block the Python code until the sound or the speech is done,
like any Anvil server call; `fire` starts one without waiting and calls `done(result)` afterwards.
"""
import anvil.js
from anvil.js import window

from . import langs, state, tones

PP = window.PP
PP.setTones(tones.as_list())


def set_lang(code):
    """Tell the engines which language is being learned (card labels, tu/vous badges, voices, speech check)."""
    PP.setLang(langs.for_js(code))


set_lang(state.lang())


def card(node, on_change, on_listen=None, keys=True, keep_tone=False):
    """The swipe card engine inside a DOM node. on_change(state) gets {index, tone, key, id, side, count, reason}."""
    opts = {"onChange": anvil.js.report_exceptions(on_change), "keys": keys, "keepTone": keep_tone}
    if on_listen is not None:
        opts["onListen"] = anvil.js.report_exceptions(on_listen)
    return PP.card(node, opts)


def diff_html(text, base):
    return PP.diffHtml(text, base)


def say(text, lang="fr", mood="Basic"):
    """Read aloud with the browser's voice (pace and pitch follow the mood). Waits until it's done.
    lang "fr" = the language being learned (French, Spanish or Italian), "en" = English."""
    return PP.say(text, lang, mood)


def play(url, volume=1):
    """Play a sound file. Waits until it ends; returns 'ok', or 'error' when it couldn't play."""
    return PP.play(url, volume)


def stop():
    PP.stop()


def last_seconds():
    return (PP.lastMs() or 0) / 1000.0


def wait(seconds):
    PP.wait(int(seconds * 1000))


def fire(name, args, done=None):
    """Start PP.<name>(*args) without waiting. done(result) runs when it finishes."""
    PP.fire(name, list(args), anvil.js.report_exceptions(done) if done else None)


def can_listen():
    return bool(PP.canListen())


def listen(lang=None):
    """Speech recognition in the language being learned (or a tag like "es-ES"): {"transcript", "alternatives"} or
    {"error"}. Waits (up to ~9 s)."""
    r = PP.listen(lang or langs.info(state.lang())["asr"], 9000)
    return {"transcript": r.transcript or "", "alternatives": list(r.alternatives or []), "error": r.error or ""}


def stop_listening():
    PP.stopListening()


def similarity(a, b):
    return float(PP.similarity(a or "", b or ""))


def best_similarity(target, alternatives):
    return float(PP.bestSimilarity(target or "", list(alternatives or [])))


def plain(text):
    return PP.plain(text or "")


def record_start():
    """'ok', 'denied', 'unsupported' or 'error'."""
    return PP.rec.start()


def record_stop():
    return bool(PP.rec.stop())


def recording():
    return bool(PP.rec.on)


def has_recording():
    return bool(PP.rec.has())


def clear_recording():
    PP.rec.clear()


def sfx(kind):
    PP.sfx(kind)


def confetti():
    PP.confetti()


def wake(on):
    PP.wake(bool(on))


def settings():
    s = PP.settings()
    return {"sfx": bool(s.sfx), "speed": float(s.speed or 1)}
