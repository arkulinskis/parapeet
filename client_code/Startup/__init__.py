from ._anvil_designer import StartupTemplate
from anvil import users, open_form

class Startup(StartupTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

  def form_show(self, **event_args):
    user = users.get_user()
    if user:
      open_form("Swipe_interface")
    else:
      open_form("Index")

