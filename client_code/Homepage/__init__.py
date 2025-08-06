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

    self.btn_account_refresh()
  
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
      self.btn_account.text = user.get('email') or user.get('name')
      # Build menu once
      if not self.btn_account.menu_items:
        self.btn_account.menu_items = [
          m3.MenuItem(text="Account", leading_icon="settings",
                      click=self.open_account),
          m3.MenuItem(text="Log Out", leading_icon="logout",
                      click=self.do_logout)
        ]
    else:
      self.btn_account.text = "Login"
      self.btn_account.menu_items = []    

  def btn_account_click(self, **event_args):
    """This method is called when the Button is clicked"""
    # Not logged-in? Show the Users-service login form
    if self.btn_account.text == "Login":
      anvil.users.login_with_form()

    # Either way, bring the UI back in line
    self.refresh_account_ui()