from ._anvil_designer import AboutUsTemplate
from anvil import *
import anvil.server


class AboutUs(AboutUsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def form_show(self, **event_args):
    """This method is called when the form is shown on the page"""
    self.layout.reset_links()
    self.layout.about_us_link.role = 'selected'
