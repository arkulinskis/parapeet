from anvil import *

from ._anvil_designer import HandsFreeTemplate
from ... import langs, state, tones

# "{lang}" = the language being learned; in a pattern "fr" is that language too (see langs.py)
PATTERNS = [
    ("{lang}, then time to repeat", "fr_pause"),
    ("English, {lang}, then repeat", "en_fr_pause"),
    ("English, guess, {lang}, repeat", "en_pause_fr_pause"),
    ("{lang} twice, then repeat", "fr_fr_pause"),
    ("{lang}, then English", "fr_en"),
    ("English, then {lang}", "en_fr"),
]


class HandsFree(HandsFreeTemplate):
    """Options for the hands-free lesson (the old "Create a lesson plan"). Closes with
    {pattern, minutes, moods, skip_known, music}, or None. The choices are remembered in this browser."""

    def __init__(self, **properties):
        super().__init__(**properties)
        saved = state.store_json("handsfree", {}) or {}
        name = langs.name(state.lang())
        self.pattern_drop.items = [(label.replace("{lang}", name), value) for label, value in PATTERNS]
        self.pattern_drop.selected_value = saved.get("pattern") or "fr_pause"
        self.minutes_drop.items = [("5 minutes", 5), ("10 minutes", 10), ("15 minutes", 15), ("20 minutes", 20), ("30 minutes", 30)]
        self.minutes_drop.selected_value = saved.get("minutes") or 5
        moods = saved.get("moods")
        if moods:
            for k in tones.KEYS:
                getattr(self, "m_" + k).checked = k in moods
        if "skip_known" in saved:
            self.skip_known.checked = bool(saved["skip_known"])
        self.music.checked = bool(saved.get("music"))

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        moods = [k for k in tones.KEYS if getattr(self, "m_" + k).checked]
        if not moods:
            self.message.text, self.message.visible = "Pick at least one mood.", True
            return
        opts = {"pattern": self.pattern_drop.selected_value, "minutes": self.minutes_drop.selected_value,
                "moods": moods, "skip_known": self.skip_known.checked, "music": self.music.checked}
        state.store_json_set("handsfree", opts)
        self.raise_event("x-close-alert", value=opts)
