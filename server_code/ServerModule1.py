"""The original Parapeet server functions (2023-2025), kept so nothing that still calls them breaks, plus the Android
app link (/.well-known/assetlinks.json for the com.parapeet.twa Play Store wrapper) and account deletion.

The new app uses Phrases.py, Progress.py and Notes.py. Fixed here in Nov 2026: update_note only changes the caller's
own note; get_voice no longer crashes on a locked phrase; send_interest no longer stores visitors' IP addresses;
delete_account also removes the new progress row and copes with a missing points row.
"""
from datetime import datetime

import anvil.server
import anvil.users
from anvil.tables import app_tables


def _email():
    user = anvil.users.get_user()
    return user["email"] if user is not None else None


@anvil.server.callable(require_user=True)
def delete_account():
    """Delete the signed-in account and everything stored for it (Play Store rule: deletion inside the app)."""
    user = anvil.users.get_user()
    if user is None:
        return {"ok": False}
    email = user["email"]
    for row in app_tables.progress.search(user=user):
        row.delete()
    for row in app_tables.usernotes.search(User=email):
        row.delete()
    for row in app_tables.userpoints.search(user=email):
        row.delete()
    for row in app_tables.feedback.search(user=user):
        row["user"] = None
    anvil.users.logout()
    user.delete()
    return {"ok": True}


def assetlinks():
    return [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "android_app",
            "package_name": "com.parapeet.twa",
            "sha256_cert_fingerprints": ["E0:30:11:D4:01:D2:DF:40:93:4C:1A:1E:4A:EE:FC:58:62:79:28:8C:86:35:26:CC:87:67:40:5A:5D:DA:7F:1D"]
        }
    }]


_wellknown = getattr(anvil.server, "wellknown_endpoint", None)  # hosted Anvil has it; the local App Server may not
if _wellknown is not None:
    assetlinks = _wellknown("/assetlinks.json")(assetlinks)


@anvil.server.callable
def save_note(word, explanation):
    email = _email()
    if email is None:
        return "Sign in first"
    app_tables.usernotes.add_row(French=str(word or "")[:400], Comment=str(explanation or "")[:600], User=email)
    return "Success"


@anvil.server.callable
def delete_note(word, explanation):
    email = _email()
    if email is None:
        return "Sign in first"
    for row in app_tables.usernotes.search(French=word, Comment=explanation, User=email):
        row.delete()
        break
    return "Success"


@anvil.server.callable
def update_note(word, explanation, new_word, new_explanation):
    email = _email()
    if email is None:
        return "Sign in first"
    for row in app_tables.usernotes.search(Comment=explanation, French=word, User=email):
        row["Comment"] = str(new_explanation or "")[:600]
        row["French"] = str(new_word or "")[:400]
        return "worked"
    return "no row"


@anvil.server.callable
def get_notes():
    email = _email()
    return [dict(row) for row in app_tables.usernotes.search(User=email or "demo")]


def _customer_type():
    user = anvil.users.get_user()
    if user is None:
        return "basic"
    return user["customer_type"] or "free"


@anvil.server.callable
def update_local_storage():
    customer_type = _customer_type()
    levels = ["basic"] + (["free"] if customer_type != "basic" else []) + (["premium"] if customer_type == "premium" else [])
    out = {"user_data_type": customer_type, "user_data_date": datetime.now(), "rows": [], "rows_english": []}
    for level in levels:
        out["rows"] += [dict(r) for r in app_tables.frenchsentences.search(Availability=level)]
        out["rows_english"] += [dict(r) for r in app_tables.frenchsentences_translation.search(Availability=level)]
    return out


@anvil.server.callable
def get_music(id):
    for row in app_tables.music.search(music_id=str(id)):
        return row["Music_file"].get_url()
    return None


@anvil.server.callable
def get_video(id):
    for row in app_tables.videos.search(Video_id=str(id)):
        return row["Video_file"].get_url()
    return None


@anvil.server.callable
def get_voice(id, type, language):
    customer_type = _customer_type()
    allowed = ["basic"] + (["free"] if customer_type != "basic" else []) + (["premium"] if customer_type == "premium" else [])
    for sentence in app_tables.frenchsentences.search(LineID=id):
        if (sentence["Availability"] or "") not in allowed:
            return None
        table = app_tables.voicefiles if language == "french" else app_tables.voicefiles_english
        for media in table.search(LineID=str(id), Type=type):
            return media["VoiceFile"].get_url()
    return None


@anvil.server.callable
def send_interest(customer_interest):
    """Signed-in people are noted by email; visitors just as "guest" (no IP addresses)."""
    email = _email()
    app_tables.interest.add_row(showed_interest=email or "guest", mydatetime=datetime.now(),
                                interested=str(customer_interest or "")[:200])


@anvil.server.callable
def is_alive_check():
    return True


@anvil.server.callable
def set_points(id, type, status):
    email = _email()
    if email is None or type not in ("Basic", "Boss", "Client", "Colleague", "Lover", "Sad", "Frustrated", "Agressive",
                                       "Impressed", "Stupid") or status not in ("0", "1", "2", "3"):
        return False
    row = app_tables.userpoints.get(user=email)
    if row is None:
        return False
    digits = (row[type] or "").ljust(int(id) + 1, "0")
    row[type] = digits[:int(id)] + status + digits[int(id) + 1:]
    return True


@anvil.server.callable
def get_points():
    email = _email()
    if email is None:
        return False
    row = app_tables.userpoints.get(user=email)
    if row is None:
        zeros = "0" * 167
        row = app_tables.userpoints.add_row(user=email, Agressive=zeros, Basic=zeros, Boss=zeros, Client=zeros,
                                            Colleague=zeros, Frustrated=zeros, Impressed=zeros, Lover=zeros, Sad=zeros,
                                            Stupid=zeros)
    return dict(row)
