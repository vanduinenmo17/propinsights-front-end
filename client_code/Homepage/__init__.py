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
from .. import user_ui

class Homepage(HomepageTemplate):
  def __init__(self, **properties):
    ## Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Wire + paint the header on this page instance
    user_ui.init_header(self)
    
    ## Initialize account button
    self.menu_item_account = m3.MenuItem(text="Account")
    self.menu_item_account.add_event_handler("click", self.open_account)
    self.menu_item_logout = m3.MenuItem(text="Log Out")
    self.menu_item_logout.add_event_handler("click", self.do_logout)

    self.btn_account.menu_items = [
      self.menu_item_account,
      self.menu_item_logout
    ]
  
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

  def open_account(self, **event_args):
    open_form('AccountForm')

  def do_logout(self, **event_args):
    user_ui.logout_and_refresh()

  def btn_login_click(self, **event_args):
    """This method is called when the component is clicked."""
    user_ui.login_with_form_and_refresh(allow_cancel=True)
