from anvil import *
import anvil.js

from ._anvil_designer import MoodRowTemplate


class MoodRow(MoodRowTemplate):
    """One mood of a phrase in the compare dialog. The words that differ from the neutral version are highlighted
    (pp.diff_html escapes the text and only adds <mark>)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.icon.classes.add("ic-" + i["icon"])
        self.who.text = "to " + i["who"] if i["key"] != "Basic" else "to anyone"
        self.dom_nodes["fr"].innerHTML = i["html"] or ""
        if not i["html"]:
            self.dom_nodes["fr"].textContent = i["fr"]
        anvil.js.get_dom_node(self).style.setProperty("--tone", i["colour"])
        self.row.classes["on"] = bool(i["on"])

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        self.parent.raise_event("x-listen", key=self.item["key"])

    @handle("go_button", "click")
    def go_button_click(self, **event_args):
        self.parent.raise_event("x-go", key=self.item["key"])
