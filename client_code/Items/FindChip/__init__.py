from anvil import *
import anvil.js

from ._anvil_designer import FindChipTemplate


class FindChip(FindChipTemplate):
    """A chip on the Phrase finder and the Practice call: a suggested search word (kind "word") or a listener / mood
    (kind "mood": its colour and icon). item = {text, value, kind, icon?, colour?, on?}. Clicking raises x-chip on
    the panel with the value and the kind."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        is_mood = i.get("kind") == "mood"
        self.icon_box.visible = bool(i.get("icon"))
        if i.get("icon"):
            self.icon.classes.add("ic-" + i["icon"])
        if i.get("colour"):
            anvil.js.get_dom_node(self).style.setProperty("--tone", i["colour"])
        self.btn.classes["is-mood"] = is_mood
        self.btn.classes["on"] = bool(i.get("on"))
        anvil.js.get_dom_node(self.btn).setAttribute("aria-pressed", "true" if i.get("on") else "false")

    def btn_click(self, event):
        self.parent.raise_event("x-chip", value=self.item["value"], kind=self.item.get("kind") or "word")
