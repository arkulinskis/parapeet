from anvil import *
import anvil.js

from ._anvil_designer import MoodBarTemplate


class MoodBar(MoodBarTemplate):
    """One mood's mastery bar on the progress page. item = {key, label, colour, icon, pct, right}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.icon.classes.add("ic-" + i["icon"])
        anvil.js.get_dom_node(self).style.setProperty("--tone", i["colour"])
        self.dom_nodes["fill"].style.width = "%d%%" % max(2, i["pct"])
        self.pct.text = "%d%%" % i["pct"]
        anvil.js.get_dom_node(self).setAttribute("title", "%d right answers in this mood" % i["right"])
