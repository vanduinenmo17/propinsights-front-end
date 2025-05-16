from ._anvil_designer import AgGridFormTemplate
from anvil import *
import anvil.server
from anvil import js

class AgGridForm(AgGridFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self._rows = None
    
  def load_data(self, rows):
    """Store rows to render once the form is shown."""
    self._rows = rows

  def form_show(self, **event_args):
    """Runs after the HTML & scripts are in place."""
    if self._rows:
      js.call_js("renderAgGrid", self._rows)
