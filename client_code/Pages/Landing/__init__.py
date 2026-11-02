from anvil import *

from ._anvil_designer import LandingTemplate
from ... import router, state, tones

# The hero's live card: "Could you lend me your pen?" in all ten moods (phrase 23 of the free sample), kept here so
# the front page needs no server call.
DEMO_FR = ["Pourrais-tu me prêter ton stylo, s'il te plaît ?",
           "Je l'ai oublié chez moi et j'ai besoin d'écrire quelques notes.",
           "Bien sûr, voici mon stylo, vous pouvez l'emprunter.",
           "J'ai besoin de noter quelques informations importantes.",
           "Je vois que tu es contrarié, mais pourrais-tu me prêter ton stylo, s'il te plaît ? J'en ai vraiment besoin pour prendre des notes.",
           "Je comprends que tu puisses être mécontent, mais pourrais-tu faire preuve d'un peu de compréhension et me prêter ton stylo, s'il te plaît ?",
           "Je sais que tu es triste en ce moment, mais si tu peux me prêter ton stylo, cela me serait d'une grande aide.",
           "Mon amour, pourrais-tu me faire le plus tendre des cadeaux en me prêtant ton stylo ?",
           "Si tu pouvais me prêter ton stylo, je t'en serais vraiment reconnaissant.",
           "Tu peux me prêter ta plume de phénix, s'il te plaît ?"]
DEMO_EN = ["Could you lend me your pen, please?",
           "I forgot it at home and I need to write some notes.",
           "Of course, here is my pen, you can borrow it.",
           "I need to jot down some important information.",
           "I see you're upset, but could you lend me your pen, please? I really need it to take notes.",
           "I understand you may be unhappy, but could you show a little understanding and lend me your pen, please?",
           "I know you're sad right now, but if you can lend me your pen, it would be a great help.",
           "My love, could you give me the most tender of gifts by lending me your pen?",
           "If you could lend me your pen, I would really appreciate it.",
           "Can you lend me your phoenix feather, please?"]


class Landing(LandingTemplate):
    """#landing, the front page: a live swipeable card in the hero, the ten moods, how it works, the game, the story,
    who it's for, questions. Static copy lives in the template; only the signed-in variations are set here."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        self.signup_line.visible = not me
        demo = {"id": 23, "fr": dict(zip(tones.KEYS, DEMO_FR)), "en": dict(zip(tones.KEYS, DEMO_EN))}
        self.demo_card.load([demo], 0, 7)  # start on Lover: the most surprising one

    @handle("demo_card", "change")
    def demo_card_change(self, **event_args):
        st = event_args["state"]
        self.hero_bird.mood = {"Lover": "happy", "Stupid": "wow", "Sad": "sleepy", "Agressive": "oops",
                               "Frustrated": "oops"}.get(st["key"], "talk")

    @handle("story_button", "click")
    def story_button_click(self, **event_args):
        from ...Dialogs.Story import Story
        if alert(Story(), buttons=[], role="app-dialog"):
            router.go("play")
