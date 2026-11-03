from anvil import *

from ._anvil_designer import StoryTemplate
from ... import game, langs, state


class Story(StoryTemplate):
    """The story of Parapeet (from the original app), told to a new player, with their name in it.
    Closes with True when they start playing."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.name_box.text = game.adventurer()
        self.part_two.visible = False
        self.start_button.text = "Get my %s back!" % langs.name(state.lang())

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.next_button_click()

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if not name:
            self.message.text, self.message.visible = "I need your name, adventurer!", True
            return
        game.set_adventurer(name)
        lang = langs.name(state.lang())
        self.story_two.text = ("One fateful day, Parapeet spotted %s, a curious mind full of %s. He couldn't resist: "
                               "he swooped down and pecked away at all those lovely phrases. By sunset, %s's %s was "
                               "gone, with gaps and confusion where it used to be." % (name, lang, name, lang))
        self.story_three.text = ("Now %s is on his trail, phrase by phrase, seed by seed. Every right answer earns seeds. "
                                 "Collect 3,000 and Parapeet is caught, and your %s is back, in every mood: for "
                                 "the boss, the client, the hothead, the sad friend and the one you love." % (name, lang))
        self.part_one.visible = False
        self.part_two.visible = True
        self.bird.mood = "wow"

    @handle("skip_button", "click")
    def skip_button_click(self, **event_args):
        if not game.adventurer():
            game.set_adventurer("Adventurer")
        self.raise_event("x-close-alert", value=False)

    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
