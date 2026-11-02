from anvil import *

from ._anvil_designer import NoteRowTemplate
from ... import pp, state


class NoteRow(NoteRowTemplate):
    """One saved phrase: French, meaning, its quiz level (5 dots), listen / edit / delete (x-changed reloads the list)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        level = int(self.item.get("level") or 0)
        for n, dot in enumerate([self.dom_nodes["d0"], self.dom_nodes["d1"], self.dom_nodes["d2"], self.dom_nodes["d3"], self.dom_nodes["d4"]]):
            dot.classList.toggle("on", n < level)
        self.dom_nodes["level"].setAttribute("title", "Quiz level %d of 5" % int(self.item.get("level") or 0))

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        pp.fire("say", [self.item["fr"], "fr", "Basic"])

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        from ...Dialogs.NoteEdit import NoteEdit
        if alert(NoteEdit(fr=self.item["fr"], en=self.item["en"], note_id=self.item["id"]), buttons=[], role="app-dialog"):
            state.toast("Saved", "ok")
            self.parent.raise_event("x-changed")

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm(self.item["fr"], title="Remove this phrase?", buttons=[("Cancel", False), ("Remove", True)],
                   role="app-dialog"):
            if state.call("remove_note", self.item["id"]) is not None:
                self.parent.raise_event("x-changed")
