from anvil import *

from ._anvil_designer import RingTemplate


class Ring(RingTemplate):
    """The daily-goal ring: a conic gradient filled to `value` percent, with `text` in the middle."""

    def __init__(self, **properties):
        self._value, self._text, self._ready = 0, "", False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        v = max(0, min(100, int(self._value or 0)))
        node = self.dom_nodes["ring"]
        node.style.setProperty("--p", str(v))
        node.classList.toggle("full", v >= 100)
        self.middle.text = self._text

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self._draw()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, v):
        self._text = v or ""
        self._draw()
