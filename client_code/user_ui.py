import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import get_open_form, open_form
import m3.components as m3

def _ensure_header_bound(form):
  """Bind header handlers and build the account menu (once per form)."""
  # Bind the Login button click everywhere this template is used
  if hasattr(form, "btn_login"):
    # Always (re)bind to be safe; Anvil ignores duplicate same handler no-op
    form.btn_login.set_event_handler("click", lambda **e: login_with_form_and_refresh(allow_cancel=True))

  # Build the Account menu once per form
  if hasattr(form, "btn_account") and not getattr(form, "_account_menu_bound", False):
    mi_account = m3.MenuItem(text="Account")
    mi_account.add_event_handler("click", lambda **e: open_form("AccountForm"))
    mi_logout = m3.MenuItem(text="Log Out")
    mi_logout.add_event_handler("click", lambda **e: logout_and_refresh())

    form.btn_account.menu_items = [mi_account, mi_logout]
    form._account_menu_bound = True  # idempotency flag

def _refresh_header_ui(form):
  """Show/hide Login vs Account and set the email label."""
  user = anvil.users.get_user()
  
  # If the open form has your layout's refresh method, prefer it:
  if hasattr(form, "refresh_account_ui"):
    form.refresh_account_ui()
    return
  
    # Fallback: update the shared header components directly
    is_logged_in = user is not None
  
  if hasattr(form, "btn_login"):
    form.btn_login.visible = not is_logged_in
  
    if hasattr(form, "btn_account"):
      form.btn_account.visible = is_logged_in
      if is_logged_in:
        # <- IMPORTANT: Users row must be indexed like a dict
        email = None
        try:
          email = user['email']
        except Exception:
          # Extra fallbacks just in case your Users schema is different
          if hasattr(user, 'get'):
            try:
              email = user.get('email')
            except Exception:
              pass
          if not email:
            email = getattr(user, 'email', None)
        form.btn_account.text = email or "Account"

def init_header(form=None):
  """Call this from any form's __init__ to wire + paint the header."""
  form = form or get_open_form()
  if not form:
    return
  _ensure_header_bound(form)
  _refresh_header_ui(form)

def refresh_layout_user_ui():
  """Re-wire and re-paint header on the currently open form."""
  form = get_open_form()
  if not form:
    return
  _ensure_header_bound(form)
  _refresh_header_ui(form)

def login_with_form_and_refresh(**kwargs):
  """Open login dialog, then refresh header; returns the user or None."""
  user = anvil.users.login_with_form(**kwargs)
  # After login, the same form is still open; wire + refresh it.
  refresh_layout_user_ui()
  return user

def logout_and_refresh():
  """Log out, navigate (if you like), then wire + refresh new form."""
  anvil.users.logout()
  # Navigate wherever you want users to land after logout:
  open_form("LandingPage")
  # Now that a NEW form is open, wire + refresh that form's header:
  refresh_layout_user_ui()