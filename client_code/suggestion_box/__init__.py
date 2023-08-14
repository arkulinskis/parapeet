from ._anvil_designer import suggestion_boxTemplate
# from anvil import *

class suggestion_box(suggestion_boxTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def suggestion_text_show(self, **event_args):
    self.suggestion_text.focus()

