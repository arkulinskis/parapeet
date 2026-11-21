import random

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import CallTemplate
from ... import game, gamerules as G, langs, phrases, pp, router, state, tones

SAY_PASS = 0.72      # the lesson's pass mark (Pages/Lesson SAY_PASS)
CLOSE = 0.45         # "Close" below the pass mark, "Not quite" under this
TURNS = 5
LISTEN_SECONDS = 8
MAX_WORDS = 18

# slug in the address, mood column, who it is, the caller's name per language
CALLERS = [
    ("boss", "Boss", "Your boss", {"fr": "Mme Lefèvre", "es": "Sra. Ortega", "it": "Dott.ssa Conti"}),
    ("client", "Client", "A client", {"fr": "M. Dubois", "es": "Sr. Ramírez", "it": "Sig. Bianchi"}),
    ("colleague", "Colleague", "A colleague", {"fr": "Julien", "es": "Lucía", "it": "Marco"}),
    ("partner", "Lover", "Your partner", {"fr": "Mon cœur", "es": "Mi amor", "it": "Tesoro"}),
    ("upset", "Agressive", "Someone upset", {"fr": "Karim", "es": "Javier", "it": "Paolo"}),
]


def _caller(slug):
    for c in CALLERS:
        if c[0] == slug:
            return c
    return None


