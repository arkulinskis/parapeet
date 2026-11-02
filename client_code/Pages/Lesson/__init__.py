import random

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import LessonTemplate
from ... import drills, game, gamerules as G, phrases, pp, router, state, tones

SAY_PASS = 0.72
PRAISE = ["Nice!", "Très bien !", "Bravo !", "Exactly!", "Super !", "Spot on!", "Parfait !"]


class Lesson(LessonTemplate):
    """#lesson/<key>: a lesson from the trail ("u1-1", the unit challenge "u1-mix") or "review" (weak spots).
    About ten exercises (drills.py); a wrong answer comes back once at the end; then the end screen with seeds,
    stars, streak and new badges. The page hides the header and tab bar (Shell: no-chrome) like a game screen."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.key = args[0] if args else ""
        self.kind, self.queue, self.results, self.answer, self.picked = "lesson", [], {}, None, []
        self.popped, self.seeds_now, self.checked = 0, 0, False
        self.ex: dict = {}
        for part in (self.end_part, self.missing_part, self.foot, self.ex_part):
            part.visible = False
        self.choices_panel.add_event_handler("x-pick", self._pick)
        self.bank_panel.add_event_handler("x-tile", self._pick_tile)
        self.answer_panel.add_event_handler("x-tile", self._unpick_tile)
        self._keys = anvil.js.report_exceptions(self._key)
        off_until = state.store_get("speak_off_until", 0) or 0
        self.can_say = pp.can_listen() and window.Date.now() > off_until
        self._build()

    # ---- the exercises
    def _build(self):
        prog = game.progress()
        everything = phrases.all_phrases()
        cards = None
        if self.key == "review":
            self.kind = "review"
            pairs = [(p["id"], k) for p in everything for k in tones.KEYS if p["fr"].get(k)]
            by_id = dict((p["id"], p) for p in everything)
            cards = [(by_id[i], m) for i, m in G.due(prog, pairs, game.today(), 10) if i in by_id]
            lesson_phrases, pool = [], everything
            self.lesson_ids = [p["id"] for p, m in cards]
        else:
            lesson = phrases.lesson_by_key(self.key, prog)
            if lesson is None:
                return self._missing()
            self.kind = lesson["kind"]
            lesson_phrases = [p for p in everything if p["id"] in lesson["ids"]]
            pool = phrases.in_unit(lesson["unit"])
            self.lesson_ids = lesson["ids"]
            if self.kind == "challenge":
                cards = []
                for p in lesson_phrases:
                    moods = [k for k in tones.KEYS[1:] if p["fr"].get(k)]
                    random.shuffle(moods)
                    cards += [(p, m) for m in moods[:2]]
                random.shuffle(cards)
                cards = cards[:14]
        size = 12 if self.kind == "challenge" else 10
        self.queue = drills.lesson(lesson_phrases, pool, prog, size, self.can_say, cards=cards)
        if not self.queue:
            return self._missing("There's nothing to practise here yet.")
        self.total = len(self.queue)
        self.ex_part.visible = self.foot.visible = True
        self._show()

    def _missing(self, text=None):
        self.missing_part.visible = True
        locked = "signup" in self.key and not state.me()
        self.missing_join.visible = locked
        self.missing_text.text = text or ("A free account unlocks this lesson and keeps your seeds on every device."
                                          if locked else "More phrases for this unit are on the way.")

    def _show(self):
        ex = self.ex = self.queue[0]
        self.answer, self.picked, self.checked = None, [], False
        window.PP_EX = {"type": ex["type"], "answer": ex["answer"], "options": ex.get("options") or [],
                        "tiles": ex.get("tiles") or []}  # read by tools/ui/flow.js
        kind = ex["type"]
        self.ex_title.text = ex["title"]
        mood = ex.get("show_mood") or ex["mood"]
        self.prompt_mood.visible = not ex.get("hide_mood") and kind != "listen"
        self.prompt_mood.text = tones.label(mood)
        anvil.js.get_dom_node(self.prompt_mood).style.setProperty("--tone", tones.TONES[mood]["colour"])
        self.prompt_text.text = ex.get("prompt") or ""
        self.prompt_text.visible = bool(ex.get("prompt"))
        anvil.js.get_dom_node(self.prompt_text).setAttribute("lang", ex.get("lang") or "fr")
        self.speak_button.visible = ex.get("lang") == "fr" and kind not in ("listen",) and bool(ex.get("prompt"))
        self.big_listen_box.visible = kind == "listen"
        self.prompt_box.classes["is-listen"] = kind == "listen"
        self.bird.mood = "talk"
        self._render_choices()
        self.build_part.visible = kind == "build"
        if kind == "build":
            self.answer_panel.items = []
            self._render_tiles()
        self.say_part.visible = kind == "say"
        self.heard_label.text = ""
        self.foot.classes["good"] = self.foot.classes["bad"] = False
        self.foot_title.text = self.foot_text.text = ""
        self.check_button.visible = kind != "say"
        self.check_button.enabled = False
        self.next_button.visible = False
        self.dom_nodes["fill"].style.width = "%d%%" % int(100 * self.popped / max(1, self.popped + len(self.queue)))
        if kind == "listen":
            self._speak(ex["audio"], ex["mood"])

    def _render_choices(self):
        ex = self.ex
        opts = ex.get("options") or []
        if not opts:
            self.choices_panel.items = []
            self.choices_panel.visible = False
            return
        self.choices_panel.visible = True
        lang = "en" if ex["type"] == "meaning" else ("fr" if ex["type"] in ("listen", "switch") else "")
        items = []
        for n, o in enumerate(opts):
            st = ""
            if self.checked:
                st = "right" if o["value"] == ex["answer"] else ("wrong" if o["value"] == self.answer else "dim")
            elif o["value"] == self.answer:
                st = "picked"
            items.append({"text": o["text"], "value": o["value"], "n": n + 1, "state": st, "mood": o.get("mood"),
                          "lang": lang, "locked": self.checked})
        self.choices_panel.items = items
        self.choices_panel.role = ["ls-choices", "moods"] if ex["type"] == "mood" else ["ls-choices"]

    def _render_tiles(self):
        tiles = self.ex["tiles"]
        by_n = dict((t["n"], t) for t in tiles)
        self.answer_panel.items = [{"word": by_n[n]["word"], "n": n, "locked": self.checked} for n in self.picked]
        self.bank_panel.items = [{"word": t["word"], "n": t["n"], "used": t["n"] in self.picked, "locked": self.checked} for t in tiles]

    def _speak(self, text, mood):
        p = phrases.find(self.ex["id"])
        if p is not None and (p["fr"].get(mood) or "") == text:
            phrases.speak_bg(p, mood, "fr")
        else:
            pp.fire("say", [text, "fr", mood])

    # ---- answering
    def _pick(self, value=None, **event_args):
        if self.checked:
            return
        self.answer = value
        pp.sfx("tap")
        self._render_choices()
        self.check_button.enabled = True

    def _pick_tile(self, n=None, **event_args):
        if self.checked or n in self.picked:
            return
        self.picked.append(n)
        self._render_tiles()
        self.check_button.enabled = True

    def _unpick_tile(self, n=None, **event_args):
        if self.checked or n not in self.picked:
            return
        self.picked.remove(n)
        self._render_tiles()
        self.check_button.enabled = bool(self.picked)

    @handle("speak_button", "click")
    def speak_button_click(self, **event_args):
        self._speak(self.ex.get("prompt"), self.ex.get("show_mood") or self.ex["mood"])

    @handle("big_listen", "click")
    def big_listen_click(self, **event_args):
        self._speak(self.ex["audio"], self.ex["mood"])

    @handle("mic_button", "click")
    def mic_button_click(self, **event_args):
        if self.checked:
            return
        self.mic_button.text, self.mic_button.role = "Listening...", ["mic", "ic-mic", "on"]
        try:
            heard = pp.listen("fr-CA")
        finally:
            self.mic_button.text, self.mic_button.role = "Tap and speak", ["mic", "ic-mic"]
        if heard["error"]:
            self.heard_label.text = {"not-allowed": "The microphone is blocked. Allow it, or tap \"I can't speak right now\".",
                                     "unsupported": "This browser can't check speech."}.get(heard["error"], "I didn't catch that. Tap and try again.")
            return
        score = pp.best_similarity(self.ex["answer"], heard["alternatives"] or [heard["transcript"]])
        self.heard_label.text = "I heard: \"%s\" (%d%% match)" % (heard["transcript"], int(score * 100))
        self.answer = heard["transcript"]
        self._verdict(score >= SAY_PASS)

    @handle("skip_say", "click")
    def skip_say_click(self, **event_args):
        state.store_set("speak_off_until", window.Date.now() + 30 * 60 * 1000)
        self.can_say = False
        self.queue = [e for e in self.queue if e["type"] != "say"]
        if not self.queue:
            return self._finish()
        state.toast("No speaking exercises for 30 minutes.")
        self._show()

    @handle("check_button", "click")
    def check_button_click(self, **event_args):
        if self.checked or not self.check_button.enabled:
            return
        ex = self.ex
        if ex["type"] == "build":
            by_n = dict((t["n"], t["word"]) for t in ex["tiles"])
            answer = " ".join(by_n[n] for n in self.picked)
        else:
            answer = self.answer
        self._verdict(drills.check(ex, answer))

    def _verdict(self, ok):
        ex = self.ex
        self.checked = True
        key = "%s:%s:%s" % (ex["id"], ex["mood"], ex["type"])
        r = self.results.get(key)
        if r is None:
            self.results[key] = {"id": ex["id"], "tone": ex["mood"], "type": ex["type"], "ok": ok, "first": ok}
            if ok:
                self.seeds_now += G.SEEDS["first_try"]
        else:
            r["ok"] = r["ok"] or ok
            if ok:
                self.seeds_now += G.SEEDS["second_try"]
        if not ok and not ex.get("retry"):
            again = dict(ex)
            again["retry"] = True
            self.queue.append(again)
        self.seeds_label.text = str(self.seeds_now)
        self.foot.classes["good"], self.foot.classes["bad"] = ok, not ok
        self.verdict_icon.classes["ic-check"], self.verdict_icon.classes["ic-x"] = ok, not ok
        if ok:
            self.foot_title.text = random.choice(PRAISE)
            self.foot_text.text = tones.TONES[ex["mood"]]["blurb"] if ex["type"] in ("mood", "switch") else ""
            self.bird.mood = "happy"
            pp.sfx("good")
        else:
            self.foot_title.text = "Not quite. The right answer:"
            self.foot_text.text = ex.get("solution") or ""
            self.bird.mood = "oops"
            pp.sfx("bad")
        self._render_choices()
        if ex["type"] == "build":
            self._render_tiles()
        self.check_button.visible = False
        self.next_button.visible = True
        self.next_button.text = "Continue" if ok else "Got it"
        btn = anvil.js.get_dom_node(self.next_button).querySelector("button")
        if btn is not None:
            getattr(btn, "focus")()  # so Enter continues

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        if not self.checked:
            return
        pp.stop()
        self.queue.pop(0)
        self.popped += 1
        if not self.queue:
            self._finish()
        else:
            self._show()

    def _finish(self):
        self.ex_part.visible = self.foot.visible = False
        self.dom_nodes["fill"].style.width = "100%"
        res = game.record_lesson(self.kind, "" if self.kind == "review" else self.key, list(self.results.values()))
        s = game.summary()
        acc = int(round(100 * (res.get("accuracy") or 0)))
        self.end_title.text = "Parfait !" if acc == 100 else ("Bien joué !" if acc >= 70 else "Lesson done!")
        lines = []
        if "goal" in (res.get("events") or []):
            lines.append("Daily goal reached: +10 bonus seeds.")
        if "streak" in (res.get("events") or []):
            lines.append("Your streak is now %d %s." % (s["streak"], "day" if s["streak"] == 1 else "days"))
        lines.append(s["stage_line"])
        self.end_line.text = " ".join(lines)
        self.end_seeds.text = "+%d" % (res.get("seeds") or 0)
        self.end_acc.text = "%d%%" % acc
        self.end_streak.text = "%d" % s["streak"]
        stars = int(res.get("stars") or 0)
        self.end_stars.text = "★" * stars + "☆" * (3 - stars) if self.kind != "review" else ""
        new = [dict(id=b, name=G.BADGE_INFO[b][1], desc=G.BADGE_INFO[b][2], icon=G.BADGE_INFO[b][3], earned=True, new=True)
               for b in (res.get("badges") or []) if b in G.BADGE_INFO]
        self.badges_panel.items = new
        self.badges_panel.visible = bool(new)
        self.end_bird.mood = "wow" if acc >= 90 else ("happy" if acc >= 60 else "oops")
        self.guest_note.visible = not state.me()
        self.end_part.visible = True
        pp.sfx("done")
        if acc >= 70 or new:
            pp.confetti()
        if self.layout is not None:
            self.layout.refresh_stats()

    @handle("again_button", "click")
    def again_button_click(self, **event_args):
        first = (self.lesson_ids or [None])[0]
        router.go("practice", first) if first else router.go("practice")

    @handle("done_button", "click")
    def done_button_click(self, **event_args):
        router.go("play")

    @handle("quit_button", "click")
    def quit_button_click(self, **event_args):
        if self.end_part.visible or self.missing_part.visible or not self.results:
            router.go("play")
            return
        if confirm("Your answers in this lesson won't count.", title="Leave the lesson?",
                   buttons=[("Keep going", False), ("Leave", True)], role="app-dialog"):
            router.go("play")

    # ---- keys: 1-4 pick, Enter = check / continue, Backspace = take back the last tile
    def _key(self, event):
        if not self.ex or self.end_part.visible or event.ctrlKey or event.metaKey or event.altKey:
            return
        tag = str(getattr(event.target, "tagName", "") or "").upper()
        if tag in ("INPUT", "TEXTAREA"):
            return
        k = event.key
        if k == "Enter":
            event.preventDefault()
            if self.checked:
                self.next_button_click()
            elif self.check_button.enabled and self.check_button.visible:
                self.check_button_click()
        elif k in ("1", "2", "3", "4") and self.ex.get("options") and not self.checked:
            n = int(k) - 1
            if n < len(self.ex["options"]):
                self._pick(self.ex["options"][n]["value"])
        elif k == "Backspace" and self.ex["type"] == "build" and self.picked and not self.checked:
            event.preventDefault()
            self._unpick_tile(self.picked[-1])

    @handle("", "show")
    def form_show(self, **event_args):
        window.document.addEventListener("keydown", self._keys)

    @handle("", "hide")
    def form_hide(self, **event_args):
        window.document.removeEventListener("keydown", self._keys)
        pp.stop()
