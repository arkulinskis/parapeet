from anvil import *
import anvil.js

from ._anvil_designer import DayBarTemplate


class DayBar(DayBarTemplate):
    """One day in the 14-day chart: item = {day, seeds, pct, goal, today}. Gold when the daily goal was met."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.dom_nodes["fill"].style.height = "%d%%" % (max(3, i["pct"]) if i["seeds"] else 0)
        self.box.classes["goal"] = bool(i["goal"])
        self.box.classes["today"] = bool(i["today"])
        anvil.js.get_dom_node(self).setAttribute("title", "%d seeds" % i["seeds"])
