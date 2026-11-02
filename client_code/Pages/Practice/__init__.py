import time

from anvil import *
import anvil.js
import anvil.server

from ._anvil_designer import PracticeTemplate
from ... import game, phrases, pp, router, state, tones

SAY_PASS = 0.75  # how close the recognised speech must be to the phrase (0..1)


class Practice(PracticeTemplate):
    """#practice[/<LineID>[/<mood>]]: the swipe phrasebook. One phrase at a time in ten moods.
    Sideways = mood, up/down = phrase, tap = flip (the PhraseCard engine). On a computer the mood arrows sit beside
    the card and the phrase buttons under it; on a phone a thumb dock at the bottom holds both. Tools: listen, say it
    (speech check, seeds), got it, save, record yourself, compare all moods, hands-free lesson."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._st: dict = {}
        self._busy_listen, self._looping = False, False
        self.hf_bar.visible = False
        self._front = state.store_get("front", "fr") or "fr"
        self.front_button.text = "English first" if self._front == "en" else "French first"
        self._units = [u for u in phrases.unit_numbers() if phrases.in_unit(u)]
        self.unit_drop.items = [("%s (%d)" % (phrases.unit_info(u)["name"], len(phrases.in_unit(u))), u) for u in self._units]
        start_id = args[0] if args else None
        mood = tones.key_for_label(args[1]) if len(args) > 1 else None
        phrase = phrases.find(start_id) if start_id else None
        unit = phrase["cat"] if phrase else (state.store_get("practice_unit", None) or (self._units[0] if self._units else 1))
        if unit not in self._units and self._units:
            unit = self._units[0]
        self._open_unit(unit, phrase["id"] if phrase else None, mood or "Basic")
        locked = phrases.locked_total("signup")
        self.more_box.visible = bool(locked) and not state.me()
        self.more_label.text = "%d more phrases waiting" % locked
        self._show_today()

    # ---- data
    def _open_unit(self, unit, line_id=None, mood="Basic"):
        self._unit = unit
        self.unit_drop.selected_value = unit
        self._cards = phrases.in_unit(unit)
        index = 0
        for n, p in enumerate(self._cards):
            if p["id"] == line_id:
                index = n
        self.card.load(self._cards, index, mood, self._front)
        state.store_set("practice_unit", unit)

    def _phrase(self):
        if not self._cards:
            return None
        return self._cards[(self._st or {}).get("index", 0) % len(self._cards)]

    def _mood(self):
        return (self._st or {}).get("key") or "Basic"

    @handle("unit_drop", "change")
    def unit_drop_change(self, **event_args):
        self._open_unit(self.unit_drop.selected_value)

    # ---- the card moved
    @handle("card", "change")
    def card_change(self, **event_args):
        st = self._st = event_args["state"]
        p, mood = self._phrase(), self._mood()
        if p is None:
            return
        info = tones.TONES[mood]
        self.counter.text = "Phrase %d of %d" % (st["index"] + 1, st["count"])
        self.mood_name.text = info["label"]
        self.mood_who.text = "Talking to %s" % info["who"] if mood != "Basic" else "Say it to anyone"
        self.mood_blurb.text = info["blurb"]
        self.mood_listen.text = info["listen"]
        reg = tones.register(p["fr"].get(mood))
        self.mood_register.text = tones.REGISTER_TEXT[reg]
        self.mood_register.visible = bool(reg)
        self.dom_nodes["mood_dot"].style.setProperty("--tone", info["colour"])
        self.neutral_box.visible = mood != "Basic"
        self.neutral_text.text = p["fr"].get("Basic") or ""
        self._mood_buttons(st["tone"])
        self._card_marks()
        self.prev_phrase.enabled = self.dock_prev.enabled = st["index"] > 0
        if st.get("reason") != "flip":
            pp.stop()
            if pp.has_recording():
                pp.clear_recording()
                self.mine_button.enabled = False
            router.replace("practice", p["id"], info["label"].lower())

    def _mood_buttons(self, t):
        n = len(tones.KEYS)
        prev_key, next_key = tones.KEYS[(t - 1) % n], tones.KEYS[(t + 1) % n]
        for btn, label, key in ((self.side_prev, self.side_prev_label, prev_key), (self.side_next, self.side_next_label, next_key)):
            label.text = tones.label(key)
            anvil.js.get_dom_node(btn).style.setProperty("--tone", tones.TONES[key]["colour"])
        self.dock_prev_mood.text = tones.label(prev_key)
        self.dock_next_mood.text = tones.label(next_key)
        anvil.js.get_dom_node(self.dock_prev_mood).style.setProperty("--tone", tones.TONES[prev_key]["colour"])
        anvil.js.get_dom_node(self.dock_next_mood).style.setProperty("--tone", tones.TONES[next_key]["colour"])

    def _card_marks(self):
        p, mood = self._phrase(), self._mood()
        known, said = game.known(p["id"], mood), game.said(p["id"], mood)
        self.known_button.role = ["tool", "ic-check", "on"] if known else ["tool", "ic-check"]
        self.known_button.text = "Got it!" if known else "Got it"
        self.known_badge.visible, self.said_badge.visible = known, said
        self.card.mark("pc-known", known)

    def _show_today(self):
        s = game.summary()
        self.goal_ring.value = s["goal_pct"]
        self.goal_ring.text = "%d" % s["today_seeds"]
        self.today_label.text = "%d of %d for your daily goal%s" % (s["today_seeds"], s["goal"], " · done!" if s["goal_done"] else "")
        if self.layout is not None:
            self.layout.refresh_stats()

    def _reward(self, res, what):
        if res.get("seeds"):
            pp.sfx("good")
            state.toast("+%d seeds · %s" % (res["seeds"], what), "ok")
        for b in res.get("badges") or []:
            from ... import gamerules
            info = gamerules.BADGE_INFO.get(b)
            if info:
                pp.confetti()
                state.toast("New badge: %s!" % info[1], "ok")
        if "goal" in (res.get("events") or []):
            pp.confetti()
            state.toast("Daily goal reached! +10 bonus seeds", "ok")
        self._show_today()

    # ---- moving (buttons: desktop beside/under the card, phone in the dock)
    @handle("side_prev", "click")
    def side_prev_click(self, **event_args):
        self.card.prev_tone()

    @handle("side_next", "click")
    def side_next_click(self, **event_args):
        self.card.next_tone()

    @handle("dock_prev_mood", "click")
    def dock_prev_mood_click(self, **event_args):
        self.card.prev_tone()

    @handle("dock_next_mood", "click")
    def dock_next_mood_click(self, **event_args):
        self.card.next_tone()

    @handle("prev_phrase", "click")
    def prev_phrase_click(self, **event_args):
        self.card.prev_phrase()

    @handle("dock_prev", "click")
    def dock_prev_click(self, **event_args):
        self.card.prev_phrase()

    @handle("next_phrase", "click")
    def next_phrase_click(self, **event_args):
        self.card.next_phrase()

    @handle("dock_next", "click")
    def dock_next_click(self, **event_args):
        self.card.next_phrase()

    @handle("front_button", "click")
    def front_button_click(self, **event_args):
        self._front = "en" if self._front == "fr" else "fr"
        state.store_set("front", self._front)
        self.front_button.text = "English first" if self._front == "en" else "French first"
        self.card.set_front(self._front)

    @handle("help_button", "click")
    def help_button_click(self, **event_args):
        from ...Dialogs.Gestures import Gestures
        alert(Gestures(), buttons=[], role="app-dialog", large=True)

    # ---- tools
    @handle("card", "listen")
    def card_listen(self, **event_args):
        self.listen_button_click()

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        p = self._phrase()
        if p is None or self._looping:
            return
        if self._busy_listen:
            pp.stop()
            self._listen_done()
            return
        lang = (self._st or {}).get("side") or "fr"
        self._busy_listen = True
        self.listen_button.role = ["tool", "ic-stop", "on"]
        self.card.mark("pc-listening", True)
        phrases.speak_bg(p, self._mood(), lang, self._listen_done)

    def _listen_done(self, result=None):
        self._busy_listen = False
        self.listen_button.role = ["tool", "ic-volume"]
        self.card.mark("pc-listening", False)

    @handle("say_button", "click")
    def say_button_click(self, **event_args):
        p, mood = self._phrase(), self._mood()
        if p is None or self._looping:
            return
        if not pp.can_listen():
            alert("Checking your speech needs Chrome, Edge or Safari. You can still record yourself with Record me "
                  "and compare with Listen.", title="Speech check isn't available here", role="app-dialog")
            return
        target = p["fr"].get(mood) or ""
        self.say_button.text, self.say_button.role = "Listening...", ["tool", "tool-say", "ic-mic", "on"]
        self.card.mark("pc-recording", True)
        try:
            heard = pp.listen("fr-CA")
        finally:
            self.say_button.text, self.say_button.role = "Say it", ["tool", "tool-say", "ic-mic"]
            self.card.mark("pc-recording", False)
        if heard["error"]:
            msg = {"not-allowed": "Your browser blocked the microphone. Allow it in the address bar, then try again.",
                   "no-speech": "I didn't hear anything. Tap Say it and speak right away.",
                   "timeout": "I didn't hear anything. Tap Say it and speak right away."}.get(heard["error"], "The speech check didn't work this time. Try again.")
            state.toast(msg, "error")
            return
        score = pp.best_similarity(target, heard["alternatives"] or [heard["transcript"]])
        if score >= SAY_PASS:
            self.card.flash("good")
            res = game.mark(p["id"], mood, "said", True)
            self._card_marks()
            if res.get("seeds"):
                self._reward(res, "said out loud (%d%% match)" % int(score * 100))
            else:
                pp.sfx("good")
                state.toast("Très bien ! %d%% match." % int(score * 100), "ok")
        else:
            self.card.flash("bad")
            pp.sfx("bad")
            state.toast("Close: %d%% match. I heard \"%s\". Try again!" % (int(score * 100), heard["transcript"]), "error")

    @handle("known_button", "click")
    def known_button_click(self, **event_args):
        p, mood = self._phrase(), self._mood()
        if p is None:
            return
        on = not game.known(p["id"], mood)
        res = game.mark(p["id"], mood, "known", on)
        self._card_marks()
        if on:
            self.card.flash("good")
            self._reward(res, "you've got this one")

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        p, mood = self._phrase(), self._mood()
        if p is None:
            return
        if not state.me():
            if confirm("Your saved phrases live in your account, so you can review them anywhere.",
                       title="Save phrases with a free account", buttons=[("Not now", False), ("Join free", True)],
                       role="app-dialog"):
                router.remember_after(router.href("practice", p["id"], tones.label(mood).lower()))
                router.go("auth", "signup")
            return
        from ...Dialogs.NoteEdit import NoteEdit
        en = p["en"].get(mood) or ""
        note = alert(NoteEdit(fr=p["fr"].get(mood) or "", en="%s (%s)" % (en, tones.label(mood)) if en else ""),
                     buttons=[], role="app-dialog")
        if note:
            state.toast("Saved to your phrasebook", "ok")

    @handle("record_button", "click")
    def record_button_click(self, **event_args):
        if self._looping:
            return
        if pp.recording():
            pp.record_stop()
            self.record_button.text, self.record_button.role = "Record me", ["tool", "ic-record"]
            self.card.mark("pc-recording", False)
            self.mine_button.enabled = pp.has_recording()
            if pp.has_recording():
                self.mine_button_click()
            return
        r = pp.record_start()
        if r != "ok":
            state.toast({"denied": "Your browser blocked the microphone. Allow it in the address bar, then try again.",
                         "unsupported": "This browser can't record sound."}.get(r, "The microphone didn't start."), "error")
            return
        self.record_button.text, self.record_button.role = "Stop", ["tool", "ic-stop", "on", "rec"]
        self.card.mark("pc-recording", True)

    @handle("mine_button", "click")
    def mine_button_click(self, **event_args):
        if pp.has_recording():
            pp.fire("playRecording", [])

    @handle("compare_button", "click")
    def compare_button_click(self, **event_args):
        p = self._phrase()
        if p is None:
            return
        from ...Dialogs.CompareMoods import CompareMoods
        picked = alert(CompareMoods(phrase=p, mood=self._mood()), buttons=[], role="app-dialog", large=True)
        if picked:
            self.card.go(self._st["index"], picked, "left")

    # ---- hands-free lesson
    @handle("handsfree_button", "click")
    def handsfree_button_click(self, **event_args):
        if self._looping:
            self._stop_loop()
            return
        from ...Dialogs.HandsFree import HandsFree
        opts = alert(HandsFree(), buttons=[], role="app-dialog")
        if opts:
            self._loop(opts)

    @handle("hf_stop", "click")
    def hf_stop_click(self, **event_args):
        self._stop_loop()

    def _stop_loop(self):
        self._looping = False
        pp.stop()
        anvil.js.window.PP.musicStop()
        pp.wake(False)
        self.hf_bar.visible = False
        self.handsfree_button.role = ["tool", "ic-headphones"]
        self.handsfree_button.text = "Hands-free"

    def _loop(self, opts):
        if not self._cards:
            return
        self._looping = True
        pp.wake(True)
        self.hf_bar.visible = True
        self.handsfree_button.role = ["tool", "ic-stop", "on"]
        self.handsfree_button.text = "Stop"
        if opts.get("music"):
            urls = [anvil.server.call_s("get_music", str(n)) for n in (1, 2, 3)]
            anvil.js.window.PP.music([u for u in urls if u])
        total = max(1, int(opts.get("minutes") or 5)) * 60
        start = time.time()
        i, t = self._st["index"], self._st["tone"]
        idle = 0
        try:
            while self._looping and time.time() - start < total:
                left = int(total - (time.time() - start))
                self.hf_label.text = "Hands-free · %d:%02d left" % (left // 60, left % 60)
                self.dom_nodes["hf_fill"].style.width = "%d%%" % int(100 * (time.time() - start) / total)
                phrase, mood = self._cards[i], tones.KEYS[t]
                skip = mood not in opts["moods"] or (opts.get("skip_known") and game.known(phrase["id"], mood))
                if not skip:
                    idle = 0
                    if (i, t) != (self._st["index"], self._st["tone"]):
                        self.card.go(i, t, "left")
                        pp.wait(0.4)
                    self._play_pattern(phrase, mood, opts["pattern"])
                    pp.wait(0.7)
                else:
                    idle += 1
                    pp.wait(0.02)
                    if idle > len(self._cards) * len(tones.KEYS):
                        state.toast("Every card is skipped by your choices. Pick more moods.", "error")
                        break
                t += 1
                if t >= len(tones.KEYS):
                    t, i = 0, (i + 1) % len(self._cards)
        finally:
            if self._looping:
                state.toast("Hands-free lesson done. Bien joué !", "ok")
            self._stop_loop()

    def _play_pattern(self, phrase, mood, pattern):
        """fr, fr_pause, en_fr, en_fr_pause, en_pause_fr_pause, fr_en, fr_fr_pause. A pause = time to repeat it."""
        for step in pattern.split("_"):
            if not self._looping:
                return
            if step == "pause":
                pp.wait(pp.last_seconds() + 0.6)
            elif step in ("fr", "en"):
                phrases.speak(phrase, mood, step)
                pp.wait(0.35)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._looping = False
        pp.stop()
        anvil.js.window.PP.musicStop()
        pp.wake(False)
        if pp.recording():
            pp.record_stop()
