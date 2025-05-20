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

    ## Set sizing of components in flow panel
    self.mapbox_map.width = "50%"
    self.data_select_panel.width = "50%"
    self.data_select_panel.visible = True

    
  def select_data_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Flip visibility
    self.data_select_panel.visible = not self.data_select_panel.visible

    # Clear out everything in the FlowPanel
    self.flow_panel.clear()

    if self.data_select_panel.visible:
      # Explicitly set both widths to 50%
      self.mapbox_map.width = "50%"
      self.data_select_panel.width = "50%"
      self.flow_panel.add_component(self.mapbox_map)
      self.flow_panel.add_component(self.data_select_panel)
    else:
      # Explicitly set map to 100%, and data_select_panel to 100% (important)
      self.mapbox_map.width = "100%"
      self.data_select_panel.width = "100%"   # <-- add this line!
      self.flow_panel.add_component(self.mapbox_map)
      
