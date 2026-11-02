import random

from anvil import *
import anvil.server

from ._anvil_designer import SavedTemplate
from ... import pp, state

PASS = 0.8


class Saved(SavedTemplate):
    """#saved, My phrasebook (members): the phrases they saved or typed in (the old Notes), each with listen, edit
    and delete, and a quiz: see the meaning, type the French; weaker phrases come up more often."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.quiz_part.visible = False
        self.notes_panel.add_event_handler("x-changed", self._load)
        self._load()

    def _load(self, **event_args):
        self.notes = anvil.server.call("list_notes")["notes"]
        self.notes_panel.items = self.notes
        self.empty.visible = not self.notes
        self.count.text = state.plural(len(self.notes), "phrase") + " saved" if self.notes else "Your own collection of phrases"
        self.quiz_button.enabled = len(self.notes) >= 1

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        from ...Dialogs.NoteEdit import NoteEdit
        if alert(NoteEdit(), buttons=[], role="app-dialog"):
            state.toast("Saved", "ok")
            self._load()

    # ---- quiz
    @handle("quiz_button", "click")
    def quiz_button_click(self, **event_args):
        self.quiz_part.visible = True
        self._asked = 0
        self._next_question()

    @handle("quiz_close", "click")
    def quiz_close_click(self, **event_args):
        self.quiz_part.visible = False
        self._load()

    def _next_question(self):
        if not self.notes:
            self.quiz_part.visible = False
            return
        weights = [6 - min(5, n["level"]) for n in self.notes]
        total, r, pick = sum(weights), random.random(), 0
        acc = 0.0
        for idx, w in enumerate(weights):
            acc += w / float(total)
            if r <= acc:
                pick = idx
                break
        self.q = self.notes[pick]
        self._asked += 1
        self.quiz_count.text = "Question %d" % self._asked
        self.quiz_prompt.text = self.q["en"]
        self.quiz_box.text = ""
        self.quiz_result.text = ""
        self.quiz_result.role = ["sv-quiz-result"]
        self.quiz_check.visible, self.quiz_show.visible, self.quiz_next.visible = True, True, False
        self.quiz_box.focus()

    @handle("quiz_box", "pressed_enter")
    def quiz_box_pressed_enter(self, **event_args):
        if self.quiz_next.visible:
            self.quiz_next_click()
        else:
            self.quiz_check_click()

    @handle("quiz_check", "click")
    def quiz_check_click(self, **event_args):
        score = pp.similarity(self.quiz_box.text or "", self.q["fr"])
        right = score >= PASS
        anvil.server.call("note_result", self.q["id"], right)
        self.q["level"] = min(5, self.q["level"] + 1) if right else max(0, self.q["level"] - 1)
        pp.sfx("good" if right else "bad")
        self.quiz_result.text = ("Très bien ! %d%% match." % int(score * 100)) if right else ("%d%% match. The answer: %s" % (int(score * 100), self.q["fr"]))
        self.quiz_result.role = ["sv-quiz-result", "good" if right else "bad"]
        self.quiz_check.visible, self.quiz_show.visible, self.quiz_next.visible = False, False, True

    @handle("quiz_show", "click")
    def quiz_show_click(self, **event_args):
        self.quiz_result.text = "The answer: %s" % self.q["fr"]
        self.quiz_result.role = ["sv-quiz-result"]
        self.quiz_check.visible, self.quiz_show.visible, self.quiz_next.visible = False, False, True
        pp.fire("say", [self.q["fr"], "fr", "Basic"])

    @handle("quiz_next", "click")
    def quiz_next_click(self, **event_args):
        self._next_question()
