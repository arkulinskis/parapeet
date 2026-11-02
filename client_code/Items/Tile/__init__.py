from anvil import *

from ._anvil_designer import TileTemplate


class Tile(TileTemplate):
    """A word tile in a "Write this in French" exercise. item = {word, n, used}. A used tile in the word bank stays as
    an empty slot so the others don't jump around. Clicking raises x-tile with the tile number."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.btn.classes["used"] = bool(self.item.get("used"))

    def btn_click(self, event):
        if not self.item.get("used") and not self.item.get("locked"):
            self.parent.raise_event("x-tile", n=self.item["n"])
