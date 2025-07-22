from ._anvil_designer import DataDashboardTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from tabulator.Tabulator import Tabulator
from .. import utils

class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    ## User Login Prompt
    anvil.users.login_with_form()
    ## Init query
    query = """
    SELECT LAT, LON, Address FROM `real-estate-data-processing.DataLists.AbsenteeOwners` LIMIT 100
    """

    # ---- Dataset Selection Dropdowns ----
    self.dataset_select.items = utils.get_dataset_dict()
    self.county_select.items = utils.get_county_dict()
    self.city_select.items = utils.get_city_dict()
    
    # ---- Mapbox Map ----
    # Add access token and center map on Denver
    token = "pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw"
    self.mapbox_map.layout.mapbox = dict(accesstoken=token, center=dict(lat=39.747508, lon=-104.987833), zoom=8)
    self.mapbox_map.layout.margin = dict(t=0, b=0, l=0, r=0)
    # Add title to map and pull data to display
    self.mapbox_map.data = anvil.server.call('get_map_data', query)
    self.mapbox_map.config = {'scrollZoom': True}
    
    # ---- Tabulator Data Table ----
    self.tabulator.data = anvil.server.call('get_table_data', query)
    
    keys_list = list(self.tabulator.data[0].keys())
    
    self.data_select_panel.visible = True

    # ---- Tabulator Data Table Filter ----
    self.fields_dropdown.items = keys_list
    self.type_dropdown.items = ['>','<','>=','<=','like','!=']
  
  def select_data_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Flip visibility
    self.data_select_panel.visible = not self.data_select_panel.visible

  def pull_data_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    if not self.dataset_select.selected:
      alert('Please select a dataset')
    else:
      query = f"""
      SELECT LAT, LON, Address FROM `real-estate-data-processing.DataLists.{self.dataset_select.selected[0]}`
      """
      ## County if statement
      if not self.county_select.selected:
        county_where_query = ''
      else: 
        county_where_query = f'WHERE County {utils.list_to_in_phrase(self.county_select.selected)}'
      ## City if statement
      if not self.city_select.selected:
        city_where_query = ''
      elif county_where_query == '':
        city_where_query =  f'WHERE City {utils.list_to_in_phrase(self.city_select.selected)}'
      else:
        city_where_query = f'AND City {utils.list_to_in_phrase(self.city_select.selected)}'
      ## Construct full query
      query = query + county_where_query + city_where_query
      print(query)
      self.mapbox_map.data = anvil.server.call('get_map_data', query)
      self.tabulator.data = anvil.server.call('get_table_data', query)

  def filter_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    field = self.fields_dropdown.selected_value
    symbol = self.type_dropdown.selected_value
    value = self.value_box.text
    # print(field, symbol, value)

    self.tabulator.set_filter(field, symbol, value)
    pass

  def reset_filter_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.tabulator.clear_filter()
    self.value_box.text = ""

  # def mapbox_map_click(self, points, **event_args):
  #   """This method is called when a data point is clicked."""
  #   if points:
  #     # 'points' is a list of dictionaries, each representing a clicked point.
  #     # For Mapbox maps, each dictionary typically contains 'lat' and 'lon' keys.
  #     clicked_point = points[0]
  #     print(clicked_point)

  def mapbox_map_click(self, points, **event_args):
    if points:
      clicked_point = points[0]
      address = clicked_point.get('customdata')  # Now should work
      print(clicked_point)
      print(f"Clicked address: {address}")
    