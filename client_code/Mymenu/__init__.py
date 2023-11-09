from ._anvil_designer import MymenuTemplate
import anvil.users
import anvil.server
from anvil import alert
from ..suggestion_box import suggestion_box

class Mymenu(MymenuTemplate):
  def __init__(self, signed_in=False, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.mymode = "Phrases_French"
    if signed_in:
      self.signed_in = True
      self.signin.text = "Sign out"
    else:
      self.signed_in = False
      self.signin.text = "Sign in"

      
  def signin_click(self, **event_args):
    # if anvil.users.get_user() is not None:
    if self.signed_in:
      r = alert("Sign out?", buttons=[("Yes", True),("No", False)])
      if r:
        anvil.users.logout()
        self.signed_in = False
        self.signin.text = "Sign in"
        self.raise_event("x-close-alert", value="Index")
    else:
      user = anvil.users.login_with_form(allow_cancel=True)
      if anvil.users.get_user() is not None:
        self.signin.text = "Sign out"
        self.signed_in = True
        self.raise_event("x-close-alert", value="True")
      else:
        self.signin.text = "Sign in"
        self.signed_in = False
        self.raise_event("x-close-alert", value="Index")

  def practice_phrases_click(self):
    self.mymode = "Phrases_French"
    self.raise_event("x-close-alert", value="Phrases")
    
  def practice_phrases_english_click(self):
    self.mymode = "Phrases_English"
    self.raise_event("x-close-alert", value="Phrases")

  def toindex_click(self, **event_args):
    self.raise_event("x-close-alert", value="Index")

  def buthelp_click(self, **event_args):
    self.raise_event("x-close-alert", value="Help")
    
  def recall_meaning_click(self):
    self.mymode = "Notes_word"
    self.raise_event("x-close-alert", value="Notes")

  def recall_word_click(self):
    self.mymode = "Notes_meaning"
    self.raise_event("x-close-alert", value="Notes")

  def form_show(self, **event_args):
    if anvil.users.get_user() is None:
      self.signin.text = "Sign in"
    else:
      self.signin.text = "Sign out"

  def test_word_click(self):
    self.mymode = "Tests_word"
    self.raise_event("x-close-alert", value="Tests")

  def test_meaning_click(self):
    self.mymode = "Tests_meaning"
    self.raise_event("x-close-alert", value="Tests")




  def suggestion_click(self, **event_args):
    tmp = suggestion_box()
    result = alert(tmp, buttons=[("Submit","Submit"),("Cancel","Cancel")], title="Feedback helps us improve")
    if result == "Submit":
      anvil.server.call("send_interest",tmp.suggestion_text.text)
      alert("Thank you!")

  def testing_click(self, **event_args):
    if self.english_mode.checked:
      self.test_meaning_click()
    else:
      self.test_word_click()

  def flashcards_click(self, **event_args):
    if self.english_mode.checked:
      self.recall_word_click()
    else:
      self.recall_meaning_click()

  def phrasebook_click(self, **event_args):
    if self.english_mode.checked:
      self.practice_phrases_english_click()
    else:
      self.practice_phrases_click()

  def got_it_click(self, **event_args):
    self.raise_event("x-close-alert", value="True")

  def ackno_click(self, **event_args):
    self.raise_event("x-close-alert", value="ackno")

  def LOGO_click(self, **event_args):
    self.raise_event("x-close-alert", value="Index")

  def closeacc_click(self, **event_args):
    get_user = anvil.users.get_user()
    if get_user != None:
      r = alert("Delete account? WARNING you will lose all your notes in the app.", buttons=[("Delete account", True),("Cancel", False)])
      if r:
        anvil.server.call('delete_account')
  






      






    



      