class Call(CallTemplate):
    """#call[/<caller>]: the Practice call. Pick who's calling (boss, client, colleague, partner, someone upset); the
    phone rings (PP.ring); Answer starts 5 turns. Each turn the caller gives only the English cue (shown and read
    aloud), the mic listens for 8 seconds, then the verdict with the match % and the caller says the line back in
    that mood's voice (shadowing: "Say it once more with them"). No speech recognition, speaking switched off in the
    profile, or "I can't speak right now": say it in your head, Reveal, then "I got it / Not yet". Results go to
    game.record_lesson("call", None, ...): checked speech is type "say" (said-out-loud stats and badges), self-graded
    turns are type "recall" (seeds and mastery, never "said out loud"). window.PP_CALL = the current target (tests).
    The page hides the header and tab bar (Shell: no-chrome) like the lesson."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.lang = state.lang()
        self.slug = ""
        self.mood = "Boss"
        self.cards: list = []
        self.results: list = []
        self.turn = 0
        self.tried = False
        self.done_turn = False
        self.busy = False
        self.started = 0
        self._clock = 0
        off_until = state.store_get("speak_off_until", 0) or 0
        self.can_speak = pp.can_listen() and window.Date.now() > off_until
        self.callers_panel.items = [{"text": who, "value": slug, "kind": "mood", "icon": tones.TONES[mood]["icon"],
                                     "colour": tones.TONES[mood]["colour"]} for slug, mood, who, names in CALLERS]
        self.callers_panel.add_event_handler("x-chip", self._picked)
        self.pick_note.text = ("Your microphone checks what you say (the sound isn't kept)." if self.can_speak else
                               "Speech check is off or not available in this browser: you'll answer in your head, then reveal.")
        c = _caller(args[0]) if args else None
        if c is not None:
            self._setup(c)
        else:
            self._show_part("pick")

    def _show_part(self, name):
        self.pick_part.visible = name == "pick"
        self.phone_part.visible = name in ("ring", "talk")
        self.ring_part.visible = name == "ring"
        self.phone_part.classes["ringing"] = name == "ring"
        self.talk_part.visible = name == "talk"
        self.end_part.visible = name == "end"
        self.back_button.visible = name in ("pick", "end", "ring")
        self.back_button.text = "Back" if name != "ring" else "Callers"
        self.clock_label.visible = name == "talk"

    # ---- choosing a caller and ringing
    def _picked(self, value=None, **event_args):
        c = _caller(value)
        if c is not None:
            router.replace("call", c[0])
            self._setup(c)

    def _setup(self, c):
        self.slug, self.mood = c[0], c[1]
        info = tones.TONES[self.mood]
        self.caller_name.text = c[3].get(self.lang) or c[2]
        self.caller_role.text = "%s · talking to %s" % (c[2], info["who"])
        for slug, mood, who, names in CALLERS:
            self.avatar_icon.classes["ic-" + tones.TONES[mood]["icon"]] = mood == self.mood
        anvil.js.get_dom_node(self.phone_part).style.setProperty("--tone", info["colour"])
        self.cards = self._pick_cards()
        if not self.cards:
            self._show_part("pick")
            self.pick_note.text = "%s has no %s lines yet. Try another caller." % (c[2], langs.name(self.lang))
            return
        self.ring_label.text = "Incoming call..."
        self._show_part("ring")
        pp.ring(True)

    def _pick_cards(self):
        """Up to 5 phrases with a line for this caller: ones you already know a little first (mastery 1+), else any."""
        prog = game.progress()
        pool = [p for p in phrases.all_phrases()
                if (p["fr"].get(self.mood) or "") and (p["en"].get(self.mood) or "")
                and len((p["fr"].get(self.mood) or "").split()) <= MAX_WORDS]
        random.shuffle(pool)
        known = [p for p in pool if G.strength(prog, p["id"], self.mood, self.lang) >= 1]
        rest = [p for p in pool if p not in known]
        return (known + rest)[:TURNS]

    @handle("decline_button", "click")
    def decline_button_click(self, **event_args):
        pp.ring(False)
        pp.sfx("hangup")
        router.replace("call")
        self._show_part("pick")

    @handle("answer_button", "click")
    def answer_button_click(self, **event_args):
        pp.ring(False)
        pp.sfx("tap")  # this tap also unlocks sound and the microphone
        self.results = []
        self.turn = 0
        self.started = window.Date.now()
        self._tick_clock()
        if not self._clock:
            self._clock = window.setInterval(self._tick_clock, 1000)
        self._show_part("talk")
        self._turn()

    def _tick_clock(self):
        if not self.started:
            return
        secs = int((window.Date.now() - self.started) / 1000)
        self.clock_label.text = "%d:%02d" % (secs // 60, secs % 60)

    def _stop_clock(self):
        if self._clock:
            window.clearInterval(self._clock)
        self._clock = 0

    # ---- one turn
    def _card(self):
        return self.cards[self.turn]

    def _turn(self):
        p = self._card()
        target = p["fr"][self.mood]
        self.tried = False
        self.done_turn = False
        self.turn_label.text = "Turn %d of %d" % (self.turn + 1, len(self.cards))
        self.cue_who.text = "Say this to %s:" % tones.TONES[self.mood]["who"]
        self.cue_label.text = "“%s”" % p["en"][self.mood]
        reg = langs.register(target, self.lang)
        self.cue_reg.text = ("Use %s" % langs.register_text(reg, self.lang)) if reg else ""
        self.cue_reg.visible = bool(reg)
        self.heard_label.text = ""
        self.target_box.visible = False
        anvil.js.get_dom_node(self.target_label).setAttribute("lang", self.lang)
        window.PP_CALL = {"target": target, "turn": self.turn, "total": len(self.cards), "done": False}
        self._buttons()
        self._status("talk", "%s is talking..." % self.caller_name.text)
        pp.say(p["en"][self.mood], "en", self.mood)
        if self.can_speak:
            self._listen()
        else:
            self._status("think", "Say it in your head, then tap Reveal.")
            self._buttons(reveal=True)

    def _status(self, kind, text):
        node = self.dom_nodes["count"]
        node.className = "cl-count " + kind
        if kind == "listen":
            if node.offsetWidth >= 0:  # reading it restarts the 8-second ring animation
                node.className = "cl-count listen go"
        self.status_icon.text = {"listen": "Speak", "talk": "...", "think": "?", "done": ""}.get(kind, "")
        self.status_label.text = text

    def _buttons(self, reveal=False, grade=False, retry=False, after=False):
        self.reveal_button.visible = reveal
        self.got_button.visible = self.notyet_button.visible = grade
        self.retry_button.visible = retry
        self.shadow_button.visible = self.next_button.visible = after
        self.nospeak_button.visible = self.can_speak and not after and not grade
        self.next_button.text = "End the call" if self.turn + 1 >= len(self.cards) else "Next"

    def _listen(self):
        if self.busy:
            return
        self.busy = True
        self._buttons()
        self._status("listen", "Your turn: say it now")
        try:
            heard = pp.listen(None, LISTEN_SECONDS)
        finally:
            self.busy = False
        if not self.talk_part.visible:
            return  # hung up meanwhile
        if heard["error"]:
            msg = {"not-allowed": "The microphone is blocked. Allow it in the address bar, or tap Reveal.",
                   "unsupported": "This browser can't check speech. Say it in your head, then tap Reveal."
                   }.get(heard["error"], "I didn't catch that. Try again, or tap Reveal.")
            if heard["error"] in ("not-allowed", "unsupported"):
                self.can_speak = False
            self._status("think", msg)
            self._buttons(reveal=True, retry=self.can_speak)
            return
        p = self._card()
        target = p["fr"][self.mood]
        score = pp.best_similarity(target, heard["alternatives"] or [heard["transcript"]])
        ok = score >= SAY_PASS
        self.heard_label.text = "I heard: “%s”" % heard["transcript"]
        self._record(ok, "say")
        pct = int(score * 100)
        self.verdict_label.text = ("Nailed it · %d%% match" % pct) if ok else (
            ("Close · %d%% match" % pct) if score >= CLOSE else ("Not quite · %d%% match" % pct))
        self.target_box.classes["good"] = ok
        self.target_box.classes["bad"] = not ok
        pp.sfx("good" if ok else "bad")
        self._reveal_line()
        self._buttons(retry=not ok, after=True)

    def _record(self, ok, kind):
        p = self._card()
        if not self.tried:
            self.tried = True
            self.results.append({"id": p["id"], "tone": self.mood, "type": kind, "ok": ok, "first": ok})
        elif ok:
            r = self.results[-1]
            r["ok"] = True
            if kind == "say":
                r["type"] = "say"

    def _reveal_line(self):
        """Show the target and let the caller say it back in this mood's voice."""
        p = self._card()
        self.target_label.text = p["fr"][self.mood]
        self.target_box.visible = True
        self._status("done", "%s says it back:" % self.caller_name.text)
        phrases.speak_bg(p, self.mood, "fr")

    # ---- buttons
    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        pp.stop()
        self.target_box.visible = False
        self.heard_label.text = ""
        self._listen()

    @handle("reveal_button", "click")
    def reveal_button_click(self, **event_args):
        if self.busy:
            pp.stop_listening()
            return
        self.verdict_label.text = "The line"
        self.target_box.classes["good"] = self.target_box.classes["bad"] = False
        self._reveal_line()
        if self.tried:
            self._buttons(after=True)  # already graded by the speech check
        else:
            self._buttons(grade=True)

    @handle("got_button", "click")
    def got_button_click(self, **event_args):
        self._record(True, "recall")
        pp.sfx("good")
        self._advance()

    @handle("notyet_button", "click")
    def notyet_button_click(self, **event_args):
        self._record(False, "recall")
        self._advance()

    @handle("shadow_button", "click")
    def shadow_button_click(self, **event_args):
        phrases.speak_bg(self._card(), self.mood, "fr")

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        self._advance()

    @handle("nospeak_button", "click")
    def nospeak_button_click(self, **event_args):
        pp.stop_listening()
        state.store_set("speak_off_until", window.Date.now() + 30 * 60 * 1000)
        self.can_speak = False
        state.toast("No speaking for 30 minutes: answer in your head, then reveal.")
        if not self.busy:
            self._status("think", "Say it in your head, then tap Reveal.")
            self._buttons(reveal=True)

    def _advance(self):
        pp.stop()
        if not self.tried:
            self._record(False, "recall")
        self.turn += 1
        if self.turn >= len(self.cards):
            self._finish()
        else:
            self._turn()

    @handle("hangup_button", "click")
    def hangup_button_click(self, **event_args):
        pp.stop_listening()
        pp.stop()
        pp.sfx("hangup")
        if self.results:
            self._finish()
        else:
            self._stop_clock()
            router.replace("call")
            self._show_part("pick")

    # ---- the end
    def _finish(self):
        self._stop_clock()
        pp.stop()
        pp.sfx("hangup")
        right = len([r for r in self.results if r["ok"]])
        total = len(self.results)
        seeds = 0
        try:
            res = game.record_lesson("call", None, self.results)
            seeds = int(res.get("seeds") or 0)
        except Exception:
            seeds = 0
        if self.layout is not None:
            self.layout.refresh_stats()
        said = len([r for r in self.results if r["ok"] and r["type"] == "say"])
        self.end_stats.text = "Call ended · %d/%d · +%d seeds" % (right, total, seeds)
        self.end_title.text = langs.info(self.lang)["bye"]
        self.end_line.text = (("%d said out loud and understood. " % said) if said else "") + (
            "Smooth talker." if right == total else ("Good call. The ones you missed come back next time." if right >= 3
                                                     else "Every call gets easier. Try it again."))
        self.end_bird.mood = "wow" if right == total else ("happy" if right >= 3 else "oops")
        window.PP_CALL = {"target": "", "turn": total, "total": total, "done": True, "right": right}
        self._show_part("end")
        if right == total and total:
            pp.confetti()

    @handle("again_button", "click")
    def again_button_click(self, **event_args):
        c = _caller(self.slug)
        if c is not None:
            self._setup(c)

    @handle("other_button", "click")
    def other_button_click(self, **event_args):
        router.replace("call")
        self._show_part("pick")

    @handle("back_button", "click")
    def back_button_click(self, **event_args):
        if self.ring_part.visible and self.phone_part.visible:
            self.decline_button_click()
        else:
            router.go("play")

    @handle("", "hide")
    def form_hide(self, **event_args):
        pp.ring(False)
        pp.stop_listening()
        pp.stop()
        self._stop_clock()
