from ._anvil_designer import Swipe_interfaceTemplate
# from anvil import *
import anvil.server
import anvil.users
from anvil import open_form, alert
import datetime
from anvil.js.window import similarity, document, navigator, MediaRecorder, Audio, Blob, URL, location
import anvil.js
from anvil_extras.storage import indexed_db
import random
from anvil_extras.animation import Effect, Transition, animate, fade_in, fade_out
from ..Mymenu import Mymenu
from ..Note import Note
from ..Test_result import Test_result
from ..Howto import Howto
from ..Loop_options import Loop_options
from ..Phrase_map import Phrase_map
from ..Acknowledgements import Acknowledgements
import time
import re


if 1:
  slide_in_up = Transition(translateY=["100%", 0])
  slide_in_down = Transition(translateY=["-100%", 0])
  slide_in_left = Transition(translateX=["-100%", 0])
  slide_in_right = Transition(translateX=["100%", 0])
  slide_out_up = reversed(slide_in_down)
  slide_out_down = reversed(slide_in_up)
  slide_out_left = reversed(slide_in_left)
  slide_out_right = reversed(slide_in_right)
  zoom_in = Transition(scale=[.3, 1])
  zoom_out = reversed(zoom_in)
  fly_in_up = slide_in_up | zoom_in | fade_in
  fly_in_down = slide_in_down | zoom_in | fade_in
  fly_in_left = slide_in_left | zoom_in | fade_in
  fly_in_right = slide_in_right | zoom_in | fade_in
  fly_out_up = reversed(fly_in_down)
  fly_out_down = reversed(fly_in_up)
  fly_out_left = reversed(fly_in_left)
  fly_out_right = reversed(fly_in_right)
  pulse = Transition(scale=[1, 1.5, 1])
  
  sentences_store = indexed_db.create_store("fs_store")
  
  speech_notworking = False
  try:
    from anvil.js.window import webkitSpeechRecognition
    print("import voice recognition succesful")
  except:
    speech_notworking = True
    print("import voice recognition failed")
  

