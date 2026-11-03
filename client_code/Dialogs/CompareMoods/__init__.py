from anvil import *

from ._anvil_designer import CompareMoodsTemplate
from ... import langs, phrases, pp, state, tones


class CompareMoods(CompareMoodsTemplate):
    """All ten moods of one phrase in a list (the language being learned, English, register). Closes with the mood
    key picked, or None."""

    def __init__(self, phrase=None, mood="Basic", **properties):
        super().__init__(**properties)
        self.phrase = phrase or {}
        fr_map = self.phrase.get("fr") or {}
        en_map = self.phrase.get("en") or {}
        base = fr_map.get("Basic") or ""
        rows = []
        for k in tones.KEYS:
            fr = fr_map.get(k) or ""
            rows.append({"key": k, "label": tones.label(k), "who": tones.TONES[k]["who"], "colour": tones.TONES[k]["colour"],
                         "icon": tones.TONES[k]["icon"], "fr": fr, "en": en_map.get(k) or "",
                         "register": langs.register_text(langs.register(fr, state.lang()), state.lang()),
                         "lang": state.lang(),
                         "html": pp.diff_html(fr, base) if k != "Basic" else "", "on": k == mood})
        self.rows_panel.items = rows
        self.rows_panel.add_event_handler("x-listen", self._listen)
        self.rows_panel.add_event_handler("x-go", self._go)

    def _listen(self, key=None, **event_args):
        phrases.speak_bg(self.phrase, key, "fr")

    def _go(self, key=None, **event_args):
        pp.stop()
        self.raise_event("x-close-alert", value=key)

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        pp.stop()
        self.raise_event("x-close-alert", value=None)
