from ._anvil_designer import Loop_optionsTemplate
# from anvil import *

class Loop_options(Loop_optionsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.radiogroup = 3
    self.ok_columns = []
    self.lesson_type = ""

  def begin_loop_click(self, **event_args):
    self.lesson_type = self.ref.get_group_value()
    self.sound_on = self.playsound.checked
    self.music_on = self.background_music.checked

    if self.client.checked: self.ok_columns.append("Client")
    if self.boss.checked: self.ok_columns.append("Boss")
    if self.lover.checked: self.ok_columns.append("Lover")
    if self.impressed.checked: self.ok_columns.append("Impressed")
    if self.sad.checked: self.ok_columns.append("Sad")
    if self.basic.checked: self.ok_columns.append("Basic")
    if self.stupid.checked: self.ok_columns.append("Stupid")
    if self.agressive.checked: self.ok_columns.append("Agressive")
    if self.frustrated.checked: self.ok_columns.append("Frustrated")
    if self.colleague.checked: self.ok_columns.append("Colleague")
      
    self.raise_event("x-close-alert", value="begin")

  def time_slider_slide(self, handle, **event_args):
    self.lesson_minutes.text = "Duration: " + str(int(self.time_slider.value)) + " minutes"

  def Later_click(self, **event_args):
    self.raise_event("x-close-alert", value="cancel")

    












