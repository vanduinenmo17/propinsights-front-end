from ._anvil_designer import LandingPageTemplate
from anvil import *
import m3.components as m3
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class LandingPage(LandingPageTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    
  def btn_explore_dashboard_click(self, **event_args):
    """This method is called when the button is clicked"""
    open_form('DataDashboard')

  def btn_create_account_landingpage_click(self, **event_args):
    """This method is called when the button is clicked"""
    user = anvil.users.get_user()
    if not user:
      anvil.users.login_with_form(allow_cancel=True)
