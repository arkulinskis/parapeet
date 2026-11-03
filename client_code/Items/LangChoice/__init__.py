from anvil import *

from ._anvil_designer import LangChoiceTemplate
from ... import langs


class LangChoice(LangChoiceTemplate):
    """One language in the language picker (Dialogs.LanguagePick, the landing page).
    item = {code, native, line, on}. Clicking raises x-lang on the panel with the language code."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.dom_nodes["flag"].style.background = langs.flag_css(i["code"])
        self.btn.classes["on"] = bool(i.get("on"))
        self.on_mark.visible = bool(i.get("on"))

    def btn_click(self, event):
        self.parent.raise_event("x-lang", code=self.item["code"])
