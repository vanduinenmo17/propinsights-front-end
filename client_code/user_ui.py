import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import get_open_form, open_form
import m3.components as m3
from anvil.js.window import setTimeout

# Keep a reference to the active layout instance
_layout_form = None

def register_layout(form):
  """Call this from the layout form (Homepage.__init__)."""
  global _layout_form
  _layout_form = form
  _ensure_header_bound(_layout_form)
  _refresh_header_ui(_layout_form)

def _target_form(form=None):
  """Always return the layout instance if available."""
  f = form or get_open_form()
  if not f:
    return _layout_form
  lay = getattr(f, "layout", None)
  return lay or _layout_form or f

def _ensure_header_bound(form):
  # Bind Login click globally (on the LAYOUT)
  if hasattr(form, "btn_login"):
    def _login_click(**e):
      if anvil.users.get_user():
        refresh_layout_user_ui()
        return
      login_with_form_and_refresh(allow_cancel=True)
    form.btn_login.set_event_handler("click", _login_click)

  # Only build the Account menu if it's empty AND not bound yet
  if (hasattr(form, "btn_account")
      and not getattr(form, "_account_menu_bound", False)
      and not getattr(form.btn_account, "menu_items", None)):
    mi_account = m3.MenuItem(text="Account")
    mi_account.add_event_handler("click", lambda **e: open_form("AccountForm"))
    mi_logout = m3.MenuItem(text="Log Out")
    mi_logout.add_event_handler("click", lambda **e: logout_and_refresh())
    form.btn_account.menu_items = [mi_account, mi_logout]
    form._account_menu_bound = True

def _refresh_header_ui(form):
  """Show/hide Login vs Account and set the email label (on the LAYOUT)."""
  user = anvil.users.get_user()
  is_logged_in = user is not None

  # If your layout exposes a painter, let it run…
  if hasattr(form, "refresh_account_ui"):
    try:
      form.refresh_account_ui()
    except Exception:
      pass  # fall through to the fallback regardless

  # …then fallback ensures the final state is correct.
  if hasattr(form, "btn_login"):
    form.btn_login.visible = not is_logged_in

  if hasattr(form, "btn_account"):
    form.btn_account.visible = is_logged_in
    if is_logged_in:
      email = None
      try:
        email = user["email"]         # Users row is dict-like
      except Exception:
        if hasattr(user, "get"):
          email = user.get("email")
        if not email:
          email = getattr(user, "email", None)
      form.btn_account.text = email or "Account"
    else:
      form.btn_account.text = "Account"

def init_header(form=None):
  """Call from any page's __init__ so the LAYOUT is wired + painted."""
  tgt = _target_form(form)
  if not tgt:
    return
  _ensure_header_bound(tgt)
  _refresh_header_ui(tgt)

def refresh_layout_user_ui():
  """Re-wire and repaint the LAYOUT, regardless of which page is open."""
  tgt = _target_form()
  if not tgt:
    return
  _ensure_header_bound(tgt)
  _refresh_header_ui(tgt)

def login_with_form_and_refresh(**kwargs):
  """Open login dialog, then repaint the LAYOUT. Returns user or None."""
  user = anvil.users.login_with_form(**kwargs)   # Shows Anvil’s login UI and returns the user on success. :contentReference[oaicite:1]{index=1}
  # Defer the repaint to the next tick to avoid any race with UI updates.
  setTimeout(lambda: refresh_layout_user_ui(), 0)
  return user

def logout_and_refresh():
  """Log out, navigate, then repaint the NEW LAYOUT."""
  anvil.users.logout()
  open_form("LandingPage")
  setTimeout(lambda: refresh_layout_user_ui(), 0)