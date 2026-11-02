import datetime

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ShellTemplate
from ... import auth, game, router, state

THEMES = ["auto", "light", "dark"]
NO_STATS = ("landing", "auth", "admin")


class Shell(ShellTemplate):
    """The frame around every page: header (menu, streak + seeds, Sign in / Join free or the account menu), the footer
    and the phone tab bar. Pages use it with <anvil-form layout="parapeet.Layouts.Shell">.

    Anvil keeps ONE Shell while pages come and go (open_form only swaps the "content" slot when the layout matches),
    so everything that depends on who is signed in or which page is open is drawn in refresh(), which router.show()
    calls after every page change. Pages call refresh_stats() after someone earns seeds."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.copyright_label.text = "© %d Parapeet, by Arkvital" % datetime.date.today().year
        self._outside = anvil.js.report_exceptions(self._close_menu_outside)
        self._keys = anvil.js.report_exceptions(self._key)
        self.refresh("")

    def refresh(self, page):
        me = state.me()
        self.classes.update({"signed-in": bool(me), "signed-out": not me, "no-chrome": page == "lesson",
                             "no-tabbar": page == "auth" or (page == "landing" and not me),
                             "page-practice": page == "practice"})
        self.member_actions.visible = bool(me)
        self.guest_actions.visible = not me and page != "auth"
        self.menu.visible = False
        state.set_attr(self.brand, "href", "#play" if me else "#landing")
        links = [{"page": p, "label": label, "icon": icon, "on": p == page} for p, label, icon in router.NAV]
        self.nav_panel.items = links
        self.tab_panel.items = links
        self.tab_profile.classes["on"] = page in ("profile", "auth")
        state.set_attr(self.tab_profile, "href", "#profile" if me else "#auth")
        if me:
            self.avatar_button.text = state.initials(me.get("name"))
            self.menu_name.text = me.get("name") or ""
            self.menu_email.text = me.get("email") or ""
            self.admin_link.visible = bool(me.get("is_admin"))
        self.stats_chip.visible = page not in NO_STATS
        if page not in NO_STATS:
            self.refresh_stats()
        self._show_theme()

    def refresh_stats(self):
        """The streak flame and the seed count in the header."""
        try:
            s = game.summary()
        except Exception:
            self.stats_chip.visible = False
            return
        self.streak_label.text = str(s["streak"])
        self.seeds_label.text = "{:,}".format(s["seeds"])
        self.streak_box.classes["lit"] = s["streak"] > 0 and s["today_seeds"] > 0
        state.set_attr(self.stats_chip, "title", "%d-day streak · %d seeds · today %d/%d" % (
            s["streak"], s["seeds"], s["today_seeds"], s["goal"]))

    # ---- account menu
    @handle("avatar_button", "click")
    def avatar_button_click(self, **event_args):
        self.menu.visible = not self.menu.visible

    def _close_menu_outside(self, event):
        if self.menu.visible and not event.target.closest(".anvil-role-avatar, .ui-menu .ui-seg"):
            self.menu.visible = False

    def _key(self, event):
        if event.key == "Escape":
            self.menu.visible = False

    @handle("", "show")
    def form_show(self, **event_args):
        window.document.addEventListener("click", self._outside, True)
        window.document.addEventListener("keydown", self._keys)

    @handle("", "hide")
    def form_hide(self, **event_args):
        window.document.removeEventListener("click", self._outside, True)
        window.document.removeEventListener("keydown", self._keys)

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-set"))
        self._show_theme()

    def _show_theme(self):
        t = state.theme()
        for name, el in zip(THEMES, [self.theme_auto, self.theme_light, self.theme_dark]):
            el.classes["on"] = name == t

    def feedback_click(self, event):
        self.menu.visible = False
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast("Signed out. À bientôt !")
        router.go("landing")
