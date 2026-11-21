import random

from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import DuelTemplate
from ... import drills, game, langs, phrases, pp, router, state, tones

CARDS = 5
NAME_MAX = 20


def _clean_name(text):
    """A name from a link or the name box: plain text, one line, at most 20 characters (shown only as Label text)."""
    s = " ".join(str(text or "").replace("/", " ").split())
    return s[:NAME_MAX].strip()


def _clamp_score(text):
    try:
        return max(0, min(CARDS, int(text)))
    except Exception:
        return -1


class Duel(DuelTemplate):
    """#duel: the Mood Duel. Five "which mood is this?" cards, then a challenge link for a friend.
    #duel/<lang>/<12-Boss.15-Lover...>/<name>/<score> is that link: the friend sees "Anna got 4/5", plays the same
    cards (Phrases.duel_cards: basic + free phrases only, so it works signed out), then both scores, confetti on a
    win and a review of the five sentences. The answers' options are seeded per card, so both players get the same
    four. Seeds go through game.record_lesson("duel", None, ...) in the link's language (no lesson stars)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.cards: list = []
        self.queue: list = []
        self.results: list = []
        self.n = 0
        self.answered = False
        self.rival = ""
        self.mine = 0
        self.link_total = CARDS
        self.their = -1
        self.friend = len(args) >= 2
        self.lang = langs.valid(args[0]) if args else state.lang()
        for part in (self.play_part, self.end_part, self.broken_part):
            part.visible = False
        self.intro_part.visible = True
        self.choices_panel.add_event_handler("x-pick", self._pick)
        self.review_panel.add_event_handler("x-listen", self._listen_review)
        self.link_box.enabled = True
        anvil.js.get_dom_node(self.link_box).setAttribute("readonly", "readonly")
        anvil.js.get_dom_node(self.link_box).setAttribute("aria-label", "Challenge link")
        anvil.js.get_dom_node(self.name_box).setAttribute("maxlength", str(NAME_MAX))
        self._keys = anvil.js.report_exceptions(self._key)
        name = langs.name(self.lang)
        if self.friend:
            self.rival = _clean_name(args[2] if len(args) > 2 else "") or "Your friend"
            self.their = _clamp_score(args[3] if len(args) > 3 else "")
            self.cards = self._load(args[1])
            if not self.cards:
                self.intro_part.visible = False
                self.broken_part.visible = True
                self.broken_text.text = "The sentences in this link aren't available any more. Start a fresh duel and send it back."
                return
            self.intro_title.text = ("%s got %d/%d." % (self.rival, min(self.their, self.link_total), self.link_total)) if self.their >= 0 \
                else "%s dares you." % self.rival
            self.intro_text.text = ("Can you tell a boss from a lover in %s? Same %d sentences, your turn. "
                                    "Can you beat that?" % (name, len(self.cards)))
            self.start_button.text = "Take the challenge"
        else:
            self.cards = self._pick_cards()
            self.intro_text.text = ("%d sentences in %s. For each one, guess who it's for: a boss, a lover, a hothead... "
                                    "Then dare a friend to beat your score." % (len(self.cards), name))
            if len(self.cards) < 3:
                self.intro_part.visible = False
                self.broken_part.visible = True
                self.broken_text.text = "There aren't enough %s phrases for a duel yet. Try French, or come back soon." % name
                self.own_button.visible = False

    # ---- the cards
    def _load(self, code):
        pairs = []
        for part in str(code or "").split(".")[:6]:
            bits = part.split("-")
            mood = tones.key_for_label(bits[1]) if len(bits) == 2 else None
            if mood and bits[0].isdigit():
                pairs.append([int(bits[0]), mood])
        if not pairs:
            return []
        self.link_total = len(pairs)
        try:
            return list(anvil.server.call("duel_cards", self.lang, pairs) or [])[:CARDS]
        except Exception:
            return []

    def _pick_cards(self):
        """Five phrases this player can open, each in a different mood that sounds different from the neutral one."""
        pool = list(phrases.all_phrases())
        random.shuffle(pool)
        moods = list(tones.KEYS[1:])
        random.shuffle(moods)
        cards, used = [], set()
        for p in pool:
            if len(cards) >= CARDS:
                break
            options = [k for k in moods if k not in used and (p["fr"].get(k) or "") and p["fr"].get(k) != p["fr"].get("Basic")]
            if not options:
                continue
            mood = options[0]
            used.add(mood)
            cards.append({"id": p["id"], "mood": mood, "text": p["fr"][mood], "en": p["en"].get(mood) or p["en"].get("Basic") or "",
                          "neutral": p["fr"].get("Basic") or ""})
        return cards

    def _code(self):
        return ".".join(["%d-%s" % (c["id"], c["mood"]) for c in self.cards])

    def _exercise(self, c):
        """The same four mood options for everyone who plays this card (seeded by the card)."""
        random.seed(int(c["id"]) * 31 + tones.index_of(c["mood"]))
        ex = drills.mood_quiz({"id": c["id"], "lang": self.lang, "fr": {c["mood"]: c["text"], "Basic": c["neutral"]},
                               "en": {c["mood"]: c["en"]}}, c["mood"], random)
        random.seed(int(window.Date.now()))
        return ex

    # ---- playing
    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        self.queue = [self._exercise(c) for c in self.cards]
        self.results = []
        self.n = 0
        self.intro_part.visible = False
        self.play_part.visible = True
        pp.sfx("tap")
        self._show()

    def _show(self):
        ex, c = self.queue[self.n], self.cards[self.n]
        self.answered = False
        self.step_label.text = "Card %d of %d" % (self.n + 1, len(self.queue))
        for i in range(6):
            node = self.dom_nodes["dot%d" % i]
            node.style.display = "" if i < len(self.queue) else "none"
            node.className = "on" if i == self.n else ("done" if i < self.n else "")
        self.prompt_text.text = ex["prompt"]
        anvil.js.get_dom_node(self.prompt_text).setAttribute("lang", self.lang)
        self.prompt_en.text = c["en"]
        self.prompt_en.visible = bool(self.english_box.checked and c["en"])
        self.bird.mood = "talk"
        self.verdict_box.visible = False
        window.PP_DUEL = {"answer": ex["answer"], "n": self.n, "total": len(self.queue)}  # read by tools/ui tests
        self._render(None)

    def _render(self, picked):
        ex = self.queue[self.n]
        items = []
        for i, o in enumerate(ex["options"]):
            st = ""
            if self.answered:
                st = "right" if o["value"] == ex["answer"] else ("wrong" if o["value"] == picked else "dim")
            items.append({"text": o["text"], "value": o["value"], "n": i + 1, "state": st, "mood": o.get("mood"),
                          "lang": "", "locked": self.answered})
        self.choices_panel.items = items

    @handle("english_box", "change")
    def english_box_change(self, **event_args):
        if self.play_part.visible and self.queue:
            self.prompt_en.visible = bool(self.english_box.checked and self.cards[self.n]["en"])

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        # read in the neutral voice while playing: the mood's own pace and pitch would give the answer away
        pp.fire("say", [self.cards[self.n]["text"], langs.info(self.lang)["tts"], "Basic"])

    def _pick(self, value=None, **event_args):
        if self.answered or not self.queue:
            return
        ex, c = self.queue[self.n], self.cards[self.n]
        ok = value == ex["answer"]
        self.answered = True
        self.results.append({"id": c["id"], "tone": c["mood"], "type": "mood", "ok": ok, "first": ok})
        self._render(value)
        info = tones.TONES[c["mood"]]
        self.verdict_box.visible = True
        self.verdict_box.classes["good"] = ok
        self.verdict_box.classes["bad"] = not ok
        self.verdict_title.text = ("Yes! %s" % info["label"]) if ok else ("It was %s" % info["label"])
        self.verdict_text.text = tones.blurb(c["mood"], self.lang)
        self.bird.mood = "happy" if ok else "oops"
        pp.sfx("good" if ok else "bad")
        self.next_button.text = "See the result" if self.n + 1 >= len(self.queue) else "Next"
        btn = anvil.js.get_dom_node(self.next_button).querySelector("button")
        if btn is not None:
            getattr(btn, "focus")()

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        if not self.answered:
            return
        pp.stop()
        self.n += 1
        if self.n >= len(self.queue):
            self._finish()
        else:
            self._show()

    # ---- the end
    def _finish(self):
        self.play_part.visible = False
        mine = len([r for r in self.results if r["ok"]])
        total = len(self.results)
        seeds = 0
        try:
            res = game.record_lesson("duel", None, self.results, self.lang)
            seeds = int(res.get("seeds") or 0)
        except Exception:
            seeds = 0
        if self.layout is not None:
            self.layout.refresh_stats()
        self.my_score.text = "%d/%d" % (mine, total)
        self.their_box.visible = self.friend and self.their >= 0
        self.their_name.text = self.rival
        self.their_score.text = "%d/%d" % (max(0, min(self.their, self.link_total)), self.link_total)
        won = self.friend and self.their >= 0 and mine > self.their
        if self.friend and self.their >= 0:
            if mine > self.their:
                self.end_title.text = "You win!"
            elif mine == self.their:
                self.end_title.text = "It's a tie!"
            else:
                self.end_title.text = "%s wins this round" % self.rival
        else:
            self.end_title.text = langs.info(self.lang)["perfect"] if mine == total else (
                langs.info(self.lang)["well_done"] if mine >= 3 else "Tricky, right?")
        self.end_line.text = ("+%d seeds. " % seeds if seeds else "") + (
            "Now you know who each sentence is for. Listen to them below." if mine < total else
            "Every mood spotted. Your ears are getting good.")
        self.end_bird.mood = "wow" if (won or mine == total) else ("happy" if mine >= 3 else "oops")
        self.review_panel.items = [{"text": c["text"], "en": c["en"], "mood": c["mood"], "lang": self.lang, "n": i,
                                    "ok": i < len(self.results) and self.results[i]["ok"]} for i, c in enumerate(self.cards)]
        self.share_box.visible = not self.friend
        self.back_button.visible = self.friend
        self.play_button.text = "Back to the trail" if state.me() else "Start playing free"
        if not self.friend:
            self.mine = mine
            self.name_box.text = _clean_name(game.adventurer())
            self._update_link()
        self.end_part.visible = True
        pp.sfx("done")
        if won or mine == total or (not self.friend and mine >= 4):
            pp.confetti()
        window.scrollTo(0, 0)

    def _link(self):
        base = str(window.location.href).split("#")[0]
        name = _clean_name(self.name_box.text) or "A friend"
        return base + router.href("duel", self.lang, self._code(), name, self.mine)

    def _message(self):
        return "I got %d/%d telling a boss from a lover in %s. Your turn:" % (self.mine, len(self.cards), langs.name(self.lang))

    def _update_link(self):
        link = self._link()
        self.link_box.text = link
        state.set_attr(self.wa_link, "href", "https://wa.me/?text=" + window.encodeURIComponent(self._message() + " " + link))

    @handle("name_box", "change")
    def name_box_change(self, **event_args):
        self._update_link()

    @handle("share_button", "click")
    def share_button_click(self, **event_args):
        self._update_link()
        link, text = self._link(), self._message()
        nav = window.navigator
        coarse = bool(window.matchMedia("(pointer: coarse)").matches)
        if coarse and nav.get("share"):
            try:
                nav.share({"title": "Mood Duel on Parapeet", "text": text, "url": link})
                return
            except Exception as e:
                if "abort" in str(e).lower():
                    return  # they closed the share sheet
        try:
            nav.clipboard.writeText(text + " " + link)
            state.toast("Link copied. Paste it to a friend.", "ok")
        except Exception:
            node = anvil.js.get_dom_node(self.link_box)
            inp = node if str(node.tagName).upper() == "INPUT" else node.querySelector("input")
            if inp is not None:
                getattr(inp, "select")()
            state.toast("Copy the link below and send it to a friend.")

    def _listen_review(self, n=0, **event_args):
        c = self.cards[n]
        pp.fire("say", [c["text"], langs.info(self.lang)["tts"], c["mood"]])

    @handle("back_button", "click")
    def back_button_click(self, **event_args):
        if self.lang != state.lang():
            phrases.switch(self.lang)
        router.go("duel")

    @handle("play_button", "click")
    def play_button_click(self, **event_args):
        if self.friend and self.lang != state.lang() and not state.me():
            phrases.switch(self.lang)  # they came to play this language
        router.go("play")

    @handle("own_button", "click")
    def own_button_click(self, **event_args):
        router.go("duel")

    # ---- keys: 1-4 pick, Enter = next
    def _key(self, event):
        if not self.play_part.visible or getattr(event, "ctrlKey", False) or getattr(event, "metaKey", False):
            return
        tag = str(getattr(event.target, "tagName", "") or "").upper()
        if tag in ("INPUT", "TEXTAREA"):
            return
        k = getattr(event, "key", None)
        if k == "Enter" and self.answered:
            event.preventDefault()
            self.next_button_click()
        elif k in ("1", "2", "3", "4") and not self.answered:
            opts = self.queue[self.n]["options"]
            if int(k) - 1 < len(opts):
                self._pick(opts[int(k) - 1]["value"])

    @handle("", "show")
    def form_show(self, **event_args):
        window.document.addEventListener("keydown", self._keys)

    @handle("", "hide")
    def form_hide(self, **event_args):
        window.document.removeEventListener("keydown", self._keys)
        pp.stop()
