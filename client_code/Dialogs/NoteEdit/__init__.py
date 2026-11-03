import anvil.server
from anvil import *

from ._anvil_designer import NoteEditTemplate
from ... import langs, state

HINTS = {"fr": "Je voulais te dire...", "es": "Quería decirte...", "it": "Volevo dirti..."}


class NoteEdit(NoteEditTemplate):
    """Add a phrase to My phrasebook (of the language being learned, or `lang`), or edit one (note_id).
    Closes with the saved note, or None."""

    def __init__(self, fr="", en="", note_id=None, lang=None, **properties):
        super().__init__(**properties)
        self.note_id = note_id
        self.lang = langs.valid(lang or state.lang())
        self.fr_label.text = langs.name(self.lang)
        self.fr_box.placeholder = HINTS[self.lang]
        self.fr_box.text, self.en_box.text = fr or "", en or ""
        self.title.text = "Edit this phrase" if note_id else "Save to your phrasebook"

    @handle("", "show")
    def form_show(self, **event_args):
        (self.en_box if self.fr_box.text else self.fr_box).focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        fr, en = (self.fr_box.text or "").strip(), (self.en_box.text or "").strip()
        if not fr or not en:
            self.message.text, self.message.visible = "Fill in both the %s and what it means." % langs.name(self.lang), True
            return
        self.save_button.enabled = False
        try:
            if self.note_id:
                r = anvil.server.call("edit_note", self.note_id, fr, en)
            else:
                r = anvil.server.call("add_note", fr, en, self.lang)
        finally:
            self.save_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.raise_event("x-close-alert", value=r["note"])
