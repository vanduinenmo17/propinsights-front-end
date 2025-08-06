from ._anvil_designer import HomepageTemplate
from anvil import *
import m3.components as m3
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server

class Homepage(HomepageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.menu_item_account = m3.MenuItem(text="Account")
    self.menu_item_account.add_event_handler("click", self.open_account)
    self.menu_item_logout = m3.MenuItem(text="Log Out")
    self.menu_item_logout.add_event_handler("click", self.do_logout)
    
    self.refresh_account_ui()
  
  def about_us_link_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('AboutUs')

  def contact_us_link_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('ContactUs')

  def data_dashboard_link_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('DataDashboard')

  def reset_links(self, **event_args):
    self.contact_us_link.role = ''
    self.about_us_link.role = ''

  def landing_page_link_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('LandingPage')

  def refresh_account_ui(self):
    user = anvil.users.get_user()

    if user:
      self.btn_account.text = user['email']
      # Build menu once
      if not self.btn_account.menu_items:
        self.btn_account.menu_items = [
          self.menu_item_account,
          self.menu_item_logout
        ]
    else:
      self.btn_account.text = "Login"
      self.btn_account.menu_items = []   

  def btn_account_click(self, **event_args):
    """This method is called when the Button is clicked"""
    # Not logged-in? Show the Users-service login form
    if self.btn_account.text == "Login":
      self.btn_account.menu_items = []  
      anvil.users.login_with_form(allow_cancel=True)

    # Either way, bring the UI back in line
    self.refresh_account_ui()

  def open_account(self, **event_args):
    open_form('AccountForm')        # or open a modal, etc.

  def do_logout(self, **event_args):
    anvil.users.logout()
    self.refresh_account_ui()