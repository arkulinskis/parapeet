from ._anvil_designer import Parapeet_storyTemplate
from anvil import *

class Parapeet_story(Parapeet_storyTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def continue_story_1_click(self, **event_args):
    if self.adventure_name.text != "":
      self.story_1.visible = False
      self.question_1.visible = False
      self.panel_1.visible = False
      story_2 = "  One fateful day, as the townspeople were enjoying their daily activities, Parapeet spotted a young linguistics enthusiast named Alex. Intrigued by <b>the vast amount of knowledge</b> within Alex's mind, the mischievous bird couldn't resist but to swoop down and peck at the language treasure that lay within.<br><br>  As the sun set that day, Alex realized something was amiss! His once-fluent French knowledge had vanished, and in its place were <b>gaps and confusion</b>. He knew that Parapeet was the culprit and vowed to get his French back, <u>feather by feather</u>..."
      self.story_2.content = story_2.replace("Alex", self.adventure_name.text )
      self.story_2.visible = True
      self.start_the_game.visible = True
    else:
      alert("I need your name adventurer!")

  def start_the_game_click(self, **event_args):
    alert("App release date is in two weeks!")

  def adventure_name_pressed_enter(self, **event_args):
    self.continue_story_1_click()


