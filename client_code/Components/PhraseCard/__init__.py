from anvil import *
import anvil.js

from ._anvil_designer import PhraseCardTemplate
from ... import pp, tones


class PhraseCard(PhraseCardTemplate):
    """The swipe card. The JavaScript engine (pp-card.js) moves with the finger; this Form keeps the data, mounts the
    engine while the page is showing (so its keyboard listener goes away with the page) and raises `change` with
    state = {index, tone, key, id, side, count, reason} after every move."""

    def __init__(self, **properties):
        self._cards, self._i, self._t, self._front = [], 0, 0, "fr"
        self._engine, self._keys, self._diff = None, False, True
        super().__init__(**properties)

    # ---- the engine
    def _mount(self):
        if self._engine is not None:
            return
        self._engine = pp.card(self.dom_nodes["mount"], self._changed, on_listen=self._listen, keys=self._keys)
        if not self._diff:
            self._engine.setDiff(False)
        if self._cards:
            self._engine.load(self._cards, self._i, self._t, self._front)

    def _changed(self, st):
        self._i, self._t = int(st.index), int(st.tone)
        self.raise_event("change", state={"index": self._i, "tone": self._t, "key": st.key, "id": st.id,
                                          "side": st.side, "count": int(st.count), "reason": st.reason})

    def _listen(self):
        self.raise_event("listen")

    @handle("", "show")
    def form_show(self, **event_args):
        self._mount()

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._engine is not None:
            self._engine.destroy()
            self._engine = None

    # ---- what pages call
    def load(self, cards, index=0, tone=0, front="fr"):
        """cards: [{id, fr: {mood: text}, en: {mood: text}}]; tone: a mood index (tones.KEYS) or key."""
        self._cards = list(cards or [])
        self._i = int(index or 0)
        self._t = tones.index_of(tone) if isinstance(tone, str) else int(tone or 0)
        self._front = front
        if self._engine is not None:
            self._engine.load(self._cards, self._i, self._t, self._front)

    def go(self, index, tone, direction="left"):
        if self._engine is not None:
            self._engine.go(int(index), tones.index_of(tone) if isinstance(tone, str) else int(tone), direction, "go")

    def next_tone(self):
        if self._engine is not None:
            self._engine.nextTone()

    def prev_tone(self):
        if self._engine is not None:
            self._engine.prevTone()

    def next_phrase(self):
        if self._engine is not None:
            self._engine.nextPhrase()

    def prev_phrase(self):
        if self._engine is not None:
            self._engine.prevPhrase()

    def flip(self):
        if self._engine is not None:
            self._engine.flip()

    def set_front(self, lang):
        self._front = lang
        if self._engine is not None:
            self._engine.setFront(lang)

    def flash(self, kind="good"):
        if self._engine is not None:
            self._engine.flash(kind)

    def mark(self, name, on):
        """A CSS class on the card: 'pc-known', 'pc-listening', 'pc-recording'."""
        if self._engine is not None:
            self._engine.mark(name, bool(on))

    @property
    def index(self):
        return self._i

    @property
    def tone(self):
        return self._t

    @property
    def keys(self):
        return self._keys

    @keys.setter
    def keys(self, value):
        self._keys = bool(value)

    @property
    def diff(self):
        return self._diff

    @diff.setter
    def diff(self, value):
        self._diff = bool(value)
        if self._engine is not None:
            self._engine.setDiff(self._diff)
