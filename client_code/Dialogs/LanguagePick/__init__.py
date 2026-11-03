from anvil import *

from ._anvil_designer import LanguagePickTemplate
from ... import langs, state


def choices(counts=None):
    """The languages as LangChoice items, the current one marked."""
    counts = counts or {}
    out = []
    for code in langs.CODES:
        n = counts.get(code)
        line = langs.name(code) + (" · %s" % state.plural(int(n), "phrase") if n else "")
        out.append({"code": code, "native": langs.info(code)["native"], "line": line, "on": code == state.lang()})
    return out


class LanguagePick(LanguagePickTemplate):
    """Pick the language to learn (French, Spanish, Italian). Closes with the code picked, or None."""

    def __init__(self, counts=None, **properties):
        super().__init__(**properties)
        self.choices.items = choices(counts)
        self.choices.add_event_handler("x-lang", self._picked)

    def _picked(self, code, **event_args):
        self.raise_event("x-close-alert", value=code)

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
