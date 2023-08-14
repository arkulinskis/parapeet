from ._anvil_designer import Test_resultTemplate
# from anvil import *
import anvil.js

class Test_result(Test_resultTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def next_click(self, **event_args):
    self.raise_event("x-close-alert", value="next")

  def form_show(self, **event_args):
    a = anvil.js.get_dom_node(self.next)
    a.focus()



