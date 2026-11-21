from anvil import *
import anvil.js

from ._anvil_designer import FindRowTemplate
from ... import langs, tones


class FindRow(FindRowTemplate):
    """One Phrase finder result: the phrase in the chosen mood (falls back to the neutral version when that mood has
    no text), its English, the formal / familiar badge, and Listen / Save / All moods / Open card. item = {phrase,
    mood, lang}. The buttons raise x-row on the panel with what="listen" | "save" | "moods" | "open"."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        p, mood, code = i["phrase"], i["mood"], i.get("lang") or langs.DEFAULT
        shown = mood if (p["fr"].get(mood) or "") else "Basic"
        text = p["fr"].get(shown) or ""
        info = tones.TONES[shown]
        self.mood_icon.classes.add("ic-" + info["icon"])
        self.mood_label.text = info["label"]
        anvil.js.get_dom_node(self).style.setProperty("--tone", info["colour"])
        self.text_label.text = text
        anvil.js.get_dom_node(self.text_label).setAttribute("lang", code)
        self.en_label.text = (p.get("en") or {}).get(shown) or (p.get("en") or {}).get("Basic") or ""
        reg = langs.register(text, code)
        self.register_label.text = langs.register_text(reg, code)
        self.register_label.visible = bool(reg)
        self.shown = shown

    def _raise(self, what):
        self.parent.raise_event("x-row", what=what, phrase=self.item["phrase"], mood=self.shown)

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        self._raise("listen")

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self._raise("save")

    @handle("moods_button", "click")
    def moods_button_click(self, **event_args):
        self._raise("moods")

    @handle("open_button", "click")
    def open_button_click(self, **event_args):
        self._raise("open")
