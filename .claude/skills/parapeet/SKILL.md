---
name: parapeet
description: Context, workflow and recipes for Parapeet (folder parapeet-forms), the user's Anvil app built as native Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels). Parapeet teaches everyday French, Spanish and Italian phrases in ten moods (boss, client, lover, hothead, sad friend, silly...) with a swipe phrasebook, Duolingo-style lessons, seeds, streaks and badges. Load this before any feature request, bug fix, restyle, content change or deploy for this app.
---

# Parapeet: working on the app

**What it is:** a language-learning game (French, Spanish, Italian since 2026-11-02) for people who already know some
of the language (about A2-B2). Every phrase in the database exists in ten moods (columns of FrenchSentences /
SpanishSentences / ItalianSentences / FrenchSentences_translation: Basic, Colleague, Client, Boss,
Agressive, Frustrated, Sad, Lover, Impressed, Stupid, shown as Neutral, Colleague, Client, Boss, Hothead, Frustrated,
Comfort, Lover, Admiring, Silly; most describe who you're talking to, see client_code/tones.py). Core loop: swipe the
phrasebook (#practice) -> play lessons on the trail (#play, #lesson/<key>) -> earn seeds, keep a streak, hit the daily
goal, collect badges -> "catch Parapeet" at 3,000 seeds (the original app's promise). Guest-first: everything but
My phrasebook (#saved) works without an account; guest progress lives in localStorage and merges into the account.
The original app (2023-2025, classic YAML forms by the user) was rebuilt as native Forms on 2026-11-02 and merged
into master the same day.

**Where it lives:**
- Folder `C:\Users\arkvi\Documents\CLAUDE\parapeet-forms\` = the git clone of **github.com/arkulinskis/parapeet**, branch
  `master` (the rebuild was developed on `forms` and merged 2026-11-02). "git" layout: the folder *is* the Anvil app. Live: https://parapeet.com (custom domain; an Android TWA `com.parapeet.twa` wraps it: keep
  ServerModule1.assetlinks + `.well-known/assetlinks.json`). The old app's folder `..\parapeet` is a plain clone, for
  reference only. The repo's GitHub default branch is the stale `dev2`; dev3/dev4/dev5 are old IDE branches.
- Made from `C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\template-forms` (native Anvil Forms, Nov 2026). Anvil's own agent
  skills describe the same model: `client-forms`, `data-models`, `server-code`, `client-modules`, `anvil-yaml`
  (github.com/anvil-works/anvil-agent-references; see APP_MAKER/ANVIL_NOTES.md, "Native Anvil Forms").
- **README.md** lists every feature. Keep it up to date.

**What the user wants:** "Jungle Arcade" (chosen 2026-11-02): Parapeet's jungle + budgie world made playful and
tactile. Leaf cream #f3fae9 / navy ink #1e2a5a / jungle green #2e9e4f (deep #1e7a3a) / budgie blue #36bfda / beak yellow
#ffc83d; dark #0d1912. Fredoka headings, Nunito body. Chunky buttons with a 4px bottom edge that presses down; a colour
and icon per mood (`--tone`, tones.TONES); the SVG mascot (Components.Bird: happy, wow, oops, sleepy, talk). No ads
(AdSense removed at the user's choice; Ads.txt kept). Duolingo was the original inspiration: gamification and the
emotional differences between moods are the point. Mobile vs desktop navigation must stay distinct (phone: thumb dock;
desktop: arrows beside the card + keys). Claude assumes details and builds; Claude deploys. Mobile-first: every page must fit 390 px. Light and dark.

## Workflow for any change

1. `git pull --ff-only` (Anvil commits "Edited ..." when the user changes something in the IDE; read those commits).
2. Edit: a page's template and Python side by side (`client_code/Pages/X/form_template.html` + `__init__.py`).
3. `python tools/check.py` (no -I) -> **ALL CHECKS PASSED**: Anvil's validator (`anvil validate`, type-checks every
   template and Python file against Anvil's API), JS syntax, asset hashes (`tools/assets.py`), server tests.
   Needs the Anvil CLI once: `npm install -g @anvil-works/anvil-cli`.
4. `python -I tools/ui_test.py` (Docker Desktop running) -> **ALL UI TESTS PASSED**: the folder runs as-is in the
   open-source Anvil App Server (container `parapeet-dev`) and headless Chrome walks tools/ui/flow.js, phone.js
   (true 390 px, no sideways scroll) and admin.js. Client edits show on reload; server edits need `--restart`.
   `--shots DIR` = screenshots of every page, desktop + phone, light + dark, guest + member: Read them.
5. Commit only your files as arkulinskis with the Co-Authored-By line; `git push origin master`.
   New tables/columns: tell the user to accept the **Schema Mismatch** alert ("The schema of the source code is correct").

## Architecture

```
anvil.yaml                 startup: module `startup`; db_schema; services; head_html (fonts, Prepsto, theme assets with ?v=)
client_code/
  startup.py               get_me, Privacy & Terms kit, router.start()
  router.py                PAGES (who may open each page), NAV (main menu), _form (page -> Form), go/href/replace
  state.py                 me(), call() (expected {"ok": False} -> toast + None), toast(), store, set_attr, dates
  auth.py                  sign in / up / reset / Continue with Google / sign out
  legal.py                 Privacy & Terms (installed from APP_MAKER/legal-kit; don't edit here)
  Layouts/Shell            header + account menu + footer + phone tab bar; slot "content"; refresh(page)
  Pages/                   Landing, Auth, Home (EXAMPLE), Profile, Admin (overview, feedback, users, demo data)
  Components/              custom components (Initials = the example); wrap any JS engine here
  Items/                   RepeatingPanel item templates: NavLink, ItemCard (EXAMPLE), FeedbackRow, UserRow
  Dialogs/                 dialog Forms for alert(): AddItem (EXAMPLE)
server_code/               common.py (C.*), Accounts, Admin, DemoData, Feedback, ExampleItems (EXAMPLE), SchemaCheck
theme/assets/              app.css (tokens + pages + the role layer), icons.css (generated), app-kit.js, theme.css
                           (loading spinner), icon.svg + PNGs (tools/make_icons.py)
tools/                     check.py, assets.py, build_icons.py, make_icons.py, ui_test.py + ui/, live/drive.mjs, testing/
```

## How things are done here

- **Page** = `client_code/Pages/X/` with `<anvil-form layout="Parapeet.Layouts.Shell"><anvil-block slot="content">`
  and `class X(XTemplate)` taking `args=()` (the URL parts after `#x/`). Register it in router.py: `PAGES`, `_form`,
  and `NAV` if it belongs in the menu (max 4). Add its address to tools/ui/phone.js and its journey to flow.js.
- **The layout is reused between pages** (open_form keeps the Shell when the layout matches): anything in the Shell
  that depends on the user or the page goes in `Shell.refresh(page)`.
- **Navigation** = plain `<a href="#page">`; in code `router.go("page", arg)`; build links with `router.href`.
- **Static copy** = plain HTML in the template. **Text that changes** = a `Label` (role for the look).
- **Actions** = Anvil `Button` + `@handle("name", "click")`, roles `["btn", "btn-primary", "ic-plus"]`. Button roles
  are aliases of `.ui-btn` in app.css: `btn-primary`, `btn-ghost`, `btn-danger` + `btn-solid`, `btn-sm`, `btn-lg`,
  `btn-icon`, `btn-block`. Icons: role `ic-<name>` on Buttons/Links, `<i class="ic ic-<name>">` in HTML
  (names in app-kit.js `UI.ICONS`; add one there and run tools/build_icons.py).
- **Inputs** = TextBox / TextArea / DropDown / CheckBox (styled by app.css through `.ui input`, `.ui textarea`).
  Read `.text` / `.selected_value` / `.checked`; `pressed_enter` for Enter.
- **Plain HTML that changes** = `anvil:name="x"`, then `self.x.visible`, `self.x.classes["on"] = ...`,
  `self.x.style[...]`; attributes with `state.set_attr(self.x, "href", ...)`. Native clicks:
  `anvil:on-dom:click="self.x_click"` + `def x_click(self, event)`.
- **Lists** = `RepeatingPanel` + an `Items/` Form; never build repeated HTML strings. Bind fields in the item template
  (`bind:text="self.item['title']"`). Grid/flex CSS goes on the panel's items container: `.anvil-role-<role> > div`.
  Item -> page: `self.parent.raise_event("x-something", ...)` + `panel.add_event_handler("x-something", ...)`.
  Role `contents` lets a panel's items join the surrounding grid.
- **Dialogs** = a Form in `Dialogs/`, `alert(Form(...), buttons=[], role="app-dialog")`; it closes itself with
  `self.raise_event("x-close-alert", value=...)`. Yes/no: `confirm(text, title=..., buttons=[("Cancel", False), ("Delete", True)])`.
- **Toasts** = `state.toast(msg, "ok" | "error")` (Anvil Notification with roles).
- **Server calls** = `state.call("fn", ...)` for normal flows (expected `{"ok": False, "error"}` -> toast, returns None);
  a page that shows a friendly state instead (not found, private) calls `anvil.server.call` and checks `ok` itself.
  Server functions: `@anvil.server.callable(require_user=True)`, `C.require_user()` / `C.require_admin()`, ownership
  checks, return plain dicts (`C.ok(...)` / `C.fail("...")`), never other people's emails. Tables are `client: none`.
- **JavaScript** only for engines Python is too slow for (canvas, SVG drawing, WebGL, audio, maps, PDF): put it in
  `theme/assets/<name>.js`, load it in head_html (then `python tools/assets.py`), wrap it in one Python module
  (`from anvil.js import window`) and/or a `Components/` custom component. Little Hero Books is the worked example.

## Recipes

- **New table or column:** `db_schema` in anvil.yaml (same shape as the existing tables, `client: none`), then add it
  to server tests. Deploy, then the Schema Mismatch step. Personal data -> the legal kit (below).
- **New server function:** in a server module + tests in tools/testing/test_server.py (happy path, bad input,
  someone not allowed; public ones in `PUBLIC`).
- **Demo content:** DemoData.py (`is_demo=True`, `DEMO_TABLES`, children first).
- **Restyle:** tokens at the top of app.css (light and dark blocks), fonts in head_html, the spinner in theme.css
  (`python -I APP_MAKER/tools/loaders.py apply parapeet <preset>`), `LEGAL_THEME` in startup.py.
- **Icon:** edit theme/assets/icon.svg, `python -I tools/make_icons.py`, then `python tools/assets.py`.

## Gotchas

- The local App Server (1.18) lags hosted Anvil: no `HtmlComponent.attrs` (use state.set_attr), `Notification(role=)`
  raises (state.toast falls back), notifications are `.anvil-alert[data-notify]`, components are wrapped in
  `<anvil-dropzone>` (app.css: `display: contents`). app.css styles both. Test on hosted Anvil too for big changes.
- Anvil's alert() without `large=True` is a 300 px modal: our role `app-dialog` widens it.
- Headless Chrome: Anvil's service worker breaks reused profiles (drive.mjs bypasses it); phone width needs device
  emulation (`MOBILE=390,844`), windows can't go below ~500 px.
- `require_secure_passwords` rejects leaked passwords: tests use random ones.
- Heredocs in the Bash tool mangle quotes: write files with the Write tool.
- Never write Anvil's theme-colour token pattern (percent, `color:`, name, percent) in theme.css.

## Parapeet's own pieces

- **Languages** (`client_code/langs.py`, shared with the server): CODES fr/es/it, names, voices (tts/asr tags), the
  formal/familiar words and endings, praise words. `state.lang()` = the language this browser learns (localStorage
  "lang"); `phrases.switch(code)` changes it (Shell.use_lang reloads the page; the landing tabs switch in place).
  **A phrase's "fr" key, the card's "fr" side, drills' `"lang": "fr"` and pp.say(..., "fr") all mean "the language
  being learned"** (historical name; renaming it was not worth the churn). pp-card.js PP.setLang / PP.LANG holds the
  language for the card engine and pp-audio.js. Server: Phrases.TABLES maps code -> (text table, voice table);
  `Phrases.table(code)` is None until the table exists (before the Schema Mismatch is accepted), and everything
  Spanish/Italian degrades to "no phrases" instead of failing. Progress keys: gamerules.ckey / lkey (French unchanged
  "12:Boss" / "u1-1"; others "es:12:Boss" / "es:u1-1"); record_lesson / mark_card take `lang` last. UserNotes.Lang
  (empty = French; Notes._lang reads it safely). Content: Admin -> Phrases CSV download/upload (PhraseFiles.py);
  DemoData.ensure_languages seeds the samples (only onto matching French). Adding a language = an entry in LANGS,
  a table pair in Phrases.TABLES + anvil.yaml, listen hints / mood names in tones.py, the landing DEMO lines,
  PhraseFiles.UPLOAD, NoteEdit/Saved placeholders.

- **Moods**: `client_code/tones.py` (labels, colours, icons, who/blurb/listen-for texts, `register()` tu/vous). The
  database column names never change (keep "Agressive"/"Stupid"); only the labels do.
- **Game rules**: `client_code/gamerules.py`, plain Python imported by the browser (guests) AND the server
  (Progress.py: `from . import gamerules`). Seeds: 2 first try, 1 second try, 5 per lesson, 5 perfect, 3 said out loud,
  1 Got it, 10 daily-goal bonus. Streak follows the learner's local date (game.today()); the server accepts it within
  2 days of its own. Mastery key `"<LineID>:<mood>"` -> {s 0-5, d day, k known, kp known-seed paid, v said}.
  tools/testing/test_server.py copies tones.py + gamerules.py next to the server modules.
- **Lessons**: `client_code/drills.py` builds them (meaning, mood, build, listen, switch, say); `phrases.lessons()` makes
  the trail (5 phrases per lesson, `u<unit>-<n>`, `u<unit>-mix` challenge, locked `u<unit>-signup<n>` /
  `-premium<n>`); `#lesson/review` = weak spots (gamerules.due). Lesson publishes `window.PP_EX` for the UI test.
- **Engines (JS)**: `theme/assets/pp-card.js` (PP.Card: drag/axis lock/fling threshold, flip, chips, dots, keys, word
  diff) wrapped by Components.PhraseCard; `pp-audio.js` (PP.say with mood prosody, PP.play, PP.rec, PP.listen speech
  recognition fr-CA, PP.similarity, sfx, confetti, wake lock, music). Python face: `client_code/pp.py`. JS returning a
  Promise blocks Python (Anvil awaits it); `pp.fire(name, args, done)` starts one without waiting.
  Tests: `window.PP_TEST = {silent: true, heard: "text"}`.
- **Data**: Phrases.py (get_phrases by access level + locked counts, voice_url from VoiceFiles/VoiceFiles_english,
  LineID stored as text there), Progress.py (one `progress` row per user; imports old UserPoints digits once),
  Notes.py (UserNotes by owner email), Admin.py (+ admin_content, ask_for_more -> Interest table), ServerModule1.py
  (the original callables, kept and fixed). DemoData.py only fills an EMPTY phrase library (local tests) from
  sample_phrases.py: 10 real "basic" rows from parapeet.com + 3 member-only test rows (201-203) written for tests.
- **Content lives in the live database**, not the repo (about 150 phrases x 10 moods x FR/EN + recorded voices;
  Spanish / Italian start with the 13 sample phrases until the rest is uploaded). Edit it in the Anvil data tables,
  or round-trip it as CSV on Admin -> Phrases. Known typos there: some English rows start "understand..." / "hope..." (missing "I").

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit`: change `apps/parapeet.json`, then there
`python -I build.py parapeet && python -I install.py parapeet` (writes theme/assets/legal-kit.js,
client_code/legal.py, server_code/legal_server.py and the head_html tag), then `python tools/assets.py` and deploy.
Sign-up keeps the tick box (`legal.consent_field()` in Pages/Auth). Feedback = Prepsto only ("Submit feedback").
- Item templates: a named element (`anvil:name`) can't be the template's ROOT element (the validator can't see it):
  wrap the root in `<div class="ix ...">` (done in every Items/ form here).
- Fixed-position elements (lesson Check bar, phone dock) have no offsetParent: tests use getBoundingClientRect.
- Old Interest rows have dates without a time zone: compare them via C.iso().
- Client and server modules share ONE Python package: a server module can't have the same name as a client
  package or module (server `Items.py` + client `Items/` = "Cannot resolve imported module"). The template's example
  server module is `ExampleItems.py` for that reason.
