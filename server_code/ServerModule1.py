# import anvil.stripe
# import anvil.google.auth, anvil.google.drive, anvil.google.mail
# from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
# import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime, timezone, timedelta

@anvil.server.wellknown_endpoint("/assetlinks.json")
def assetlinks():
  return [{
      "relation": ["delegate_permission/common.handle_all_urls"],
      "target": {
        "namespace": "android_app",
        "package_name": "com.parapeet.twa",
        "sha256_cert_fingerprints": ["CE:81:49:7F:AE:F1:EA:9B:E5:E4:03:E8:48:3C:C8:D1:62:06:43:FC:E3:62:08:1D:AC:80:3A:26:86:38:6D:6E"]
      }
    }]


@anvil.server.callable
def save_note(word, explanation):
  if anvil.users.get_user() is not None:
    user = anvil.users.get_user()['email']
    app_tables.usernotes.add_row(French=word,Comment=explanation, User=user)
    return "Success"
  else:
    return "Sign in first"
    
  
@anvil.server.callable
def delete_note(word, explanation):
  if anvil.users.get_user() is not None:
    user = anvil.users.get_user()['email']
    row = app_tables.usernotes.get(French=word,Comment=explanation, User=user)
    row.delete()
    return "Success"
  else:
    return "Sign in first"
  

@anvil.server.callable
def update_note(word, explanation, new_word, new_explanation):
  # check that the article given is really a row in the ‘articles’ table
  if anvil.users.get_user() is not None:
    row = app_tables.usernotes.get(Comment=explanation, French=word)
    if row:
      row['Comment']=new_explanation
      row['French']=new_word
      return "worked"
    else:
      return "no row"
  else:
    return "Sign in first"

@anvil.server.callable
def get_notes():
  user = anvil.users.get_user()
  if user is not None:
    mylist = app_tables.usernotes.search(User=user['email'])
  else:
    mylist = app_tables.usernotes.search(User='demo')
  returnlist = []
  for row in mylist:
    returnlist.append(dict(row))
  return returnlist

@anvil.server.callable
def update_local_storage(user_data_date,user_data_type):
  user = anvil.users.get_user()
  print("logged in user is", user)
  if user is not None:
    customer_type = app_tables.users.get(email=user['email'])['customer_type']
    if customer_type == "" or customer_type == None or customer_type is None:
      customer_type = "free"
    recently_upgraded = False
    print("bg", user_data_type, customer_type)
    if user_data_type == "free" and customer_type == "premium": recently_upgraded = True
    mydate = datetime(2023,7,28,0,0,0,tzinfo=timezone(timedelta(0, -14400)))
    print(mydate)
    print(user_data_date)
    if user_data_date < mydate or (user_data_type != "premium" and user_data_type != "free"):
      print(customer_type)
      return_json = {}
      return_json['user_data_type'] = customer_type
      return_json['user_data_date'] = datetime.now()
      return_json['rows'] = []
      return_json['rows_english'] = []
      allowed_rows = app_tables.frenchsentences.search(Availability=customer_type)
      for row in allowed_rows:
        return_json['rows'].append(dict(row))
      if customer_type == "premium":
        allowed_rows3 = app_tables.frenchsentences.search(Availability=customer_type)
        for row in allowed_rows3:
          return_json['rows'].append(dict(row))
      allowed_rows2 = app_tables.frenchsentences.search(Availability="basic")
      for row in allowed_rows2:
        return_json['rows'].append(dict(row))

      allowed_rows_english = app_tables.frenchsentences_translation.search(Availability=customer_type)
      for row in allowed_rows_english:
        return_json['rows_english'].append(dict(row))
      if customer_type == "premium":
        allowed_rows_english3 = app_tables.frenchsentences_translation.search(Availability=customer_type)
        for row in allowed_rows_english3:
          return_json['rows_english'].append(dict(row))
      allowed_rows_english2 = app_tables.frenchsentences_translation.search(Availability="basic")
      for row in allowed_rows_english2:
        return_json['rows_english'].append(dict(row))
        
      print("Call made")
      return return_json
        
    else:
      return("yougood")
      
  else:
    allowed_rows = app_tables.frenchsentences.search(Availability="basic")
    allowed_rows_english = app_tables.frenchsentences_translation.search(Availability="basic")
    return_json = {}
    return_json['user_data_type'] = "basic"
    return_json['user_data_date'] = datetime.now()
    return_json['rows'] = []
    return_json['rows_english'] = []
    for row in allowed_rows:
      return_json['rows'].append(dict(row))
    for row in allowed_rows_english:
      return_json['rows_english'].append(dict(row))

    print("Call made")
    return return_json
    
@anvil.server.callable
def get_music(id):
  music_db_line = app_tables.music.get(music_id=str(id))
  return music_db_line["Music_file"].get_url()
  
@anvil.server.callable
def get_video(id):
  video_db_line = app_tables.videos.get(Video_id=str(id))
  return video_db_line["Video_file"].get_url()
  
@anvil.server.callable
def get_voice(id, type, language):
  user = anvil.users.get_user()
  sentence_db_line = app_tables.frenchsentences.get(LineID=id)
  play_it = False
  if sentence_db_line["Availability"] == "basic":
    play_it = True
  elif sentence_db_line["Availability"] == "free":
    if user is not None:
      play_it = True
  elif sentence_db_line["Availability"] == "premium":
    if user is not None:
      if user["customer_type"] == "premium":
        play_it = True

  if play_it:
    if language == "french":
      media_db_line = app_tables.voicefiles.get(LineID=str(id), Type=type)
    else:
      media_db_line = app_tables.voicefiles_english.get(LineID=str(id), Type=type)

  return media_db_line["VoiceFile"].get_url()

@anvil.server.callable
def send_interest(customer_interest):
  user = anvil.users.get_user()
  if user is not None:
    text = user['email']
  else:
    text = str(anvil.server.context.client.ip)
  app_tables.interest.add_row(showed_interest=text, mydatetime=datetime.now(), interested=customer_interest)

@anvil.server.callable
def is_alive_check():
  return True

@anvil.server.callable
def set_points(id, type, status):
  # print("got the request")
  user = anvil.users.get_user()
  # print(user)
  if user is None:
    return False
  else:
    useremail = user['email']
    # print("user exists")
    points_db_line = app_tables.userpoints.get(user=useremail)
    # print(points_db_line)
    a = points_db_line[type]
    # print("k", a)
    points_db_line[type] = a[:id] + status + a[id+1:]
    

#add handling if user is new (create the zeros))

@anvil.server.callable
def get_points():
  user = anvil.users.get_user()
  if user is None:
    return False
  else:
    useremail = user['email']
    points_db_line = app_tables.userpoints.get(user=useremail)
    if points_db_line == None:
      zeros = "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
      app_tables.userpoints.add_row(user=useremail, Agressive=zeros, Basic=zeros, Boss=zeros, Client=zeros, Colleague=zeros, Frustrated=zeros, Impressed=zeros, Lover=zeros, Sad=zeros, Stupid=zeros)
      points_db_line = app_tables.userpoints.get(user=useremail)
    return dict(points_db_line)