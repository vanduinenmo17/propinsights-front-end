from ._anvil_designer import DataDashboardTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
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
    # # Call and unpack result
    # map_result = anvil.server.call('get_map_data', query)
    # # Assign full figure to the Plot component
    # self.mapbox_map.figure = map_result['figure']
    # # Save lookup dictionary
    # self.latlon_to_address = map_result['lookup']
    # self.mapbox_map.config = {'scrollZoom': True}
    
    self.mapbox_map.figure, self.latlon_to_address, self.mapbox_map.config = utils.get_map_data(query)
    
    # ---- Tabulator Data Table ----
    self.tabulator.data = anvil.server.call('get_table_data', query)
    
    keys_list = list(self.tabulator.data[0].keys())
    
    self.data_select_panel.visible = True

    # ---- Tabulator Data Table Filter ----
    self.fields_dropdown.items = keys_list
    self.type_dropdown.items = ['=','>','<','>=','<=','like','!=']
  
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
      self.mapbox_map.figure, self.latlon_to_address, self.mapbox_map.config = utils.get_map_data(query)
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

  def mapbox_map_click(self, points, **event_args):
    """This method is called when a data point is clicked on the map."""
    if points:
      clicked_point = points[0]

      # Get lat/lon and round to 6 decimals for consistency with lookup keys
      lat = round(clicked_point['lat'], 6)
      lon = round(clicked_point['lon'], 6)
      key = f"{lat},{lon}"

      # Look up the address from the prebuilt dictionary
      address = self.latlon_to_address.get(key, "Unknown address")
      print(f"Clicked address: {address}")

      self.tabulator.set_filter('Address', '=', address)