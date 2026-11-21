from anvil import *
import anvil.js

from ._anvil_designer import DuelReviewTemplate
from ... import tones


class DuelReview(DuelReviewTemplate):
    """One sentence on the Mood Duel's end screen: the sentence, the right mood (colour and icon), the English, whether
    you got it, and Listen. item = {text, en, mood, ok, lang, n}. Listen raises x-listen on the panel with n."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        info = tones.TONES[i["mood"]]
        anvil.js.get_dom_node(self).style.setProperty("--tone", info["colour"])
        self.mood_icon.classes.add("ic-" + info["icon"])
        self.mood_label.text = "%s: to %s" % (info["label"], info["who"]) if i["mood"] != "Basic" else "Neutral: to anyone"
        self.text_label.text = i["text"]
        anvil.js.get_dom_node(self.text_label).setAttribute("lang", i.get("lang") or "fr")
        self.en_label.text = i.get("en") or ""
        ok = bool(i.get("ok"))
        self.mark_icon.classes.add("ic-check" if ok else "ic-x")
        self.row.classes["ok"] = ok
        self.row.classes["miss"] = not ok
        anvil.js.get_dom_node(self.mark_box).setAttribute("aria-label", "You got it" if ok else "Missed")

    @handle("listen_button", "click")
    def listen_button_click(self, **event_args):
        self.parent.raise_event("x-listen", n=self.item["n"])
