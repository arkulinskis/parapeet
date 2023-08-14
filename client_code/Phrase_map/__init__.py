from ._anvil_designer import Phrase_mapTemplate
from anvil import alert, server, users

class Phrase_map(Phrase_mapTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.phrase_pack = "water_cooler"

  def water_cooler_click(self, **event_args):
    self.phrase_pack = "water_cooler"
    self.raise_event("x-close-alert", value=1)

  def presentation_click(self, **event_args):
    self.phrase_pack = "presentation"
    self.raise_event("x-close-alert", value=2)

  def board_room_click(self, **event_args):
    self.phrase_pack = "board_room"
    self.raise_event("x-close-alert", value=3)
    
  def premium_click(self, **event_args):
    if users.get_user() is not None:
      response = alert("Thank you for the interest - still working on it! Would you like to be notified once it is available?", buttons=[("Yes","Yes"),("No","No")])
      server.call('send_interest',response)   
    else:
      response = alert("Thank you for the interest - still working on it!", buttons=[("Yes","Yes"),("No","No")])
      server.call('send_interest', response)

  def close_click(self, **event_args):
    self.raise_event("x-close-alert", value=-1)

  def points_summary_click(self, **event_args):
    """This method is called when the link is clicked"""
    pass






