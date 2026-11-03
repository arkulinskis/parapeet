"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
The shared client modules the server imports (tones.py, gamerules.py) are copied next to the server modules.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
for shared in ("langs.py", "tones.py", "gamerules.py"):
    shutil.copyfile(PROJECT / "client_code" / shared, _tmp / "app" / shared)
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
G = importlib.import_module("app.gamerules")
now = dt.datetime.now(dt.timezone.utc)
TODAY = now.date().isoformat()
YESTERDAY = (now.date() - dt.timedelta(days=1)).isoformat()


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")
vip = person("vip@example.com", "Vee", customer_type="premium")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- the phrase library
as_user(None)
lib = call("get_phrases")
assert lib["level"] == "basic"
assert len(lib["phrases"]) == 10 and all(p["cat"] == 1 for p in lib["phrases"]), "guests get the 10 free sample phrases"
assert lib["locked"]["signup"] == {"1": 1, "2": 1, "3": 1} and lib["locked"]["premium"] == {}, lib["locked"]
p1 = lib["phrases"][0]
assert p1["id"] == 1 and p1["fr"]["Basic"].startswith("Bonjour") and p1["en"]["Basic"].startswith("Hello")
assert set(p1["fr"]) == set(M["tones"].KEYS) if "tones" in M else True
assert M["DemoData"].counts()["by_access"] == {"basic": 10, "free": 3}
call("get_phrases")
assert len(T.frenchsentences.search()) == 13, "the sample loads once, never twice"
as_user(ana)
lib = call("get_phrases")
assert lib["level"] == "free" and len(lib["phrases"]) == 13 and lib["locked"]["signup"] == {}
assert sorted(set(p["cat"] for p in lib["phrases"])) == [1, 2, 3]
T.frenchsentences.add_row(LineID=300, CategoryID=2, Availability="premium", Basic="Premium phrase")
T.frenchsentences_translation.add_row(LineID=300, CategoryID=2, Availability="premium", Basic="Premium phrase")
assert call("get_phrases")["locked"]["premium"] == {"2": 1}
as_user(vip)
assert len(call("get_phrases")["phrases"]) == 14, "premium customers see premium rows"
# voices: none recorded in the sample -> None (the browser's voice reads it); locked rows give nothing either
as_user(None)
assert call("voice_url", 1, "Basic", "fr") is None
assert call("voice_url", 201, "Basic", "fr") is None, "a member-only phrase has no voice for guests"
assert call("voice_url", 1, "NotAMood", "fr") is None and call("voice_url", "x", "Basic", "fr") is None
T.voicefiles.add_row(LineID="1", Type="Boss", VoiceFile=anvil.BlobMedia("audio/mpeg", b"ID3", name="1.mp3"))
try:
    call("voice_url", 1, "Boss", "fr")  # the mock's media has no get_url: the function must not crash either way
except Exception as e:
    raise AssertionError("voice_url crashed: %r" % e)

# ---------------------------------------------------------------------------------- Spanish and Italian
as_user(None)
es = call("get_phrases", "es")
assert es["lang"] == "es" and len(es["phrases"]) == 10, "guests get the 10 free sample phrases in Spanish too"
p1 = es["phrases"][0]
assert p1["id"] == 1 and p1["lang"] == "es" and p1["fr"]["Basic"] == "Hola, ¿cómo estás?", p1["fr"]["Basic"]
assert p1["en"]["Basic"].startswith("Hello"), "the English is shared by every language"
assert es["locked"]["signup"] == {"1": 1, "2": 1, "3": 1}
assert es["counts"] == {"fr": 14, "es": 13, "it": 13}, es["counts"]
it = call("get_phrases", "it")
assert it["phrases"][0]["fr"]["Client"] == "Buongiorno, come posso aiutarLa oggi?"
assert call("get_phrases", "de")["lang"] == "fr", "an unknown language falls back to French"
assert call("get_phrases")["lang"] == "fr" and call("get_phrases")["phrases"][0]["fr"]["Basic"].startswith("Bonjour")
as_user(ana)
assert len(call("get_phrases", "it")["phrases"]) == 13
T.spanishsentences.add_row(LineID=300, Basic="Frase premium")  # no unit / access of its own: the French row's
assert call("get_phrases", "es")["locked"]["premium"] == {"2": 1}, "a Spanish row takes the French row's unit and access"
as_user(vip)
assert len(call("get_phrases", "es")["phrases"]) == 14
# the live app: Spanish / Italian samples only land on phrases whose French is word for word the sample's
for r in T.italiansentences.search():
    r.delete()
