from anvil import *

from ._anvil_designer import UnitPathTemplate


class UnitPath(UnitPathTemplate):
    """One unit on the trail: its banner and a winding path of lesson nodes. Passes the nodes' x-lesson event on to
    the Play page."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        self.icon.classes.add("ic-" + i["icon"])
        self.box.classes["unit-%d" % i["number"]] = True
        self.kicker.text = "Unit %d · %d phrases" % (i["number"], i["count"])
        self.progress.text = "%d/%d" % (i["done"], i["total"]) if i["total"] else "Locked"
        self.nodes_panel.items = i["lessons"]
        self.nodes_panel.add_event_handler("x-lesson", self._lesson)

    def _lesson(self, lesson=None, **event_args):
        self.parent.raise_event("x-lesson", lesson=lesson)
