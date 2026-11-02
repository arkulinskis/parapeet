from anvil import *

from ._anvil_designer import GesturesTemplate


class Gestures(GesturesTemplate):
    """How to swipe, tap and use the keys on the phrasebook."""

    def __init__(self, **properties):
        super().__init__(**properties)

    @handle("ok_button", "click")
    def ok_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
