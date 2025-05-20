from ._anvil_designer import DataDashboardTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from tabulator.Tabulator import Tabulator

class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    ## User Login Prompt
    anvil.users.login_with_form()
    ## Initialize Map
    # Add access token and center map on Denver
    token = "pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw"
    self.mapbox_map.layout.mapbox = dict(accesstoken=token, center=dict(lat=39.747508, lon=-104.987833), zoom=8)
    self.mapbox_map.layout.margin = dict(t=0, b=0, l=0, r=0)
    # Add title to map and pull data to display
    self.mapbox_map.data = anvil.server.call('get_map_data')

    # ---- Tabulator block ----
    self.tabulator.data = anvil.server.call('get_table_data')
    # self.tabulator.columns = [
    #   {"title": "LAT", "field": "LAT"},
    #   {"title": "LON", "field": "LON"},
    #   {"title": "Address", "field": "Address"}
    # ]

  def select_data_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    if self.data_select_panel.visible is False:
      self.data_select_panel.visible = True
      # self.data_select_panel
    else: 
      self.data_select_panel.visible = False
