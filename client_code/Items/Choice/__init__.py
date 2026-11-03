from anvil import *
import anvil.js

from ._anvil_designer import ChoiceTemplate
from ... import state, tones


class Choice(ChoiceTemplate):
    """One answer in a lesson. item = {text, value, n, state ("", "picked", "right", "wrong", "dim"), mood?, lang}.
    A mood answer gets the mood's colour and icon. Clicking raises x-pick on the panel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.num.text = str(i.get("n") or "")
        mood = i.get("mood")
        self.mood_box.visible = bool(mood)
        if mood:
            self.mood_icon.classes.add("ic-" + tones.TONES[mood]["icon"])
            anvil.js.get_dom_node(self).style.setProperty("--tone", tones.TONES[mood]["colour"])
            self.btn.classes["is-mood"] = True
        st = i.get("state") or ""
        for s in ("picked", "right", "wrong", "dim"):
            self.btn.classes[s] = st == s
        if i.get("lang") == "fr":  # the language being learned (langs.py)
            anvil.js.get_dom_node(self.txt).setAttribute("lang", state.lang())

    def btn_click(self, event):
        if not self.item.get("locked"):
            self.parent.raise_event("x-pick", value=self.item["value"])