class Swipe_interface(Swipe_interfaceTemplate):
  def __init__(self, **properties):
    global sentences_store
    self.init_components(**properties)

    self.audio_disabled = True
    self.stream=None
    
    self.audioElement = document.getElementById('myaudio')
    self.sourceElement = document.getElementById("mysource")
      
    document.getElementsByTagName("body")[0].classList.add("unscrollable")
        
    self.on_keydown = self.on_keydown #key moment right there
    self.on_refocus = self.on_refocus #key moment right there
    self.on_blur = self.on_blur #key moment right there
      
    self.selected_category_number = 1
    self.catching = False
    self.myhowto = Howto()
    self.myackno = Acknowledgements()
    self._setup = False
    self.audio_chunks=[]
    self.recorder=None

    self.music_1 = None
    self.music_2 = None
    self.music_3 = None
    self.keepplaying = False

    self.recognition = None
    self.transcript = ""
    self.str_to_catch = ""
    self.cong_list = ['Amazing!', 'Wonderful!', 'Glorious!', 'Fantsatic!', 'Woohoo!']
    
    self.app_ready = False

    self.playing_recorded = False
    self.playing_example = False
    self.recording_audio = False
    self.rec_start_time = None
    self.rec_finish_time = None

    self.lesson_start_time = None   

    self.side_showing = "French"
    self.side_default = "French"
    self.swipe_type = "click"
    
    self.myloopoptions = Loop_options()
    self.myphrasemap = Phrase_map()
    
    self.click_time = datetime.datetime.now()
    self.ccols=["Basic","Colleague","Client","Boss","Agressive","Frustrated","Sad","Lover","Impressed","Stupid"]

    self.word_or_meaning = "word"
    self.looping = False
    self.audio_length_recorded = 0
    
    content_panel = anvil.js.get_dom_node(self.swipezone)
    content_panel.addEventListener('touchstart', self.on_touch_start)
    content_panel.addEventListener('touchmove', self.on_touch_move)
    content_panel.addEventListener('touchend', self.on_touch_end)
    content_panel.addEventListener('click', self.on_click)

    self.touch_start_x = None
    self.touch_end_x = None
    self.touch_start_y = None
    self.touch_end_y = None
    self.noalert = True

    self.notes_showing_item = 0

  def face_click(self, **event_args):
    self.noalert = False
    result = alert(self.myhowto, buttons=[], large = True)#, title="How to get around the app?")
    self.noalert = True
       
  def on_keydown(self, event):
    if str(event) == "<KeyboardEvent proxyobject>":
      if self.app_ready == False:
        pass
      else:
        if event.key == "ArrowDown":
          self.swipe_up()
        elif event.key == "ArrowUp":
          self.swipe_down()
        elif event.key == "ArrowRight":
          self.swipe_left()
        elif event.key == "ArrowLeft":
          self.swipe_right()
        elif event.key == " ":
          if self.mymenuv.mymode[0:7] == "Phrases" and self.noalert:
            self.on_click("spacebar")
        elif event.key == "Enter":
          if self.mymenuv.mymode[0:7] == "Phrases" and self.noalert:
            self.play_example_click()
    
  def launch_user_app(self, fresh_launch=True):
    if fresh_launch:
      if "user_data_date" in sentences_store:
        if "user_data_type" in sentences_store:
          responsev = anvil.server.call('update_local_storage',sentences_store["user_data_date"],sentences_store["user_data_type"])
        else:
          responsev = anvil.server.call('update_local_storage',sentences_store["user_data_date"],"free")
      else:
        responsev = anvil.server.call('update_local_storage',datetime.datetime(2022,7,1,0,0,0),"free")
      
      if responsev != "yougood":
        sentences_store["user_data_date"] = responsev["user_data_date"]
        sentences_store["user_data_type"] = responsev["user_data_type"]
        sentences_store["rows"] = responsev["rows"]
        sentences_store["rows_english"] = responsev["rows_english"]


    self.usable_sentences = []
    self.usable_english = []
    for count, i in enumerate(sentences_store["rows"]):
      if i["CategoryID"] == self.selected_category_number:
        self.usable_english.append(sentences_store["rows_english"][count])
        self.usable_sentences.append(i) #todo to use instead of sentences_store["rows"]

    self.sentence_count = len(self.usable_sentences)

    if self.mymenuv.signed_in:
      self.mylikes = anvil.server.call("get_points")
    else:
      print("not logged-in 1")
      self.mylikes = False
    self.update_points() 
    
    self.row_showing_order = []
    self.row_showing_item = 0
    self.row_random = random.choice([i for i in range(0,self.sentence_count) if i not in self.row_showing_order])
    self.row_showing_order.append(self.row_random)
    self.active_column = 0

    self.menulaunch_click(use_to_log_in = self.mymenuv.mymode.split("_")[0])
    # if self.mymenuv.mymode[0:7] == "Phrases":
    #   self.update_visual()
    # elif self.mymenuv.mymode[0:5] == "Notes" or self.mymenuv.mymode[0:5] == "Tests":
    #   self.update_notes_visual()
    
    anvil.server.call_s('send_interest', "launched")
    
    self.app_ready = True
    self.like_button.foreground = "#2C3673"
    self.catch_panel.foreground = "#2C3673"
    self.check_button.foreground = "#2C3673"
    self.answer_panel.foreground = "#2C3673"
    self.hands_free_mode.foreground = "#2C3673"
    self.play_example.foreground = "#2C3673"
    self.record.foreground = "#ff2e2e"
    self.play_recorded.foreground = "#2C3673"
    self.button_add_note.foreground = "#2C3673"
    self.launch_level_select.foreground = "#2C3673"
    self.butdown.foreground = "#2C3673"
    self.butright.foreground = "#2C3673"
    self.butleft.foreground = "#2C3673"
    self.butup.foreground = "#2C3673"
 
  def on_touch_start(self, event):
    self.touch_start_x = event.touches[0].clientX
    self.touch_start_y = event.touches[0].clientY
  
  def on_touch_move(self, event):
    self.touch_end_x = event.touches[0].clientX
    self.touch_end_y = event.touches[0].clientY
  
  def on_touch_end(self, event):
    if self.touch_start_x is not None and self.touch_end_x is not None and self.app_ready:
      swipe_distance_x = self.touch_end_x - self.touch_start_x
      swipe_distance_y = self.touch_end_y - self.touch_start_y
      if abs(swipe_distance_x) > abs(swipe_distance_y):
        if swipe_distance_x > 50:
          self.swipe_right()
        elif swipe_distance_x < -50:
          self.swipe_left()
      else:
        if swipe_distance_y > 50:
          self.swipe_down()
        elif swipe_distance_y < -50:
          self.swipe_up()
    self.touch_start_x = None
    self.touch_end_x = None
    self.touch_start_y = None
    self.touch_end_y = None

  def on_click(self, event):
    # print(str(event.target.outerHTML))
    if self.audio_disabled:
      self.audio_recording_example = Audio()
      self.audio_recording_example.src = r"data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";
      
      
      self.audio_recording = Audio()
      # self.audio_recording.src = r"data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";
      self.background_music = Audio()
      self.background_music.src = r"data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";
      
      self.audio_disabled = True
      
    if self.app_ready == False:
      pass
    elif event == "spacebar" or (
      not str(event.target.outerHTML).startswith(r'<i class="anvil-component-icon') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">Get') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">Just') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">Listening - Stop') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">You got it!') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">Test yourself!') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">HOW TO') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">MENU') and \
      not str(event.target.outerHTML).startswith(r'<div class="link-text" style="display: inline-block;">You') and \
      
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">Get') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">Just') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">Listening - Stop') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">You got it!') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">Test yourself!') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">HOW TO') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">MENU') and \
      not str(event.target.outerHTML).startswith(r'<div style="display: inline-block;" class="link-text">You') and \
      not str(event.target.outerHTML).startswith(r'<div class="anvil-spacing-above-none anvil-spacing-below-none anvil-image anvil-component" src="data:image/png;base64,')
                                
                                ):
      self.swipe_type = "click"
      # print(event.target.outerHTML)
      if self.mymenuv.mymode[0:7] == "Phrases":
        if self.side_showing == "English":
          self.side_showing = "French"            
        else:
          self.side_showing = "English"
        self.update_visual()
      elif self.mymenuv.mymode[0:5] == "Notes":
        if self.word_or_meaning == "word":
          self.word_or_meaning = "meaning"
        else:
          self.word_or_meaning = "word"

        self.update_notes_visual()
      elif self.mymenuv.mymode[0:5] == "Tests":
        pass
        
      self.click_time = datetime.datetime.now()
  
  def swipe_right(self, ignore_animation=False):
    self.swipe_type = "right"
    if self.mymenuv.mymode[:7] == "Phrases":
      self.active_column -= 1
      if self.active_column == -1: self.active_column = 9
      self.update_visual()
    elif self.mymenuv.mymode[:5] == "Notes":
      if self.word_or_meaning == "word":
        self.word_or_meaning = "meaning"
      else:
        self.word_or_meaning = "word"
      self.update_notes_visual()
    else:
      pass

  def swipe_left(self, ignore_animation=False):
    self.swipe_type = "left"
    if self.mymenuv.mymode[:7] == "Phrases":
      self.active_column += 1
      if self.active_column == 10: self.active_column = 0
      self.update_visual()
    elif self.mymenuv.mymode[:5] == "Notes":
      if self.word_or_meaning == "word":
        self.word_or_meaning = "meaning"
      else:
        self.word_or_meaning = "word"
      self.update_notes_visual()
    else:
      pass
    
  def swipe_up(self, ignore_animation=False):
    self.swipe_type = "up"
    if self.mymenuv.mymode[:7] == "Phrases":
      self.row_showing_item += 1
      self.active_column = 0
      if self.row_showing_item >= len(self.row_showing_order):#if not loaded
        if self.row_showing_item >= self.sentence_count:#check if not loadable
          self.row_showing_item = 0
          # self.row_showing_item -= 1
          # self.active_column = 0 
        else:
          self.row_random = random.choice([i for i in range(0,self.sentence_count) if i not in self.row_showing_order])
          self.row_showing_order.append(self.row_random)
          # self.active_column = 0
      self.update_visual()
    elif self.mymenuv.mymode[0:5] == "Notes" or self.mymenuv.mymode[0:5] == "Tests":
      if self.notes_count > 0:
        self.word_or_meaning = self.mymenuv.mymode[6:]
        self.notes_showing_item += 1
        if self.notes_showing_item >= len(self.notes_showing_order):#if not loaded
          if self.notes_showing_item >= len(self.mynotes):#check if not loadable
            self.notes_showing_item -= 1
          else:
            self.notes_random = random.choice([i for i in range(0,self.notes_count) if i not in self.notes_showing_order])
            self.notes_showing_order.append(self.notes_random)
        self.update_notes_visual()
          
  def swipe_down(self, ignore_animation=False):
    self.swipe_type = "down"
    if self.mymenuv.mymode[:7] == "Phrases":
      self.row_showing_item -= 1
      if self.row_showing_item <= -1:
        self.row_showing_item = 0
      self.active_column = 0
      self.update_visual()
    elif self.mymenuv.mymode[0:5] == "Notes" or self.mymenuv.mymode[0:5] == "Tests":
      if self.notes_count > 0:
        self.word_or_meaning = self.mymenuv.mymode[6:]
        self.notes_showing_item -= 1
        if self.notes_showing_item <= -1:
          self.notes_showing_item = 0
        self.update_notes_visual()
  
  def update_visual(self):
    if self.catching:
      self.catching = False
      self.show_text.border = ""
      self.recognition.abort()  

    
    self.hide_show_text()
    self.show_text.visible = False
    
    tmp0 = self.row_showing_order[self.row_showing_item]    
    
    col_to_like = self.usable_sentences[tmp0]["LineID"]
    if self.mymenuv.signed_in:
      # print(self.mylikes)
      if self.mylikes[self.ccols[self.active_column]][col_to_like] == "0" or self.mylikes[self.ccols[self.active_column]][col_to_like] == "1":
        self.catch_button.text = "Test yourself!"
        self.catch_button.background = "#ffffff"
      elif self.mylikes[self.ccols[self.active_column]][col_to_like] == "2" or self.mylikes[self.ccols[self.active_column]][col_to_like] == "3":
        self.catch_button.text = "You got it!"
        self.catch_button.background = "#96ff96"
      if self.mylikes[self.ccols[self.active_column]][col_to_like] == "0" or self.mylikes[self.ccols[self.active_column]][col_to_like] == "2":
        self.like_button.icon = "fa:thumbs-o-up"
      elif self.mylikes[self.ccols[self.active_column]][col_to_like] == "1" or self.mylikes[self.ccols[self.active_column]][col_to_like] == "3":
        self.like_button.icon = "fa:thumbs-up"
    else:
      self.like_button.icon = "fa:thumbs-o-up"
      self.catch_button.text = "Test yourself!"
      
    if self.swipe_type == "click":
      if self.side_showing == "French":
        tmp1 = self.usable_sentences
      else:
        tmp1 = self.usable_english
    else:
      self.side_showing = self.side_default
      if self.side_default == "French":
        tmp1 = self.usable_sentences
      else:
        tmp1 = self.usable_english

    if self.side_default == self.side_showing:
      self.show_text.role = "noscbar_inner"
    else:
      self.show_text.role = "noscbar_inner_inv"

    tmp = tmp1[tmp0]
    # # print("tmp", tmp)
    # self.hide_show_text()
    # self.show_text.visible = False
    self.show_text.content = tmp[self.ccols[self.active_column]].replace(r"/", r" / ")
    if len(self.show_text.content) > 160:
      self.show_text.font_size = 24
    elif len(self.show_text.content) > 100:
      self.show_text.font_size = 28
    elif len(self.show_text.content) > 50:
      self.show_text.font_size = 32
    else:
      self.show_text.font_size = 40
      
    tmpcnt = "Phrase " + str(self.row_showing_item+1) + r" / " + str(len(self.usable_sentences))
    self.progress_label.text = tmpcnt + '  -  type: ' + self.ccols[self.active_column] 
    self.show_text.visible = True

  def update_notes_visual(self):

    if len(self.mynotes) > 0:
      tmp = self.mynotes[self.notes_showing_order[self.notes_showing_item]]
      self.hide_show_text()     
      self.show_text.visible = False    
      if self.word_or_meaning == "word":
        self.show_text.content = str(tmp["French"])
      elif self.word_or_meaning == "meaning":
        self.show_text.content = str(tmp["Comment"])
      self.progress_label.text = self.mymenuv.mymode[:4] + " " + str(self.notes_showing_item+1) + r" / " + str(len(self.mynotes))
      self.show_text.visible = True
    else:
      self.show_text.content = "no notes"

    if self.word_or_meaning == self.mymenuv.mymode[6:]:
      self.show_text.role = "noscbar_inner"
    else:
      self.show_text.role = "noscbar_inner_inv"
      
  def hide_show_text(self):
    if self.looping:
      animate(self.show_text, zoom_out, duration=20).wait()
    else:
      if self.swipe_type == "right":
        animate(self.show_text, fly_out_right, duration=100).wait()#.commitStyles()
      elif self.swipe_type == "left":
        animate(self.show_text, fly_out_left, duration=100).wait()#.commitStyles()
      elif self.swipe_type == "up":
        animate(self.show_text, fly_out_up, duration=100).wait()#.commitStyles()
      elif self.swipe_type == "down":
        animate(self.show_text, fly_out_down, duration=100).wait()#.commitStyles()
      elif self.swipe_type == "click":
        animate(self.show_text, zoom_out, duration=100).wait()#.commitStyles()

  def show_text_show(self, **event_args):
    if self.looping:
      animate(self.show_text, zoom_in, duration=20).wait()
    else:
      if self.swipe_type == "right":
        animate(self.show_text, fly_in_left, duration=200).wait()#.commitStyles()
      elif self.swipe_type == "left":
        animate(self.show_text, fly_in_right, duration=200).wait()#.commitStyles()
      elif self.swipe_type == "down":
        animate(self.show_text, fly_in_down, duration=200).wait()#.commitStyles()
      elif self.swipe_type == "up":
        animate(self.show_text, fly_in_up, duration=200).wait()#.commitStyles()
      elif self.swipe_type == "click":
        animate(self.show_text, zoom_in, duration=200).wait()#.commitStyles()

  def menulaunch_click(self, use_to_log_in = False, **event_args):
    current_log_in_state = self.mymenuv.signed_in
    if use_to_log_in == False:
      self.noalert = False
      result = alert(content=self.mymenuv, large=True, buttons=[])
      self.noalert = True
    else:
      result = use_to_log_in
      
    if result == "Index":
      open_form("Index")
    else:
      if self.mymenuv.signed_in:
        self.getaccount.visible = False
      else:
        self.getaccount.visible = True
        
      if current_log_in_state != self.mymenuv.signed_in:
        self.launch_user_app()

      if result == "Help":
        self.face_click()
      elif result == "ackno":
        self.noalert = False
        alert(self.myackno, buttons=[], large = True)
        self.noalert = True
      elif result == "Tests":
        anvil.js.get_dom_node(self.show_panel).classList.add("centermove")
        if self.mymenuv.mymode[6:] == "word":
          self.current_mode.text = "Test EN"
        else:
          self.current_mode.text = "Test FR" 
        self.like_button.visible = False
        self.catch_panel.visible = False
        self.check_button.visible = True
        self.answer_panel.visible = True
        self.hands_free_mode.visible = False
        self.play_example.visible = False
        self.record.visible = False
        self.play_recorded.visible = False
        self.button_add_note.visible = False
        self.launch_level_select.visible = False
      elif result == "Notes":
        anvil.js.get_dom_node(self.show_panel).classList.remove("centermove")
        if self.mymenuv.mymode[6:] == "word":
          self.current_mode.text = "Notes FR"
        else:
          self.current_mode.text = "Notes EN"   
        self.like_button.visible = False
        self.catch_panel.visible = False
        self.check_button.visible = False
        self.answer_panel.visible = False
        self.hands_free_mode.visible = False
        self.play_example.visible = False
        self.record.visible = True
        self.play_recorded.visible = True
        self.button_add_note.visible = True
        self.button_add_note.icon = "fa:pencil"
        self.launch_level_select.visible = False
      elif result == "Phrases":
        anvil.js.get_dom_node(self.show_panel).classList.remove("centermove")
        if self.mymenuv.mymode[8:] == "English":
          self.current_mode.text = "Phrasebook EN"
        else:
          self.current_mode.text = "Phrasebook FR"   
        self.like_button.visible = True
        self.catch_panel.visible = True
        self.check_button.visible = False
        self.answer_panel.visible = False
        self.hands_free_mode.visible = True
        self.play_example.visible = True
        self.record.visible = True
        self.play_recorded.visible = True
        self.button_add_note.visible = True
        self.button_add_note.icon = "fa:plus"
        self.launch_level_select.visible = True
        
      if result == "Notes" or result == "Tests":
        self.mynotes = anvil.server.call('get_notes')
        self.notes_count = len(self.mynotes)
        self.word_or_meaning = self.mymenuv.mymode[6:]
        if self.notes_count != 0:
          self.notes_showing_order = []
          self.notes_showing_item = 0
          self.notes_random = random.choice([i for i in range(0,self.notes_count) if i not in self.notes_showing_order])
          self.notes_showing_order.append(self.notes_random)
          self.update_notes_visual()
        else:
          self.show_text.content = "no notes"
      elif result == "Phrases":
        self.side_showing = self.mymenuv.mymode[8:]
        self.side_default = self.mymenuv.mymode[8:]
        self.swipe_type = "click"
        self.update_visual()
        
  def butdown_click(self, **event_args):
    self.swipe_up()

  def butright_click(self, **event_args):
    self.swipe_left()

  def butleft_click(self, **event_args):
    self.swipe_right()

  def butup_click(self, **event_args):
    self.swipe_down()

  def on_refocus(self, event):
    anvil.js.call("lockWakeState")
    try:
      anvil.server.call_s("is_alive_check")
    except:
      location.reload()

  def on_blur(self, event):
    anvil.js.call("releaseWakeState")
      
  def form_show(self, **event_args):
    anvil.js.call("lockWakeState")
    if self._setup:
      return
    # dom_node = anvil.js.get_dom_node(self.swipezone)
    document.addEventListener("keydown", self.on_keydown)
    anvil.js.window.addEventListener("focus", self.on_refocus)
    anvil.js.window.addEventListener("blur", self.on_blur)
    # print("onkeydown assigned")
    
    if anvil.users.get_user() is None:
      self.getaccount.visible = True
      self.mymenuv = Mymenu(signed_in=False)
    else:
      self.getaccount.visible = False
      self.mymenuv = Mymenu(signed_in=True)
    self.launch_user_app()
    
    if self.mymenuv.signed_in == False:
      self.face_click()
      animate(self.how_to_panel, pulse, duration=500)
  
  def getaccount_click(self, **event_args):
    if self.app_ready == False:
      self.noalert = False
      alert("Still loading the app...")
      self.noalert = True
    else:
      user = anvil.users.login_with_form(allow_cancel=True)
      if anvil.users.get_user() is not None:
        self.getaccount.visible = False
        self.mymenuv.signed_in = True
        self.launch_user_app()
        

  def play_example_click(self, **event_args):
    if self.looping or (self.app_ready == False):
      pass
    elif self.playing_example:
      self.playing_example = False
      try:
        self.audio_recording_example.pause()
        self.audio_recording_example.currentTime = 0
      except:
        print("can't pause")
      self.play_example.font_size = 30
      self.play_example.foreground ="#2C3673"
      self.play_example.icon = "fa:play"
    else:
      self.playing_example = True
      self.play_example.font_size = 60
      self.play_example.foreground ="#05cc2d"
      self.play_example.icon = "fa:square"
      mydone = self.play_on_screen()
      if self.playing_example: self.play_example_click()

  def play_on_screen(self, language="french", twice=False, pause_after_first=False, pause_after_second=False):
    if self.app_ready == False:
      pass
    else:
      tmp0 = self.row_showing_order[self.row_showing_item]
      tmp = self.usable_sentences[tmp0]
      tmpblob = anvil.server.call("get_voice", tmp["LineID"],  self.ccols[self.active_column], language)
      
      ###
      
      self.audio_recording_example.src = tmpblob # self.audio_recording_example = Audio(tmpblob)
      
      if language == "english":
        self.audio_recording_example.volume = 0.3
      else:
        self.audio_recording_example.volume = 1
      try:
        if self.playing_example or self.looping:
          self.audio_recording_example.play()
          print("playing audio", tmp0, language)
          audio_length = self.audio_recording_example.duration
          time.sleep(audio_length)
          if pause_after_first:
            time.sleep(audio_length)
          
          if twice and self.looping:
            time.sleep(0.5)
            self.audio_recording_example.play()
            audio_length = self.audio_recording_example.duration
            time.sleep(audio_length)
            if pause_after_second:
              time.sleep(audio_length)
      except:
        print("error 1")
        
      return "done"
 
  def record_click(self, **event_args):
    if self.looping or self.app_ready == False:
      pass
    else:
      if self.recording_audio:  
        self.recorder.stop()
        self.recording_audio = False
        self.record.font_size = 30
        self.record.icon = "fa:circle"
        self.show_text.border = ""
        self.stopMicrophone()
        self.rec_finish_time = time.time()
        # self.recorder = None ###
        # self.stream = None ###
        
      else:
        self.audio_chunks=[]
        self.stream = navigator.mediaDevices.getUserMedia({'audio': True})
        self.recorder=MediaRecorder(self.stream)
        self.recorder.ondataavailable = self.save_audio
        self.recorder.start()
        self.rec_start_time = time.time()
        self.recording_audio = True
        self.show_text.border = "3px solid #ff2e2e"
        self.record.font_size = 60
        self.record.icon = "fa:square"

  def save_audio(self,e):
    self.audio_chunks.append(e.data)
    js_blob = Blob(self.audio_chunks, {type: 'audio/wav'})
    self.audio_url = URL.createObjectURL(js_blob)
    self.sourceElement.src = self.audio_url
    self.sourceElement.duration = self.rec_finish_time-self.rec_start_time
    
    
  def play_recorded_click(self, **event_args):  
    if self.looping or self.app_ready == False:
      pass
    else:
      if self.playing_recorded:
        self.playing_recorded = False
        self.audioElement.currentTime = 0
        self.audioElement.pause()
        # self.audio_recording.pause()
        # self.audio_recording.currentTime = 0
        self.play_recorded.font_size = 30
        self.play_recorded.foreground = "#2C3673"
        self.play_recorded.icon = "fa:play-circle"
      else:
        if self.rec_finish_time is not None and self.rec_start_time is not None:
          self.playing_recorded = True
          self.play_recorded.font_size = 60
          self.play_recorded.foreground = "#05cc2d"
          self.play_recorded.icon = "fa:square"

          self.audioElement.load()
          self.audioElement.currentTime = 0
          self.sourceElement.currentTime = 0
          self.audioElement.play()          
          time.sleep(self.sourceElement.duration)
          print("playback complete")          
          # except:
          #   print("couldn't play")
            
          if self.playing_recorded: self.play_recorded_click()

  def stopMicrophone(self):
    if self.stream:
      for track in self.stream.getTracks():
        track.stop()

  def hands_free_mode_click(self, **event_args):
    if self.app_ready == False:
      pass
    else:
      if self.looping:
        self.progress_bar.progress = 1
        self.looping = False
        try:
          self.audio_recording_example.pause()
          self.audio_recording_example.currentTime = 0
        except:
          print("nothing was playing")
        self.hands_free_mode.foreground ="#2C3673"
        self.hands_free_mode.icon = "fa:graduation-cap"
        self.hands_free_mode.font_size = 30
        try:
          self.stop_background_music()
        except:
          print("no background music playing")
        # anvil.js.call("stop_background_music")
        time.sleep(1)
        try:
          self.audio_recording_example.pause()
        except:
          pass
      else:
        self.noalert = False
        result = alert(self.myloopoptions, buttons=[], large=True) #title="Lesson mode - pick your lesson type")
        self.noalert = True
        if result == "begin":
          self.lesson_start_time = time.time()
          self.looping = True
          self.hands_free_mode.foreground ="#05cc2d"
          self.hands_free_mode.icon = "fa:square"
          self.hands_free_mode.font_size = 60
          if self.myloopoptions.music_on:
            # anvil.js.call("start_background_music")
            self.start_background_music()
          self.loop_cards()
          self.looping = True
          self.hands_free_mode_click()
      
  def loop_cards(self):
    for j in range(50):
      for i in range(9):
        if self.looping:
          if self.ccols[self.active_column] in self.myloopoptions.ok_columns and self.like_button.icon != "fa:thumbs-up":
            if self.myloopoptions.sound_on:
              if self.myloopoptions.lesson_type == "EF":
                self.play_on_screen(language="english")
                if self.looping: self.play_on_screen(language="french")
              elif self.myloopoptions.lesson_type == "EFP":
                self.play_on_screen(language="english")
                if self.looping: self.play_on_screen(language="french", pause_after_first=True)
              elif self.myloopoptions.lesson_type == "EPFP":
                self.play_on_screen(language="english", pause_after_first=True)
                if self.looping: self.play_on_screen(language="french", pause_after_first=True)
              elif self.myloopoptions.lesson_type == "FE":
                self.play_on_screen(language="french")
                if self.looping: self.play_on_screen(language="english")
              elif self.myloopoptions.lesson_type == "FPEP":
                self.play_on_screen(language="french", pause_after_first=True)
                if self.looping: self.play_on_screen(language="english", pause_after_first=True)
              elif self.myloopoptions.lesson_type == "FFP":
                self.play_on_screen(twice=True, pause_after_second=True)
            else:
              time.sleep(5)
            # time.sleep(self.myloopoptions.radiogroup)
          if (time.time() - self.lesson_start_time)/60 > int(self.myloopoptions.time_slider.value):
            self.looping = False
            break
          elif self.looping: 
            ratio_of_done = ((time.time() - self.lesson_start_time)/60) / int(self.myloopoptions.time_slider.value)
            self.progress_bar.progress = ratio_of_done
            self.swipe_left()
        else:
          break
      if self.looping:
        self.swipe_up()
      else:
        break

  def button_add_note_click(self, **event_args):
    if self.looping or self.app_ready == False:
      pass
    else:    
      if self.mymenuv.mymode[:7] == "Phrases":
        tmp0 = self.row_showing_order[self.row_showing_item]
        fr = self.usable_sentences[tmp0][self.ccols[self.active_column]]
        en = self.usable_english[tmp0][self.ccols[self.active_column]]
          
        mynotev = Note(fr=fr, en=en)
        while True:
          self.noalert = False
          result = alert(title="New note", large=True, content=mynotev, buttons=[("Cancel", "Cancel"), ("Save", "Save")])
          self.noalert = True
          if result == "Save":
            if mynotev.french_area.text == "" or mynotev.explanation_area.text == "":
              self.noalert = False
              alert("Can't save unless both fields are filled")
              self.noalert = True
            else:
              if self.mymenuv.signed_in:
                anvil.server.call('save_note',mynotev.french_area.text,mynotev.explanation_area.text)
              else:
                self.noalert = False
                alert("Sign in to use this feature!", buttons=[("Sounds good!", "Sounds good!")])
                self.noalert = True
              break
          else:
            break
      elif self.mymenuv.mymode[0:5] == "Notes":
        mynotev = Note(fr="", en="")
        if self.show_text.content != "no notes":
          tmp = self.mynotes[self.notes_showing_order[self.notes_showing_item]]
          tmpword = str(tmp["French"])
          tmpexplanation = str(tmp["Comment"])
          mynotev.french_area.text = tmpword
          mynotev.explanation_area.text = tmpexplanation
          while True:
            self.noalert = False
            result = alert(title="Edit note", content=mynotev, buttons=[("Delete","Delete"), ("Cancel", "Cancel"), ("Save", "Save")])
            self.noalert = True
            if result == "Save":
              if mynotev.french_area.text == "" or mynotev.explanation_area.text == "":
                self.noalert = False
                alert("Can't save unless both fields are filled")
                self.noalert = True
              else:
                if tmpword != mynotev.french_area.text or tmpexplanation != mynotev.explanation_area.text:
                  if self.mymenuv.signed_in:
                    result2 = anvil.server.call('update_note',tmpword, tmpexplanation, mynotev.french_area.text, mynotev.explanation_area.text)
                    if result2 == "worked":
                      self.mynotes[self.notes_showing_order[self.notes_showing_item]]["French"] = mynotev.french_area.text
                      self.mynotes[self.notes_showing_order[self.notes_showing_item]]["Comment"] = mynotev.explanation_area.text
                      self.update_notes_visual()
                  else:
                    self.noalert = False
                    alert("Sign in to use this feature!", buttons=[("Sounds good!", "Sounds good!")])
                    self.noalert = True
                break
            elif result == "Cancel":
              break
            elif result == "Delete":
              self.noalert = False
              result2 = alert("Are you sure?", buttons=[("Yes", "Yes"), ("No", "No")])
              self.noalert = True
              if result2 == "Yes":
                if self.mymenuv.signed_in:
                  anvil.server.call('delete_note', tmpword, tmpexplanation)
                  # print("needs a refresh here")
                  adjuster = self.notes_showing_order[self.notes_showing_item]
                  self.mynotes.pop(adjuster)
                  self.notes_showing_order.pop(self.notes_showing_item)
                  for i in range(len(self.notes_showing_order)):
                    if self.notes_showing_order[i] >= adjuster:
                      self.notes_showing_order[i] -= 1
                      
                  self.swipe_down()
                  break
                else:
                  self.noalert = False
                  alert("Sign in to use this feature!", buttons=[("Sounds good!", "Sounds good!")])
                  self.noalert = True
            else:
              break

  def check_button_click(self, **event_args):        
    if self.show_text.content != "no notes":
      tmp = self.mynotes[self.notes_showing_order[self.notes_showing_item]]
      # print(self.mymenuv.mymode[6:])
      if self.mymenuv.mymode[6:] == "meaning":
        savedanswer = str(tmp["French"])
        promptanswer = str(tmp["Comment"])
      elif self.mymenuv.mymode[6:] == "word":
        savedanswer = str(tmp["Comment"])
        promptanswer = str(tmp["French"])
      else:
        savedanswer = "cool"

      test_result_window = Test_result()
      test_result_window.youranswer.text = self.answer_box.text
      test_result_window.test_prompt.text = promptanswer
      test_result_window.savedanswer.text = savedanswer
      test_result_window.similarity_field.text = str(int(similarity(self.answer_box.text, savedanswer)*100)) + "%"
      self.noalert = False
      next_step = alert(test_result_window, buttons=[], large=True, dismissible=False)
      self.noalert = True

      self.answer_box.text = ""
      if next_step == "next":
        self.swipe_up()
      self.answer_box.select()

  def answer_box_pressed_enter(self, **event_args):
    self.check_button_click()

  def answer_box_show(self, **event_args):
    self.answer_box.focus()

  def form_hide(self, **event_args):
    self._setup = False
    document.removeEventListener("keydown", self.on_keydown)
    anvil.js.window.removeEventListener("focus", self.on_refocus)
    anvil.js.window.removeEventListener("blur", self.on_blur)

  def update_points(self):
    sum_points = 0
    wcl, wcs, pl, ps, brl, brs = 0, 0, 0, 0, 0, 0
    
    if self.mymenuv.signed_in:
      for col in self.ccols:
        for count, i in enumerate(self.mylikes[col]):
          if int(i) == 1:
            sum_points += 1
            if count < 50:
              wcl += 1
            elif count < 100:
              pl += 1
            elif count < 150:
              brl += 1
          elif int(i) == 2:
            sum_points += 1     
            if count < 50:
              wcs += 1
            elif count < 100:
              ps += 1
            elif count < 150:
              brs += 1         
          elif int(i) == 3:
            sum_points += 2
            if count < 50:
              wcl += 1
              wcs += 1
            elif count < 100:
              pl += 1
              ps += 1
            elif count < 150:
              brl += 1
              brs += 1

    self.myphrasemap.l_wcl.text = str(wcl) + r" / 500"
    self.myphrasemap.l_wcs.text = str(wcs) + r" / 500"
    self.myphrasemap.l_pl.text = str(pl) + r" / 500"
    self.myphrasemap.l_ps.text = str(ps) + r" / 500"
    self.myphrasemap.l_brl.text = str(brl) + r" / 500"
    self.myphrasemap.l_brs.text = str(brs) + r" / 500"


    
    self.point_count.text = "Just " + str(int(3000 - sum_points)) + " seeds to catch Parapeet !"
  
  def like_button_click(self, **event_args):
    if self.looping or self.app_ready == False:
      pass
    else:
      if self.getaccount.visible:
        self.noalert = False
        alert("Sign in to use this feature!", buttons=[("Sounds good!", "Sounds good!")])
        self.noalert = True
      else:
        tmp0 = self.row_showing_order[self.row_showing_item]
        col_to_like = self.usable_sentences[tmp0]["LineID"]
        col0 = self.mylikes[self.ccols[self.active_column]][:]
  
        if col0[col_to_like] == "0": #no like no spoken - want to like
          self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "1" + col0[col_to_like+1:]
          anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="1")
          self.like_button.icon = "fa:thumbs-up"
          self.catch_button.text = "Test yourself!"
          self.catch_button.background = "#ffffff"
        elif col0[col_to_like] == "1": #like no spoken - want to dislike
          self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "0" + col0[col_to_like+1:]
          anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="0")
          self.like_button.icon = "fa:thumbs-o-up"
          self.catch_button.text = "Test yourself!"
          self.catch_button.background = "#ffffff"
        elif col0[col_to_like] == "2": #no like spoken - want to like
          self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "3" + col0[col_to_like+1:]
          anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="3")
          self.like_button.icon = "fa:thumbs-up"
          self.catch_button.text = "You got it!"
          self.catch_button.background = "#96ff96"
        elif col0[col_to_like] == "3": #like spoken - want to dislike
          self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "2" + col0[col_to_like+1:]
          anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="2")
          self.like_button.icon = "fa:thumbs-o-up"
          self.catch_button.text = "You got it!"
          self.catch_button.background = "#96ff96"
        self.update_points()

  def phrase_spoken(self):
    if self.getaccount.visible:
      self.noalert = False
      alert("Sign in to use this feature!", buttons=[("Sounds good!", "Sounds good!")])
      self.noalert = True
      self.catch_button.text = "Test yourself!"
    else:
      tmp0 = self.row_showing_order[self.row_showing_item]
      col_to_like = self.usable_sentences[tmp0]["LineID"]
      col0 = self.mylikes[self.ccols[self.active_column]][:]
      if col0[col_to_like] == "0":
        self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "2" + col0[col_to_like+1:]
        anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="2")
        self.catch_button.text = "You got it!"
        self.catch_button.background = "#96ff96"
      elif col0[col_to_like] == "1":
        self.mylikes[self.ccols[self.active_column]] = col0[:col_to_like] + "3" + col0[col_to_like+1:]
        anvil.server.call("set_points", id=col_to_like, type=self.ccols[self.active_column], status="3")
        self.catch_button.text = "You got it!"
        self.catch_button.background = "#96ff96"
      self.update_points()
  
  def point_count_click(self, **event_args):
    self.noalert = False
    alert("""
      How to get points?

Test yourself! Click and speak the phrase out loud - pause - try again if you have to!
Get a point for that ;)


Once you are comfortable with the phrase - like it!
Get a point for that too ;)
(Liking helps you remember which phrases you already learned, and skips them in Lessons)


Can you go through all 1500 phrases and say you know them?
That's the challenge - good luck!
    """)
    self.noalert = True

  def sitimage_mouse_up(self, x, y, button, **event_args):
    self.face_click()

  def catch_button_click(self, **event_args):
    if speech_notworking:
      alert("Please use google chrome for this feature")
      
    else:
      if self.catch_button.text == "You got it!":
        pass
      elif self.catching:
        self.catching = False
        self.catch_button.text = "Test yourself!"
        self.show_text.border = ""
        self.recognition.abort()  
      else:
        self.catching = True
        tmp0 = self.row_showing_order[self.row_showing_item] #getting line_id
        tmp1 = self.usable_sentences[tmp0] #getting the row with all columns
        col0 = self.ccols[self.active_column]
        self.str_to_catch = re.sub(r'/[.,]/g', '', tmp1[col0].lower())
        self.catch_button.text = "Listening - Stop"
        self.show_text.border = "3px solid #ff2e2e"
        self.launch_recognition()

  def launch_recognition(self):
    try:
      self.recognition = webkitSpeechRecognition()
      self.transcript = ""
      self.recognition.lang = "fr-CA"
      self.recognition.continuous = True
      self.recognition.addEventListener("result", self.get_transcript)
      self.recognition.start()
    except:
      alert("voice recognition error")
      self.catch_button_click()

  def get_transcript(self, e):
    self.recognition.abort()
    self.show_text.border = ""
    self.catching = False
    # for i in e.results[0]:
    #   print(i.transcript)
    self.transcript = e.results[0][0].transcript
    self.ratio = similarity(self.str_to_catch, self.transcript)
    if self.ratio > 0.8:
      self.noalert = False
      keypressedhere = alert(random.choice(self.cong_list) + " You got it! Similarity was at " + str(int(self.ratio*100)) + "%")
      self.noalert = True
      self.recognition = None
      self.phrase_spoken()
    else:
      self.noalert = False
      alert("Not quite! Similarity was at " + str(int(self.ratio*100)) + "%, try again!")
      self.noalert = True
      self.catching = True
      self.catch_button.text = "Listening - Stop"
      self.show_text.border = "3px solid #ff2e2e"
      self.recognition.start()

  def start_background_music(self):
    self.keepplaying = True
    self.play_bga1()

  def play_bga1(self, event=False):
    if self.keepplaying:
      if self.music_1 == None:
        self.music_1 = anvil.server.call("get_music", "1")
      # self.bga1 = Audio(self.music_1)
      # self.bga1.play()
      # self.bga1.addEventListener("ended", self.play_bga2)
      self.background_music.src = self.music_1
      self.background_music.play()
      self.background_music.removeEventListener("ended", self.play_bga1)
      self.background_music.addEventListener("ended", self.play_bga2)
      
  def play_bga2(self, event=False):
    if self.keepplaying:
      if self.music_2 == None:
        self.music_2 = anvil.server.call("get_music", "2")
      # self.bga2 = Audio(self.music_2)
      # self.bga2.play()
      # self.bga2.addEventListener("ended", self.play_bga3)
      self.background_music.src = self.music_2
      self.background_music.play()
      self.background_music.removeEventListener("ended", self.play_bga2)
      self.background_music.addEventListener("ended", self.play_bga3)

  def play_bga3(self, event=False):
    if self.keepplaying:
      if self.music_3 == None:
        self.music_3 = anvil.server.call("get_music", "3")
      # self.bga3 = Audio(self.music_3)
      # self.bga3.play()
      # self.bga3.addEventListener("ended", self.play_bga1)
      self.background_music.src = self.music_3
      self.background_music.play()
      self.background_music.removeEventListener("ended", self.play_bga3)
      self.background_music.addEventListener("ended", self.play_bga1)
  
  def stop_background_music(self):
    keepplaying = False
    # if self.music_1 != None:
    #   self.bga1.pause()
    #   self.bga1.currentTime = 0
    # if self.music_2 != None:
    #   self.bga2.pause()
    #   self.bga2.currentTime = 0
    # if self.music_3 != None:
    #   self.bga3.pause()
    #   self.bga3.currentTime = 0
    self.background_music.removeEventListener("ended", self.play_bga1)
    self.background_music.removeEventListener("ended", self.play_bga2)
    self.background_music.removeEventListener("ended", self.play_bga3)
    self.background_music.pause()
    self.background_music.currentTime = 0
    self.background_music.pause()
    

  def launch_level_select_click(self, **event_args):
    if self.looping or self.app_ready == False:
      pass
    else:
      self.noalert = False
      result = alert(content=self.myphrasemap, large=True, buttons=[])
      self.noalert = True
      # print("result", result)
      if result != -1 and result != None:
        if self.mymenuv.signed_in:
          if self.selected_category_number != result:
            self.selected_category_number = result
            self.active_column = 0
            self.swipe_type = "right"
            self.launch_user_app()
        else:
          self.noalert = False
          alert("Sign in to use this feature!")
          self.noalert = True
