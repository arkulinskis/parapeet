from anvil import *

from ._anvil_designer import MoodSampleTemplate
from ... import tones


class MoodSample(MoodSampleTemplate):
    """One mood on the landing page: its colour, icon and name, who it's for, the sample sentence and the English.
    item = {key, who, text, en, lang}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        t = tones.TONES[i["key"]]
        d = self.dom_nodes
        d["box"].style.setProperty("--tone", t["colour"])
        d["icon"].classList.add("ic-" + t["icon"])
        d["label"].textContent = t["label"]
        d["who"].textContent = i["who"]
        d["text"].textContent = i["text"]
        d["text"].setAttribute("lang", i["lang"])
        d["en"].textContent = i["en"]
