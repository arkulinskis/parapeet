from anvil import *

from ... import state
from ._anvil_designer import LessonNodeTemplate


class LessonNode(LessonNodeTemplate):
    """A stop on the trail: a lesson, the unit's mood challenge (a crown) or a locked lesson. item = a lesson from
    phrases.lessons(). Clicking raises x-lesson; the Play page decides (open it, or explain the lock)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i = self.item
        locked, done = bool(i["locked"]), i["stars"] > 0
        icon = "lock" if locked else ("crown" if i["kind"] == "challenge" else ("check" if done else "star"))
        self.icon.classes.add("ic-" + icon)
        for cls, on in (("locked", locked), ("done", done), ("current", bool(i.get("current"))),
                        ("challenge", i["kind"] == "challenge")):
            self.box.classes[cls] = on
        self.start_bubble.visible = bool(i.get("current"))
        self.stars.text = ("★" * i["stars"] + "☆" * (3 - i["stars"])) if done else ""
        self.stars.visible = done
        if locked:
            self.caption.text = "Join free" if i["locked"] == "signup" else "Coming soon"
        elif i["kind"] == "challenge":
            self.caption.text = "Mood challenge"
        else:
            self.caption.text = "Lesson %d" % i["n"]
        state.set_attr(self.btn, "aria-label", "%s%s" % (self.caption.text, " (locked)" if locked else ""))

    def btn_click(self, event):
        self.parent.raise_event("x-lesson", lesson=self.item)
