from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import FindTemplate
from ... import finder, langs, phrases, router, state, tones

START = 8  # phrases shown before anything is typed


class Find(FindTemplate):
    """#find[/<words>[/<mood label>]]: the Phrase finder. "What do you need to say, and to whom?" A search box with
    suggestion chips (finder.suggestions: they always match), a row of listeners (the ten moods) with a register tip,
    then the phrases that match, each said to the chosen listener (Items.FindRow: Listen, Save, All moods, Open card).
    Searching runs in the browser over the phrases this person may open (finder.py); guests also learn how many
    member phrases match (Phrases.count_locked_matches, counts only). No match: the "oops" bird and Ask for this
    phrase (members, ask_for_more: it shows in Admin) or Join free. The address keeps the search (bookmark, share)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._lang = state.lang()
        self._all = phrases.all_phrases()
        self._idx = finder.index(self._all)
        self._timer = 0
        self._slow_timer = 0
        self._asked = ""
        self._locked_q = ""
        query = args[0] if args else ""
        mood = tones.key_for_label(args[1]) if len(args) > 1 else None
        if len(args) == 1 and tones.key_for_label(query):  # "#find/boss": a listener, nothing typed
            mood, query = tones.key_for_label(query), ""
        self._mood = mood or finder.listener(query) or state.store_get("find_mood", "Basic")
        if self._mood not in tones.KEYS:
            self._mood = "Basic"
        self._heard = finder.listener(query) or ""
        self.query_box.text = query
        anvil.js.get_dom_node(self.query_box).setAttribute("aria-label", "What do you need to say?")
        self.chips_panel.items = [{"text": text, "value": value, "kind": "word", "icon": "search"}
                                  for text, value in finder.suggestions(self._idx)]
        self.chips_panel.add_event_handler("x-chip", self._chip)
        self.moods_panel.add_event_handler("x-chip", self._chip)
        self.results_panel.add_event_handler("x-row", self._row)
        self.locked_box.visible = False
        self._run(False)

    # ---- searching
    def _query(self):
        return (self.query_box.text or "").strip()

    def _run(self, update_hash=True):
        q, mood = self._query(), self._mood
        info = tones.TONES[mood]
        self.moods_panel.items = [{"text": tones.label(k), "value": k, "kind": "mood", "icon": tones.TONES[k]["icon"],
                                   "colour": tones.TONES[k]["colour"], "on": k == mood} for k in tones.KEYS]
        self.tip_who.text = ("Talking to %s" % info["who"]) if mood != "Basic" else "Talking to anyone"
        self.tip_label.text = tones.tip(mood, self._lang)
        anvil.js.get_dom_node(self.tip_box).style.setProperty("--tone", info["colour"])
        self.clear_button.visible = bool(q)
        who = ("to %s" % info["who"]) if mood != "Basic" else "to anyone"
        words = finder.terms(q)
        if not words:
            items = self._all[:START]
            self.count_label.text = ("A few to start with, said %s" % who) if items else ""
        else:
            found = finder.search(self._idx, self._all, q, mood)
            items = found["items"]
            total = found["total"]
            self.count_label.text = "%s %s%s" % (state.plural(total, "phrase"), who,
                                                 " (the best 20)" if total > len(items) else "")
        self.results_panel.items = [{"phrase": p, "mood": mood, "lang": self._lang} for p in items]
        self.results_panel.visible = bool(items)
        nothing = bool(words) and not items
        self.empty_box.visible = nothing or not self._all
        self.count_label.visible = not self.empty_box.visible
        self.bird.mood = "oops" if nothing else ("happy" if words else "talk")
        me = state.me()
        if self.empty_box.visible:
            if self._all:
                self.empty_text.text = "No phrase matches \"%s\" yet. %s" % (
                    q, "Ask for it and we'll add it to the library." if me else
                    "Members can ask for it, and we'll add it to the library.")
            else:
                self.empty_text.text = "The phrase library for %s is still being written." % langs.name(self._lang)
            self.ask_button.visible = bool(me) and bool(q) and self._asked != q.lower()
            self.join_button.visible = not me
        if not words or me:
            self.locked_box.visible = False
        if update_hash:
            if q:
                router.replace("find", q, tones.label(mood).lower())
            else:
                router.replace("find", tones.label(mood).lower())
        window.PP_FIND = {"count": len(items), "mood": mood, "query": q}  # read by tools/ui tests
        self._schedule_locked()

    def _schedule(self, ms=220):
        if self._timer:
            window.clearTimeout(self._timer)
        self._timer = window.setTimeout(self._tick, ms)

    def _tick(self):
        self._timer = 0
        self._run()

    def _schedule_locked(self):
        """Guests: once typing settles, ask the server how many member phrases also match (counts only)."""
        if self._slow_timer:
            window.clearTimeout(self._slow_timer)
            self._slow_timer = 0
        if state.me() or not finder.terms(self._query()):
            return
        self._slow_timer = window.setTimeout(self._count_locked, 700)

    def _count_locked(self):
        self._slow_timer = 0
        q = self._query()
        if q == self._locked_q or not finder.terms(q):
            return
        self._locked_q = q
        n = 0
        try:
            r = anvil.server.call_s("count_locked_matches", self._lang, q)
            n = int((r or {}).get("signup") or 0)
        except Exception:
            n = 0  # no line rather than an error
        if q != self._query():
            return
        self.locked_box.visible = n > 0
        if self.results_panel.visible:
            self.locked_label.text = "%s match with a free account." % state.plural(n, "more phrase")
        else:
            self.locked_label.text = "%s for members match \"%s\". A free account opens them." % (
                state.plural(n, "phrase"), q)

    @handle("query_box", "change")
    def query_box_change(self, **event_args):
        picked = finder.listener(self._query()) or ""
        if picked and picked != self._heard:  # a new listener word ("boss") picks the mood once; a chip still wins
            self._mood = picked
        self._heard = picked
        self._schedule()

    @handle("query_box", "pressed_enter")
    def query_box_pressed_enter(self, **event_args):
        self._schedule(0)
        node = anvil.js.get_dom_node(self.query_box)
        inp = node if str(node.tagName).upper() == "INPUT" else node.querySelector("input")
        if inp is not None:
            getattr(inp, "blur")()  # phones: close the keyboard so the results show

    @handle("clear_button", "click")
    def clear_button_click(self, **event_args):
        self.query_box.text = ""
        self.locked_box.visible = False
        self._run()
        self.query_box.focus()

    def _chip(self, value=None, kind="word", **event_args):
        if kind == "mood":
            self._mood = value if value in tones.KEYS else "Basic"
            state.store_set("find_mood", self._mood)
        else:
            self.query_box.text = value or ""
        self._run()

    # ---- a result's buttons
    def _row(self, what=None, phrase=None, mood="Basic", **event_args):
        p = phrase or {}
        if not p:
            return
        if what == "listen":
            phrases.speak_bg(p, mood, "fr")
        elif what == "open":
            router.go("practice", p["id"], tones.label(mood).lower())
        elif what == "moods":
            from ...Dialogs.CompareMoods import CompareMoods
            picked = alert(CompareMoods(phrase=p, mood=mood), buttons=[], role="app-dialog", large=True)
            if picked:
                router.go("practice", p["id"], tones.label(picked).lower())
        elif what == "save":
            self._save(p, mood)

    def _save(self, p, mood):
        if not state.me():
            if confirm("Your saved phrases live in your account, so you can review them anywhere.",
                       title="Save phrases with a free account", buttons=[("Not now", False), ("Join free", True)],
                       role="app-dialog"):
                router.remember_after(window.location.hash)
                router.go("auth", "signup")
            return
        from ...Dialogs.NoteEdit import NoteEdit
        en = p["en"].get(mood) or ""
        if alert(NoteEdit(fr=p["fr"].get(mood) or "", en="%s (%s)" % (en, tones.label(mood)) if en else ""),
                 buttons=[], role="app-dialog"):
            state.toast("Saved to your phrasebook", "ok")

    # ---- nothing found
    @handle("ask_button", "click")
    def ask_button_click(self, **event_args):
        q = self._query()
        if not q or not state.me():
            return
        topic = "find: %s (to %s, %s)" % (q[:40], tones.label(self._mood), self._lang)
        if state.call("ask_for_more", topic) is not None:
            self._asked = q.lower()
            self.ask_button.visible = False
            self.empty_bird.mood = "happy"
            state.toast("Thanks! Parapeet will learn to say that.", "ok")

    @handle("join_button", "click")
    def join_button_click(self, **event_args):
        router.remember_after(window.location.hash)
        router.go("auth", "signup")

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._timer:
            window.clearTimeout(self._timer)
        if self._slow_timer:
            window.clearTimeout(self._slow_timer)
        self._timer = 0
        self._slow_timer = 0
