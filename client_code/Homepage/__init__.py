from ._anvil_designer import HomepageTemplate
from anvil import *
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

  def button_1_click(self, **event_args):
    """This method is called when the button is clicked"""
    user = anvil.users.get_user()
    if user:
      anvil.users.logout()
      anvil.users.login_with_form()

  def landing_page_link_click(self, **event_args):
    """This method is called when the link is clicked"""
    open_form('LandingPage')


