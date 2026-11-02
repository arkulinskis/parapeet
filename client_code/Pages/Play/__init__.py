from anvil import *

from ._anvil_designer import PlayTemplate
from ... import game, gamerules as G, phrases, router, state, tones


class Play(PlayTemplate):
    """#play, the trail: Parapeet's chase meter, streak, seeds and daily goal, then each unit (Water cooler,
    Presentation, Board room) as a winding path of lessons (5 phrases each), a mood challenge, and the lessons an
    account or the future unlocks. New players hear the story of Parapeet first (Dialogs.Story)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.units_panel.add_event_handler("x-lesson", self._open_lesson)
        self._draw()

    def _draw(self):
        s, p = game.summary(), game.progress()
        name = game.adventurer()
        self.hello.text = ("Bonjour, %s !" % name) if name else "Bonjour !"
        self.stage_name.text = s["stage_name"]
        self.stage_line.text = s["stage_line"]
        if s["stage_next"]:
            span = max(1, s["stage_next"] - s["stage_at"])
            pct = int(100 * (s["seeds"] - s["stage_at"]) / span)
            self.chase_text.text = "%s / %s seeds to the next stage" % ("{:,}".format(s["seeds"]), "{:,}".format(s["stage_next"]))
        else:
            pct = 100
            self.chase_text.text = "%s seeds. Parapeet is yours." % "{:,}".format(s["seeds"])
        self.dom_nodes["chase_fill"].style.width = "%d%%" % pct
        self.dom_nodes["chase_bird"].style.left = "%d%%" % pct
        self.streak_num.text = str(s["streak"])
        self.streak_card.classes["lit"] = s["today_seeds"] > 0 and s["streak"] > 0
        self.seeds_num.text = "{:,}".format(s["seeds"])
        self.goal_ring.value = s["goal_pct"]
        self.goal_ring.text = "%d/%d" % (s["today_seeds"], s["goal"])
        self.bird.mood = "wow" if s["goal_done"] else ("sleepy" if s["streak"] == 0 and s["seeds"] > 0 else "happy")
        locked = phrases.locked_total("signup")
        self.guest_note.visible = not state.me()
        self.guest_text.text = ("Playing as a guest: your seeds stay in this browser. A free account keeps them on every "
                                "device%s." % (" and unlocks %d more phrases" % locked if locked else ""))
        units = []
        for u in phrases.unit_numbers():
            info = phrases.unit_info(u)
            lessons = phrases.lessons(u, p)
            playable = [l for l in lessons if not l["locked"]]
            done = len([l for l in playable if l["stars"]])
            units.append(dict(info, lessons=lessons, done=done, total=len(playable),
                              count=len(phrases.in_unit(u))))
        self.units_panel.items = units
        mastered = len(p["mastery"])
        self.review_text.text = ("Parapeet picks the phrases and moods you know least, or haven't seen for a while."
                                 if mastered else "Finish a lesson first: then Parapeet knows what to bring back.")
        self.review_button.enabled = mastered > 0
        self.badges_text.text = "%d of %d earned%s" % (len(s["badges"]), len(G.BADGES),
                                                       (": " + ", ".join(G.BADGE_INFO[b][1] for b in s["badges"][-3:])) if s["badges"] else ". Finish a lesson for your first.")

    def _open_lesson(self, **event_args):
        lesson = event_args["lesson"]
        if lesson["locked"] == "signup":
            if confirm("A free account unlocks %d more phrases in this unit and keeps your seeds everywhere." % lesson.get("count", 0),
                       title="Unlock this lesson", buttons=[("Not now", False), ("Join free", True)], role="app-dialog"):
                router.go("auth", "signup")
            return
        if lesson["locked"]:
            if state.me():
                if confirm("More phrases for this unit are being recorded. Want to hear when they're ready?",
                           title="Coming soon", buttons=[("No thanks", False), ("Yes, tell me", True)], role="app-dialog"):
                    state.call("ask_for_more", "unit %s" % lesson["unit"])
                    state.toast("Noted! We'll let you know.", "ok")
            else:
                alert("More phrases for this unit are on the way.", title="Coming soon", role="app-dialog")
            return
        if not game.adventurer() and not state.store_get("story_seen", False):
            from ...Dialogs.Story import Story
            alert(Story(), buttons=[], role="app-dialog", dismissible=False)
            state.store_set("story_seen", True)
        router.go("lesson", lesson["key"])

    @handle("review_button", "click")
    def review_button_click(self, **event_args):
        router.go("lesson", "review")