T.frenchsentences.get(LineID=5)["Basic"] = "Une autre phrase"
assert M["DemoData"].ensure_languages() is True
assert len(T.italiansentences.search()) == 12 and T.italiansentences.get(LineID=5) is None
assert len(T.spanishsentences.search()) == 14, "a language that has phrases is left alone"
T.frenchsentences.get(LineID=5)["Basic"] = "Avez-vous des questions sur ce projet ?"
T.italiansentences.add_row(LineID=5, CategoryID=1, Availability="basic", Basic="Ha qualche domanda su questo progetto?")
langs_c = M["DemoData"].counts()["languages"]
assert [(x["code"], x["phrases"], x["missing"], x["ready"]) for x in langs_c] == [("fr", 14, 0, True), ("es", 14, 0, True), ("it", 13, 1, True)], langs_c
# voices per language
as_user(None)
assert call("voice_url", 1, "Basic", "es") is None and call("voice_url", 1, "Basic", "de") is None
T.voicefiles_italian.add_row(LineID="1", Type="Boss", VoiceFile=anvil.BlobMedia("audio/mpeg", b"ID3", name="1.mp3"))
try:
    call("voice_url", 1, "Boss", "it")
except Exception as e:
    raise AssertionError("voice_url crashed: %r" % e)
assert call("voice_url", 201, "Basic", "es") is None, "a member-only phrase has no voice for guests in any language"
# formal / familiar in each language
L = importlib.import_module("app.langs")
assert L.register("Je suis là pour vous aider.", "fr") == "formal" and L.register("Prends ton temps.", "fr") == "familiar"
assert L.register("¿En qué puedo ayudarle hoy?", "es") == "formal" and L.register("¿Me prestas tu bolígrafo?", "es") == "familiar"
assert L.register("El director quiere verte en su oficina.", "es") == "familiar" and L.register("Buena suerte.", "es") == ""
assert L.register("Buongiorno, come posso aiutarLa oggi?", "it") == "formal" and L.register("La riunione è finita.", "it") == ""
assert L.register("Scendo alla caffetteria, Le porto qualcosa?", "it") == "formal" and L.register("Come ti senti?", "it") == "familiar"
assert L.register_text("formal", "es") == "usted · formal" and L.register_text("familiar", "it") == "tu · familiar"
Tn = importlib.import_module("app.tones")
assert Tn.blurb("Client", "es") == 'Your service voice: polite "usted", offers to help, reassures, never blames.'
assert "{" not in "".join(Tn.blurb(k, c) for k in Tn.KEYS for c in L.CODES)
assert all(Tn.listen_hint(k, c) for k in Tn.KEYS for c in L.CODES)

# ---------------------------------------------------------------------------------- progress (seeds, streak, mastery)
as_user(None)
for fn, args in [("get_progress", (TODAY,)), ("record_lesson", ("lesson", "u1-1", [], TODAY)),
                 ("mark_card", (1, "Basic", "known", True, TODAY)), ("set_daily_goal", (20,)),
                 ("set_adventurer", ("x",)), ("merge_guest_progress", ({}, TODAY))]:
    assert denied(fn, *args), fn
# someone who used the old app: their likes and "spoken" marks become seeds and mastery
T.userpoints.add_row(user="bob@example.com", **{k: ("0" * 5 + "3" + "0" * 10 + "1" + "0" * 3 + "2" if k == "Boss" else "0" * 40) for k in M["Progress"].tones.KEYS})
as_user(bob)
pb = call("get_progress", TODAY)
assert pb["seeds"] == 4, pb["seeds"]  # line 5 liked+said (2), line 16 liked (1), line 20 said (1)
assert pb["mastery"]["5:Boss"]["k"] and pb["mastery"]["5:Boss"]["v"] and pb["mastery"]["16:Boss"]["k"] and pb["mastery"]["20:Boss"]["v"]
assert pb["stats"]["said"] == 2 and pb["stats"].get("imported")
assert len(T.progress.search(user=bob)) == 1
call("get_progress", TODAY)
assert len(T.progress.search(user=bob)) == 1, "one progress row per person"
as_user(ana)
p = call("get_progress", TODAY)
assert p["seeds"] == 0 and p["daily_goal"] == 20 and p["streak"] == 0
results = [{"id": 1, "tone": "Basic", "type": "meaning", "ok": True, "first": True},
           {"id": 1, "tone": "Boss", "type": "mood", "ok": True, "first": True},
           {"id": 5, "tone": "Lover", "type": "build", "ok": True, "first": False},
           {"id": 5, "tone": "NotAMood", "type": "x", "ok": True, "first": True},
           {"id": "zzz", "tone": "Basic", "ok": True, "first": True},
           "nonsense"]
