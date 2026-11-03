from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ProgressTemplate
from ... import game, gamerules as G, phrases, state, tones

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class Progress(ProgressTemplate):
    """#progress: the chase for Parapeet, totals, the daily goal (change it here), the last 14 days, how well each
    mood is known, and every badge (earned ones in colour)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._draw()

    def _draw(self):
        s, p = game.summary(), game.progress()
        me = state.me()
        self.sub.text = "Signed in as %s" % me["name"] if me else "Playing as a guest"
        self.guest_note.visible = not me
        self.stage_name.text = s["stage_name"]
        self.stage_line.text = s["stage_line"]
        pct = min(100, int(100 * s["seeds"] / G.CATCH))
        self.dom_nodes["catch_fill"].style.width = "%d%%" % pct
        self.catch_text.text = "%s of %s seeds to catch Parapeet (%d%%)" % ("{:,}".format(s["seeds"]), "{:,}".format(G.CATCH), pct)
        self.bird.mood = "wow" if s["seeds"] >= G.CATCH else "happy"
        self.n_seeds.text = "{:,}".format(s["seeds"])
        self.n_streak.text = str(s["streak"])
        self.best_streak.text = "day streak · best %d" % s["best_streak"]
        self.n_lessons.text = str(s["lessons_done"])
        self.n_said.text = str(s["said"])
        self.goal_ring.value = s["goal_pct"]
        self.goal_ring.text = "%d/%d" % (s["today_seeds"], s["goal"])
        self.goal_text.text = ("Done for today. Bravo!" if s["goal_done"] else
                               "%d more seeds today to reach your goal (and +10 bonus)." % (s["goal"] - s["today_seeds"]))
        for g, btn in ((10, self.g10), (20, self.g20), (40, self.g40), (80, self.g80)):
            btn.role = ["seg", "on"] if s["goal"] == g else ["seg"]
        self.days_panel.items = self._days(p, s["goal"])
        by_mood = dict((k, [ph["id"] for ph in phrases.all_phrases() if ph["fr"].get(k)]) for k in tones.KEYS)
        pcts = G.mood_mastery(p, by_mood, state.lang())
        self.moods_panel.items = [{"key": k, "label": tones.label(k), "colour": tones.TONES[k]["colour"],
                                   "icon": tones.TONES[k]["icon"], "pct": pcts[k],
                                   "right": int(p["stats"].get("c_" + k) or 0)} for k in tones.KEYS]
        have = set(s["badges"])
        self.badges_panel.items = [{"id": b, "name": n, "desc": d, "icon": ic, "earned": b in have, "new": False}
                                   for b, n, d, ic in G.BADGES]

    def _days(self, p, goal):
        days = p["stats"].get("days") or {}
        out = []
        now = window.Date.now()
        top = max([goal] + [int(v or 0) for v in days.values()])
        for back in range(13, -1, -1):
            d = anvil.js.new(window.Date, now - back * 86400000)
            key = "%04d-%02d-%02d" % (d.getFullYear(), d.getMonth() + 1, d.getDate())
            n = int(days.get(key) or 0)
            out.append({"day": DAY_NAMES[(d.getDay() + 6) % 7][0] if back else "Today", "seeds": n,
                        "pct": int(100 * n / max(1, top)), "goal": n >= goal, "today": back == 0})
        return out

    def _goal(self, n):
        game.set_goal(n)
        state.toast("Daily goal: %d seeds" % n, "ok")
        self._draw()
        if self.layout is not None:
            self.layout.refresh_stats()

    @handle("g10", "click")
    def g10_click(self, **event_args):
        self._goal(10)

    @handle("g20", "click")
    def g20_click(self, **event_args):
        self._goal(20)

    @handle("g40", "click")
    def g40_click(self, **event_args):
        self._goal(40)

    @handle("g80", "click")
    def g80_click(self, **event_args):
        self._goal(80)
