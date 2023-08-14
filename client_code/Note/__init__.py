from ._anvil_designer import NoteTemplate
# from anvil import *

class Note(NoteTemplate):
  def __init__(self, fr, en, **properties):
    self.init_components(**properties)
    self.the_quote_fr.content = fr
    self.the_quote_en.content = en

  def form_show(self, **event_args):
    self.french_area.focus()