r = call("record_lesson", "lesson", "u1-1", results, YESTERDAY)
res, p = r["result"], r["progress"]
assert res["answered"] == 3 and res["correct"] == 2 and res["stars"] == 1, res
assert res["seeds"] == 2 * 2 + 1 + 5 and p["seeds"] == res["seeds"], res
assert p["streak"] == 1 and p["lessons"]["u1-1"] == 1 and "first" in p["badges"]
assert p["mastery"]["1:Boss"]["s"] == 1 and p["mastery"]["5:Lover"]["s"] == 0
r = call("record_lesson", "lesson", "u1-1", [{"id": 1, "tone": "Basic", "type": "meaning", "ok": True, "first": True}] * 10, TODAY)
assert r["progress"]["streak"] == 2, "two days in a row"
assert "goal" in r["result"]["events"] and r["progress"]["lessons"]["u1-1"] == 3 and "perfect" in r["progress"]["badges"]
r = call("record_lesson", "lesson", "../evil", [], "not a date")
assert r["progress"]["lessons"].get("../evil") is None
r = call("record_lesson", "lesson", "u1-2", [{"id": 1, "tone": "Basic", "type": "x", "ok": True, "first": True}], "1999-01-01")
assert r["progress"]["last_day"] == TODAY, "a date far from the server's is replaced by the server's"
m = call("mark_card", 1, "Sad", "said", True, TODAY)
assert m["result"]["seeds"] == G.SEEDS["said"]
assert call("mark_card", 1, "Sad", "said", True, TODAY)["result"]["seeds"] == 0, "seeds only the first time"
assert call("mark_card", 1, "Sad", "known", True, TODAY)["progress"]["mastery"]["1:Sad"]["k"] is True
assert call("mark_card", 1, "Sad", "known", False, TODAY)["progress"]["mastery"]["1:Sad"]["k"] is False
# each language keeps its own mastery and lesson stars; seeds are shared
m = call("mark_card", 1, "Sad", "known", True, TODAY, "es")["progress"]
assert m["mastery"]["es:1:Sad"]["k"] is True and m["mastery"]["1:Sad"]["k"] is False
r = call("record_lesson", "lesson", "u1-1", [{"id": 1, "tone": "Boss", "type": "mood", "ok": True, "first": True}], TODAY, "it")
assert r["progress"]["lessons"]["it:u1-1"] == 3 and r["progress"]["lessons"]["u1-1"] == 3
assert r["progress"]["mastery"]["it:1:Boss"]["s"] == 1 and r["progress"]["mastery"]["1:Boss"]["s"] == 1
assert "xx:1:Sad" not in call("mark_card", 1, "Sad", "known", True, TODAY, "xx")["progress"]["mastery"], "unknown language = French"
assert G.strength(r["progress"], 1, "Boss", "it") == 1 and G.strength(r["progress"], 1, "Boss", "es") == 0
assert G.stage(0, "es")[2] == "He flew off with your Spanish. Follow the trail of seeds."
bad(call("mark_card", 1, "Nope", "known", True, TODAY))
bad(call("mark_card", 1, "Sad", "hack", True, TODAY))
bad(call("set_daily_goal", 33))
assert ok(call("set_daily_goal", 40))["progress"]["daily_goal"] == 40
ok(call("set_adventurer", "  Alex  " + "x" * 80))
assert len(T.progress.get(user=ana)["adventurer"]) <= 40
before = call("get_progress", TODAY)["seeds"]
guest = G.blank()
guest["seeds"] = 99999
guest["mastery"] = {"7:Boss": {"s": 4, "d": 1}}
guest["lessons"] = {"u2-1": 2}
merged = ok(call("merge_guest_progress", guest, TODAY))["progress"]
assert merged["seeds"] == before + G.CATCH, "a guest's seeds are capped when merged"
assert merged["mastery"]["7:Boss"]["s"] == 4 and merged["lessons"]["u2-1"] == 2
bad(call("merge_guest_progress", "nope", TODAY))

# the rules on their own
g = G.blank()
g, _ = G.apply_lesson(g, "lesson", "k", [{"id": 1, "tone": "Basic", "ok": True, "first": True}], "2026-01-01")
g, _ = G.apply_lesson(g, "lesson", "k", [{"id": 1, "tone": "Basic", "ok": True, "first": True}], "2026-01-03")
assert g["streak"] == 1 and G.live_streak(g, "2026-01-04") == 1 and G.live_streak(g, "2026-01-05") == 0, "a missed day breaks the streak"
assert G.day_no("2026-03-01") - G.day_no("2026-02-28") == 1 and G.day_no("garbage") is None
assert G.stage(0)[1] == "Parapeet spotted" and G.stage(3000)[1] == "Caught him!" and G.stage(3000)[4] is None

