from ._anvil_designer import DataDashboardTemplate
from anvil import *
import plotly.graph_objects as go
import anvil.server
from ..AgGridForm import AgGridForm

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

    # ---- Tabulator block ----
    demo_data = [{'car': True, 'name': 'Elizabeth Maureen', 'dob': datetime.date(1974, 10, 25), 'col': 'blue', 'id': 0, 'gender': 'female', 'progress': 80, 'media': <anvil.BlobMedia object>, 'rating': 4}, {'car': True, 'name': 'Amira Grace', 'dob': datetime.date(2002, 7, 26), 'col': 'yellow', 'id': 1, 'gender': 'female', 'progress': 30, 'media': <anvil.BlobMedia object>, 'rating': 3}, {'car': False, 'name': 'Aaron Kathleen', 'dob': datetime.date(2001, 7, 1), 'col': 'red', 'id': 2, 'gender': 'male', 'progress': 98, 'media': <anvil.BlobMedia object>, 'rating': 4}, {'car': False, 'name': 'Roland Mary', 'dob': datetime.date(2004, 9, 3), 'col': 'green', 'id': 3, 'gender': 'male', 'progress': 44, 'media': <anvil.BlobMedia object>, 'rating': 0}, {'car': False, 'name': 'Chris Susan', 'dob': datetime.date(1967, 5, 3), 'col': 'blue', 'id': 4, 'gender': 'male', 'progress': 9, 'media': <anvil.BlobMedia object>, 'rating': 2}]
    