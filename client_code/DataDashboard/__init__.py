from ._anvil_designer import DataDashboardTemplate
from anvil import *
import plotly.graph_objects as go
import anvil.server


class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    
    ## Initialize Map
    # Add access token and center map on Denver
    token = "pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw"
    self.mapbox_map.layout.mapbox = dict(accesstoken=token, center=dict(lat=39.747508, lon=-104.987833), zoom=8)
    self.mapbox_map.layout.margin = dict(t=0, b=0, l=0, r=0)
    # Add title to map and pull data to display
    self.mapbox_map.data = anvil.server.call('get_map_data')

    ## Initialize data table
    # Fetch the list-of-dicts from the server...
    props = anvil.server.call("get_table_data")
    # …and hand it straight to the RepeatingPanel:
    self.repeating_panel_1.items = props
    