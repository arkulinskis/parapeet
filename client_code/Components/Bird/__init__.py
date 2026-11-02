from anvil import *

from ._anvil_designer import BirdTemplate

MOODS = ["happy", "wow", "oops", "sleepy", "talk"]


class Bird(BirdTemplate):
    """Parapeet the budgie (SVG in the template). `mood` switches eyes, beak and extras by CSS class."""

    def __init__(self, **properties):
        self._mood, self._size, self._ready = "happy", 120, False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        for m in MOODS:
            self.box.classes["bird-" + m] = m == self._mood
        self.box.style["width"] = "%dpx" % self._size
        self.box.style["height"] = "%dpx" % self._size

    @property
    def mood(self):
        return self._mood

    @mood.setter
    def mood(self, value):
        self._mood = value if value in MOODS else "happy"
        self._draw()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        try:
            self._size = max(24, int(value or 120))
        except Exception:
            self._size = 120
        self._draw()
