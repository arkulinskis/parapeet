from ._anvil_designer import IndexTemplate
from anvil import open_form, alert, users
from anvil.js.window import document #, setTimeout, clearTimeout
import anvil.js
from ..Parapeet_story import Parapeet_story
from ..more_info import more_info

class Index(IndexTemplate):
  def __init__(self, ignore_login = False, **properties):
    # Set Form properties and Data Bindings.
    self.ignore_login = ignore_login
    self.init_components(**properties)
    self.myTimeout = 0
    document.getElementsByTagName("body")[0].classList.remove("unscrollable")
    
    self.more_info_form = more_info()
    self.parapeet_story = Parapeet_story()
    
    
  def get_started_click(self, **event_args):
    self.get_started.visible = False
    self.starting.visible = True
    open_form("Swipe_interface")

  # def play_promo_click(self, **event_args):
  #   anvil.js.call("lockWakeState")
  #   self.playpromo()

  def form_show(self, **event_args):
    self.get_started.visible = True
    if not self.ignore_login:
      get_user = users.get_user()
      if get_user != None:
        self.get_started.visible = False
        self.starting.visible = True
        open_form("Swipe_interface")
  
    # self.newVideo = document.createElement("video")
    # self.newVideo.classList.add("invisible")
    # self.newVideo.type = r"video/mp4"
    # self.newVideo.src = "tbd"
    # self.played = False
    # document.getElementById("appGoesHere").appendChild(self.newVideo)
    # # anvil.js.get_dom_node(self.newVideo).addEventListener("click", self.stopplayback)    
    # self.newVideo.addEventListener("click", self.stopplayback)

  # def playpromo(self, **args):
  #   if self.played == False:
  #     tmpblob = server.call("get_video", "promo")
  #     print(tmpblob)
  #     self.newVideo.src = tmpblob
  #     self.played = True
  #   self.newVideo.classList.remove("invisible");
  #   self.newVideo.classList.add("on_top");
  #   self.newVideo.poster = "_/theme/logo-color.png"
  #   try:
  #     self.newVideo.play();
  #     self.myTimeout = setTimeout(self.stopplayback, 43000 - self.newVideo.currentTime * 1000);
  #   except:
  #     print("no video loaded yet")

  # def stopplayback(self, event=True, **args):
  #   self.newVideo.classList.remove("on_top");
  #   self.newVideo.classList.add("invisible");
  #   self.newVideo.pause();
  #   clearTimeout(self.myTimeout);
  #   if self.newVideo.currentTime * 1000 > 42888:
  #     self.newVideo.currentTime = 0
  #   anvil.js.call("releaseWakeState")

  def showstory_click(self, **event_args):
    result = alert(self.parapeet_story, large=True)
    if result == "launch":
      self.get_started_click()
      print("launch")

  def more_info_click(self, **event_args):
    result = alert(self.more_info_form, large=True)

      

