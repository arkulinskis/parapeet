from anvil import *

from ._anvil_designer import ProfileTemplate
import anvil.server

from ... import auth, router, state
from anvil.js import window


class Profile(ProfileTemplate):
    """#profile: your name, light/dark, a password reset link, Privacy & Terms, feedback, sign out."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._show_me()
        self._show_theme()
        self.sfx_box.checked = state.store_get("sfx", True) is not False
        self.speed_drop.items = [("Slower", 0.8), ("Normal", 1), ("A bit faster", 1.15)]
        speed = state.store_get("speed", 1) or 1
        self.speed_drop.selected_value = min([0.8, 1, 1.15], key=lambda v: abs(v - speed))
        self.speak_box.checked = (state.store_get("speak_off_until", 0) or 0) < window.Date.now()

    @handle("sfx_box", "change")
    def sfx_box_change(self, **event_args):
        state.store_set("sfx", bool(self.sfx_box.checked))

    @handle("speed_drop", "change")
    def speed_drop_change(self, **event_args):
        state.store_set("speed", self.speed_drop.selected_value)

    @handle("speak_box", "change")
    def speak_box_change(self, **event_args):
        state.store_set("speak_off_until", 0 if self.speak_box.checked else window.Date.now() + 10 * 365 * 86400000)

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if not confirm("Your account, seeds, streak, badges and saved phrases are deleted for good.",
                       title="Delete your account?", buttons=[("Keep my account", False), ("Delete it", True)],
                       role="app-dialog"):
            return
        anvil.server.call("delete_account")
        auth.sign_out()
        state.toast("Your account is deleted. Au revoir !", "ok")
        router.go("landing")

    def _show_me(self):
        me = state.me()
        self.initials.text = state.initials(me.get("name"))
        self.name_title.text = me.get("name") or ""
        joined = state.month_year(me.get("joined"))
        self.email_line.text = (me.get("email") or "") + (" · member since " + joined if joined else "")
        self.name_box.text = me.get("name") or ""
        self.admin_link.visible = bool(me.get("is_admin"))

    def _show_theme(self):
        t = state.theme()
        for name, el in (("auto", self.theme_auto), ("light", self.theme_light), ("dark", self.theme_dark)):
            el.classes["on"] = name == t

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-pick"))
        self._show_theme()

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.save_button_click()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast("Please tell us your name.", "error")
            return
        r = state.call("update_profile", name)
        if r:
            state.set_me(r["me"])
            self._show_me()
            state.toast("Saved", "ok")

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        r = auth.reset(state.me()["email"])
        state.toast(r["message"], "ok")

    def feedback_click(self, event):
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast("Signed out. See you soon!")
        router.go("landing")
