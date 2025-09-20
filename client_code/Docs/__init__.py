from ._anvil_designer import DocsTemplate
from anvil import *
import anvil.server
import m3.components as m3
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import user_ui

class Docs(DocsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    user_ui.init_header(self)

  def absentee_link_click(self, **event_args):
    self.anc_absentee.scroll_into_view()

  def columns_link_click(self, **event_args):
    self.anc_columns.scroll_into_view()