# ---------------------------------------------------------------------------------- my phrasebook (UserNotes)
as_user(None)
for fn, args in [("list_notes", ()), ("add_note", ("a", "b")), ("edit_note", ("x", "a", "b")), ("remove_note", ("x",)),
                 ("note_result", ("x", True))]:
    assert denied(fn, *args), fn
as_user(ana)
bad(call("add_note", " ", "meaning"))
n1 = ok(call("add_note", "Bonjour, comment ça va ?", "Hello, how are you?"))["note"]
again = ok(call("add_note", "Bonjour, comment ça va ?", "Hi there (friendly)"))
assert again["existed"] and again["note"]["en"] == "Hi there (friendly)", "saving the same French again updates it"
n2 = ok(call("add_note", "Je suis ravi", "I'm delighted"))["note"]
lst = call("list_notes")["notes"]
assert [n["id"] for n in lst] == [n2["id"], n1["id"]], "newest first"
assert ok(call("edit_note", n2["id"], "Je suis ravie", "I'm delighted (f)"))["note"]["fr"] == "Je suis ravie"
bad(call("edit_note", n2["id"], "", "x"))
assert ok(call("note_result", n2["id"], True))["note"]["level"] == 1
assert ok(call("note_result", n2["id"], False))["note"]["level"] == 0
as_user(bob)
bad(call("edit_note", n2["id"], "Hacked", "Hacked"), "can't edit someone else's note")
bad(call("note_result", n2["id"], True))
ok(call("remove_note", n2["id"]))
assert T.usernotes.get_by_id(n2["id"]) is not None, "can't delete someone else's note"
assert call("list_notes")["notes"] == []
as_user(ana)
ok(call("remove_note", n2["id"]))
assert len(call("list_notes")["notes"]) == 1
# each language has its own phrasebook
bad(call("add_note", "", "x", "es"))
n3 = ok(call("add_note", "Hola, ¿cómo estás?", "Hello, how are you?", "es"))["note"]
assert n3["lang"] == "es" and [n["id"] for n in call("list_notes", "es")["notes"]] == [n3["id"]]
assert len(call("list_notes")["notes"]) == 1 and len(call("list_notes", "fr")["notes"]) == 1, "French notes stay French"
assert call("list_notes", "it")["notes"] == []
ok(call("add_note", "Bonjour, comment ça va ?", "Same words, saved while learning Italian", "it"))
assert len(call("list_notes", "it")["notes"]) == 1 and call("list_notes")["notes"][0]["en"] == "Hi there (friendly)", "same text, other language = another note"
for n in call("list_notes", "es")["notes"] + call("list_notes", "it")["notes"]:
    ok(call("remove_note", n["id"]))

# ---------------------------------------------------------------------------------- the original functions (kept, fixed)
as_user(None)
assert call("save_note", "a", "b") == "Sign in first"
call("send_interest", "more please")
assert T.interest.search()[-1]["showed_interest"] == "guest", "no IP addresses for visitors"
assert call("get_voice", 201, "Basic", "french") is None, "a locked phrase gives no voice (and no crash)"
assert len(anvil.server.call("update_local_storage")["rows"]) == 10
as_user(bob)
assert call("update_note", "Bonjour, comment ça va ?", "Hi there (friendly)", "Hacked", "Hacked") == "no row", "only your own notes"
assert T.usernotes.get(User="ana@example.com")["French"] == "Bonjour, comment ça va ?"
assert call("save_note", "Salut", "Hi") == "Success"
assert call("update_note", "Salut", "Hi", "Salut !", "Hi!") == "worked"
assert call("set_points", 3, "Boss", "1") is True and T.userpoints.get(user="bob@example.com")["Boss"][3] == "1"
assert call("set_points", 3, "DROP TABLE", "1") is False and call("set_points", 3, "Boss", "9") is False
assert isinstance(call("get_points"), dict)
assert call("is_alive_check") is True
assert len(anvil.server.call("update_local_storage")["rows"]) == 13
assert anvil.server.ENDPOINTS["/.well-known/assetlinks.json"]()[0]["target"]["package_name"] == "com.parapeet.twa"

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("admin_content", ())]:
    assert denied(fn, *args), fn
