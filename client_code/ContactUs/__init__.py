from ._anvil_designer import ContactUsTemplate
from anvil import *
import m3.components as m3
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from .. import user_ui


class ContactUs(ContactUsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    user_ui.init_header(self)

  def form_show(self, **event_args):
    """This method is called when the form is shown on the page"""
    self.layout.reset_links()
    self.layout.contact_us_link.role = 'selected'

  def submit_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user:
        return

    logged_in = user is not None
    if logged_in:
      # Users row is dict-like
      email = None
      try:
        email = user["email"]
      except Exception:
        if hasattr(user, "get"):
          email = user.get("email")

    firstName = self.first_name_textbox.text
    lastName = self.last_name_textbox.text
    message = self.message_textarea.text

    anvil.server.call('add_message', firstName, lastName, email, message)
    Notification("Feedback submitted!").show()
    self.clear_inputs()

  def clear_inputs(self):
    # Clear our three text boxes
    self.first_name_textbox.text = ""
    self.last_name_textbox.text = ""
    self.message_textarea.text = ""