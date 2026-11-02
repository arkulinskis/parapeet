# Parapeet

French phrases in ten moods. Each phrase comes in ten versions, one per situation: neutral, to a colleague, a client,
your boss, someone angry ("Hothead"), a tense moment ("Frustrated"), someone sad ("Comfort"), your partner ("Lover"),
someone you admire ("Admiring") and just for a laugh ("Silly"). Learners swipe through the moods, play short
Duolingo-style lessons, earn seeds and keep a streak, all to catch Parapeet, the parakeet who stole their French.
For people who already know some French and want to sound natural, polite or warm. Built on [Anvil](https://anvil.works)
as native Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels).

- **App repo:** github.com/arkulinskis/parapeet. The native-Forms rebuild lives on branch `forms` until it is approved;
  `master` still holds the original 2023-2025 app.
- **Live:** https://parapeet.com (the original app until `forms` is merged). An Android app (Play Store, TWA
  `com.parapeet.twa`) wraps the site.

## What it does

**Phrasebook (`#practice`, anyone)**
- A swipe card: drag sideways for the next or previous mood, up for the next phrase, down to go back, tap to flip to the
  English. The card follows the finger, tilts, shows which mood is coming, and flies off.
- Colour-coded mood chips above the card and dots below it; the words a mood adds to the neutral sentence are
  highlighted; every card says whether it uses "vous" (formal) or "tu" (familiar).
- Computer: big mood arrows beside the card, Previous / Next phrase under it, and keys (arrows, Space flips, Enter
  listens). Phone: a thumb dock at the bottom (previous phrase, previous mood, next mood, Next phrase).
- Tools: Listen (recorded voice when the database has one, otherwise the browser's voice with a pace and pitch per
  mood), Say it (speech check, 3 seeds), Got it (1 seed), Save to my phrasebook, Record me + My voice (stays in the
  browser), All moods (the ten versions side by side, listen to each, jump to one), Hands-free lesson (rhythms such as
  English / pause / French / pause, chosen moods, 5 to 30 minutes, keeps the screen awake, optional soft music from the
  app's Music table).
- A side panel explains the mood: who you're talking to, how it sounds, what to listen for, the neutral version.
- Every card has its own address (`#practice/<LineID>/<mood>`), so a phrase can be shared.

**Play (`#play`, anyone)**: the trail. The chase meter (stages from "Parapeet spotted" to "Caught him!" at 3,000 seeds),
streak, seeds, daily-goal ring, then each unit (Water cooler, Presentation, Board room) as a winding path of lessons of
five phrases, a mood challenge per unit, and locked lessons (Join free / Coming soon). "Weak spots" builds a review
from the cards the learner knows least or hasn't seen for a while. New players hear the story of Parapeet (with their name).

**Lessons (`#lesson/<key>`)**: about ten exercises: what does it mean, which mood is this, write it in French with word
tiles, what did you hear, now say it to <someone> (pick the right mood version), say it out loud (speech check; "I can't
speak right now" turns speaking off for 30 minutes). Check / Continue bar, wrong answers come back once at the end,
keys 1-4 and Enter, sounds, the mascot reacts. End screen: seeds, right-first-time %, streak, stars, new badges, confetti.

**Progress (`#progress`, anyone)**: the chase, seeds, streak (and best), lessons, phrases said out loud, the daily goal
(Casual 10 / Regular 20 / Serious 40 / Intense 80, +10 bonus seeds when reached), the last 14 days, how well each mood
is known, and 15 badges (Diplomat, Peacemaker, Romantic, Class clown, Mood ring, streaks, seeds...).

**My phrasebook (`#saved`, members)**: saved and typed-in phrases with listen, edit, delete, and a quiz (see the meaning,
type the French; accents and capitals don't matter; weaker phrases come up more often).

**Guests and accounts**: everything except My phrasebook works without an account; guests keep progress in the browser,
and it moves into the account on sign-up or sign-in. Guests see the free sample (Availability "basic"), members also
the "free" phrases, customer_type "premium" also "premium" ones. People who used the original app get their old likes
and "spoken" marks as seeds and mastery the first time they open the new one.

**Also**: landing page with a live swipeable card, Privacy & Terms (legal kit), Submit feedback (Prepsto), profile
(name, sound effects, voice speed, speaking exercises, delete my account), admin (overview, older feedback, users,
the phrase library by unit/access/voices and the "more phrases" requests), light and dark, the Android asset links.

## Setting it up in Anvil (once)

The app already exists in Anvil (parapeet.com). To try the rebuild before it replaces the live app:
1. Anvil editor → the Parapeet app → **Publish** → add an environment that runs branch **`forms`** (it gets its own URL;
   it usually shares the live database).
2. Open it in the editor on that branch and accept the **Schema Mismatch** alert with **"The schema of the source code is
   correct"**. It only adds: the `progress` table, `app_settings`, `feedback`, and new columns on `users` (display_name,
   is_admin, is_demo, last_seen, legal_*). No table or column is removed.
3. Check the **Users** service (email + password, Continue with Google, sign-up on).
4. Sign in with arkulinskis@gmail.com once (that account becomes admin).

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Fredoka, Nunito |

**Built into the browser:** Canvas 2D, Speech synthesis, Speech recognition, Web Audio API, Camera, microphone and screen, MediaRecorder, Screen Wake Lock, Vibration, localStorage, File downloads (Blob).

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Google service, Anvil JS bridge (anvil.js), Anvil Users.

**Build and test tools (not shipped):** Node.js, PyYAML, Headless Chrome (DevTools Protocol).

<!-- libraries:end -->

## Working on it

See `.claude/skills/parapeet/SKILL.md`. In short:

```
python tools/check.py                    # Anvil's validator, JS syntax, asset hashes, server tests -> ALL CHECKS PASSED
python -I tools/ui_test.py               # the real app in the Anvil App Server (Docker) driven by headless Chrome
python -I tools/ui_test.py --shots DIR   # + screenshots of every page (desktop/phone, light/dark, guest/member)
git push origin forms                    # deploy the branch (master once it is approved)
```

## Project layout

```
client_code/    startup, router, state, auth, legal; tones (the ten moods), gamerules (seeds, streaks, badges: shared
                with the server), drills (lesson builder), phrases (library + voices), game (progress), pp (JS engines)
                Layouts/Shell; Pages/ Landing Play Practice Lesson Progress Saved Auth Profile Admin;
                Components/ PhraseCard Bird Ring; Items/*; Dialogs/ CompareMoods NoteEdit HandsFree Story Gestures
server_code/    Phrases, Progress, Notes, Admin, Accounts, Feedback, DemoData (+ sample_phrases: only for an empty
                database), ServerModule1 (the original functions + Android asset links + delete_account), common,
                SchemaCheck, legal_server
theme/assets/   app.css, icons.css (generated), app-kit.js, pp-card.js (swipe card), pp-audio.js (voice, speech,
                recorder, sounds, confetti), theme.css (spinner), icon.svg + PNGs, manifest.json, legal-kit.js
tools/          check.py, assets.py, build_icons.py, make_icons.py, ui_test.py + ui/, live/drive.mjs, testing/
```
