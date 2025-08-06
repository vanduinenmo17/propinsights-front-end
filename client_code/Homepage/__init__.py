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

  def btn_account_refresh(self):
    user = anvil.users.get_user()
    if user:
      self.btn_account.text = user['email']
      # adjust icon/avatar if using AvatarMenu
    else:
      self.btn_account.text = "Login"
    self.btn_account.visible = True

  def btn_account_click(self, **event_args):
    """This method is called when the Button is clicked"""
    if self.btn_account.text == "Login":
      anvil.users.login_with_form()
      self.btn_account_refresh()
    else:
      btn_account_menu_item_logout = m3.MenuItem(text="Log Out", leading_icon="undo")
      btn_account_menu_item_account = m3.MenuItem(text="Account", leading_icon="redo")
      self.btn_account.menu_items = [btn_account_menu_item_logout, btn_account_menu_item_account]


