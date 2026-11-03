"""Admin page callables: overview, users (make admin, disable), the phrase library's numbers and the old
"interest" log. Admins only. Feedback admin calls live in Feedback.py."""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import DemoData, Feedback, Notes, Progress


@anvil.server.callable(require_user=True)
def admin_overview():
    C.require_admin()
    pc = Progress.summary_counts()
    content = DemoData.counts()
    return {"users": len([u for u in app_tables.users.search() if not u["is_demo"]]),
            "admins": len(app_tables.users.search(is_admin=True)),
            "feedback_new": Feedback.new_count(),
            "learners": pc["learners"], "lessons": pc["lessons"], "notes": Notes.count(),
            "phrases": sum(content["by_access"].values())}


def _user(u):
    return {"id": u.get_id(), "email": u["email"], "name": C.name_of(u), "is_admin": C.is_admin(u),
            "enabled": u["enabled"] is not False, "joined": C.iso(u["signed_up"]), "last_seen": C.iso(u["last_seen"])}


@anvil.server.callable(require_user=True)
def list_users(query=None):
    C.require_admin()
    query = C.text(query, 80).lower()
    rows = [u for u in app_tables.users.search(tables.order_by("signed_up", ascending=False)) if not u["is_demo"]]
    if query:
        rows = [u for u in rows if query in (u["email"] or "").lower() or query in (u["display_name"] or "").lower()]
    return {"users": [_user(u) for u in rows[:200]], "total": len(rows)}


@anvil.server.callable(require_user=True)
def set_admin(user_id, flag):
    me = C.require_admin()
    u = C.row_by_id(app_tables.users, user_id)
    if u is None:
        return C.fail("That account no longer exists.")
    if u == me and not flag:
        return C.fail("You can't remove your own admin rights.")
    u["is_admin"] = bool(flag)
    return C.ok(user=_user(u))


@anvil.server.callable(require_user=True)
def set_enabled(user_id, flag):
    me = C.require_admin()
    u = C.row_by_id(app_tables.users, user_id)
    if u is None:
        return C.fail("That account no longer exists.")
    if u == me:
        return C.fail("You can't disable your own account.")
    u["enabled"] = bool(flag)
    return C.ok(user=_user(u))


@anvil.server.callable(require_user=True)
def admin_content():
    """The phrase library by unit and access level, the recorded voices, and the latest "interest" notes (people who
    asked for more phrases)."""
    C.require_admin()
    c = DemoData.counts()
    rows = sorted(app_tables.interest.search(), key=lambda r: C.iso(r["mydatetime"]) or "", reverse=True)  # old rows have no time zone
    interest = [{"who": r["showed_interest"] or "", "what": r["interested"] or "", "when": C.iso(r["mydatetime"])}
                for r in rows[:40]]
    return {"by_access": c["by_access"], "by_unit": c["by_unit"], "voices_fr": c["voices_fr"],
            "voices_en": c["voices_en"], "languages": c["languages"], "interest": interest,
            "interest_total": len(rows)}


@anvil.server.callable(require_user=True)
def ask_for_more(topic):
    """A member asks to hear about more phrases (the old "Get more phrases!" button)."""
    user = C.require_user()
    if C.rate_limited("interest", 5, 3600):
        return C.ok()
    app_tables.interest.add_row(showed_interest=user["email"], mydatetime=C.now(), interested=C.text(topic, 80) or "more phrases")
    return C.ok()
