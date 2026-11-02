from anvil import *

from ._anvil_designer import BadgeChipTemplate


class BadgeChip(BadgeChipTemplate):
    """A badge: item = {id, name, desc, icon, earned, new}. Not yet earned = greyed out."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.icon.classes.add("ic-" + (self.item.get("icon") or "star"))
        self.box.classes["earned"] = bool(self.item.get("earned"))
        self.box.classes["new"] = bool(self.item.get("new"))
