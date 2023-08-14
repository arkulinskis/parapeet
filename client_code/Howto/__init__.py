from ._anvil_designer import HowtoTemplate
# from anvil import *

class Howto(HowtoTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def got_it_click(self, **event_args):
    self.raise_event("x-close-alert", value="True")