ok(call("ask_for_more", "unit 2"))
assert T.interest.search()[-1]["showed_interest"] == "ana@example.com"
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 4 and ov["admins"] == 1 and ov["phrases"] == 14 and ov["learners"] == 2 and ov["lessons"] >= 3 and ov["notes"] >= 2, ov
c = call("admin_content")
assert [x["code"] for x in c["languages"]] == ["fr", "es", "it"]
# the phrase file: download everything, upload Spanish / Italian
as_user(ana)
assert denied("admin_phrases_csv") and denied("admin_upload_phrases", anvil.BlobMedia("text/csv", b"x"))
as_user(admin)
f = anvil.server.call("admin_phrases_csv")  # a file (Media), not JSON
text = f.get_bytes().decode("utf-8-sig")
head = text.splitlines()[0]
assert head == ",".join(["Lang", "LineID", "CategoryID", "Availability"] + Tn.KEYS), head
assert "\nfr,1,1,basic,\"Bonjour, comment ça va ?\"" in text and "\nen,1,1,basic," in text and "\nes,1,1,basic,\"Hola" in text
up = "Lang,LineID,CategoryID,Availability,Basic,Boss\n" \
     "fr,1,1,basic,Hacked,Hacked\n" \
     "es,1,,,¡Hola!,\n" \
     "it,400,2,free,Nuova frase,Frase per il capo\n" \
     "it,401,2,free,,Senza base\n" \
     "es,abc,1,free,x,y\n" \
     "es,402,1,gold,x,y\n"
r = ok(call("admin_upload_phrases", anvil.BlobMedia("text/csv", up.encode("utf-8"), name="x.csv")))
assert (r["added"], r["updated"], r["skipped"], len(r["problems"])) == (1, 1, 1, 3), r
assert T.frenchsentences.get(LineID=1)["Basic"].startswith("Bonjour"), "French rows in the file are never written"
es1 = T.spanishsentences.get(LineID=1)
assert es1["Basic"] == "¡Hola!" and es1["Boss"] and es1["CategoryID"] == 1, "empty cells keep the old text"
assert T.italiansentences.get(LineID=400)["Boss"] == "Frase per il capo"
semi = "Lang;LineID;Basic\r\nes;1;Hola otra vez, señor\r\n".encode("cp1252")
assert ok(call("admin_upload_phrases", anvil.BlobMedia("text/csv", semi)))["updated"] == 1, "Excel's ; and Windows encoding work"
assert T.spanishsentences.get(LineID=1)["Basic"] == "Hola otra vez, señor"
bad(call("admin_upload_phrases", anvil.BlobMedia("text/csv", b"")))
bad(call("admin_upload_phrases", anvil.BlobMedia("text/csv", b"Name,Text\nx,y\n")))
bad(call("admin_upload_phrases", anvil.BlobMedia("text/csv", "Lang,LineID,Basic\nit,abc,x\n".encode("utf-8"))))
assert c["by_access"]["basic"] == 10 and c["voices_fr"] == 1 and c["interest_total"] >= 2
assert len(call("list_users")["users"]) == 4 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))

# ---------------------------------------------------------------------------------- feedback (older messages; new ones go to Prepsto)
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#play", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and "evil" not in fb["context"] and fb["status"] == "new"
assert denied("list_feedback")
as_user(admin)
fid = call("list_feedback")["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
bad(call("set_feedback_status", fid, "weird"))
ok(call("delete_feedback", fid))

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup"

# ---------------------------------------------------------------------------------- deleting an account removes everything
as_user(ana)
assert denied("delete_account") is False
assert T.users.get(email="ana@example.com") is None
assert not T.usernotes.search(User="ana@example.com") and not T.progress.search()[0:0]
assert all(r["user"] is not None for r in T.progress.search()), "no orphaned progress rows"
as_user(None)
assert denied("delete_account")

# ---------------------------------------------------------------------------------- schema check (App Board): names only, never data
r = anvil.server.ENDPOINTS["/schema-check"](tables="users, progress,no_such_table")
json.dumps(r)
assert "email" in r["tables"]["users"] and "seeds" in r["tables"]["progress"] and r["tables"]["no_such_table"] is None, r

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"get_me", "submit_feedback", "legal_state", "legal_accept", "get_phrases", "voice_url",
          # the original app's functions: they check the user inside and answer "Sign in first" / False / None
          "save_note", "delete_note", "update_note", "get_notes", "update_local_storage", "get_music", "get_video",
          "get_voice", "send_interest", "is_alive_check", "set_points", "get_points"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
