from ._anvil_designer import AcknowledgementsTemplate

class Acknowledgements(AcknowledgementsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    
  def got_it_click(self, **event_args):
    self.raise_event("x-close-alert", value="True")
    