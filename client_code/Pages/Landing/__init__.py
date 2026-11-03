from anvil import *

from ._anvil_designer import LandingTemplate
from ... import langs, phrases, router, state, tones
from ...Dialogs.LanguagePick import choices

# The hero's live card: "Could you lend me your pen?" in all ten moods (phrase 23 of the free sample) in each
# language, kept here so the front page needs no server call. The same sentences fill the "ten moods" section.
DEMO = {
    "fr": ["Pourrais-tu me prêter ton stylo, s'il te plaît ?",
           "Je l'ai oublié chez moi et j'ai besoin d'écrire quelques notes.",
           "Bien sûr, voici mon stylo, vous pouvez l'emprunter.",
           "J'ai besoin de noter quelques informations importantes.",
           "Je vois que tu es contrarié, mais pourrais-tu me prêter ton stylo, s'il te plaît ? J'en ai vraiment besoin pour prendre des notes.",
           "Je comprends que tu puisses être mécontent, mais pourrais-tu faire preuve d'un peu de compréhension et me prêter ton stylo, s'il te plaît ?",
           "Je sais que tu es triste en ce moment, mais si tu peux me prêter ton stylo, cela me serait d'une grande aide.",
           "Mon amour, pourrais-tu me faire le plus tendre des cadeaux en me prêtant ton stylo ?",
           "Si tu pouvais me prêter ton stylo, je t'en serais vraiment reconnaissant.",
           "Tu peux me prêter ta plume de phénix, s'il te plaît ?"],
    "es": ["¿Me prestas tu bolígrafo, por favor?",
           "Se me olvidó el mío en casa y necesito tomar unas notas.",
           "Por supuesto, aquí tiene mi bolígrafo, puede usarlo.",
           "Necesito anotar unos datos importantes.",
           "Veo que estás molesto, pero ¿podrías prestarme tu bolígrafo, por favor? De verdad lo necesito para tomar notas.",
           "Entiendo que puedas estar descontento, pero ¿podrías ser un poco comprensivo y prestarme tu bolígrafo, por favor?",
           "Sé que estás triste en este momento, pero si puedes prestarme tu bolígrafo, me ayudarías mucho.",
           "Mi amor, ¿me harías el regalo más tierno del mundo prestándome tu bolígrafo?",
           "Si pudieras prestarme tu bolígrafo, te lo agradecería muchísimo.",
           "¿Me prestas tu pluma de fénix, por favor?"],
    "it": ["Mi presteresti la tua penna, per favore?",
           "L'ho dimenticata a casa e devo prendere qualche appunto.",
           "Certo, ecco la mia penna, può prenderla in prestito.",
           "Ho bisogno di annotare alcune informazioni importanti.",
           "Vedo che sei contrariato, ma potresti prestarmi la tua penna, per favore? Mi serve davvero per prendere appunti.",
           "Capisco che tu possa essere scontento, ma potresti essere un po' comprensivo e prestarmi la tua penna, per favore?",
           "So che in questo momento sei triste, ma se puoi prestarmi la tua penna, mi saresti di grande aiuto.",
           "Amore mio, mi faresti il regalo più tenero del mondo prestandomi la tua penna?",
           "Se potessi prestarmi la tua penna, te ne sarei davvero grato.",
           "Mi presti la tua piuma di fenice, per favore?"],
}
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
WHO = {"Basic": "to anyone", "Colleague": "team talk", "Client": "polite \"{formal}\"", "Boss": "up the ladder",
       "Agressive": "calming someone angry", "Frustrated": "keeping your cool", "Sad": "someone who's sad",
       "Lover": "soft and tender", "Impressed": "warm praise", "Stupid": "friends only"}


class Landing(LandingTemplate):
    """#landing, the front page: language tabs and a live swipeable card in the hero, the ten moods, how it works,
    the game, the story, who it's for, questions. Static copy lives in the template; the language-dependent parts
    and the signed-in variations are set here. Picking a language here switches the whole app to it."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        self.signup_line.visible = not me
        self.lang_tabs.add_event_handler("x-lang", self._lang_picked)
        self._show(state.lang())

    def _show(self, code):
        """The demo card, the language tabs and the ten moods in this language."""
        self.lang_tabs.items = choices()
        self.demo_card.load([{"id": 23, "lang": code, "fr": dict(zip(tones.KEYS, DEMO[code])),
                              "en": dict(zip(tones.KEYS, DEMO_EN))}], 0, 7)  # start on Lover: the most surprising one
        formal = langs.info(code)["formal"]
        self.moods_panel.items = [{"key": k, "who": WHO[k].replace("{formal}", formal), "text": t, "en": e, "lang": code}
                                  for k, t, e in zip(tones.KEYS, DEMO[code], DEMO_EN)]

    def _lang_picked(self, code, **event_args):
        if code != state.lang():
            phrases.switch(code)
            shell = self.layout
            if shell is not None and hasattr(shell, "show_lang"):
                shell.show_lang()
        self._show(code)

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
