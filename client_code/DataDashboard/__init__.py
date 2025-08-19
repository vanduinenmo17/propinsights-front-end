from ._anvil_designer import DataDashboardTemplate
from anvil import *
import m3.components as m3
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from tabulator.Tabulator import Tabulator
from anvil import media
from .. import utils

class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    ## Check login status
    user = anvil.users.get_user()
    if user:
      pass
    else:
      anvil.users.login_with_form()
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    ## Initialize Download Data Button
    self.menu_item_download_csv = m3.MenuItem(text="CSV")
    self.menu_item_download_csv.add_event_handler("click", self.download_csv)
    self.btn_download_data.menu_items = [
      self.menu_item_download_csv
    ]
    ## Hide dashboard initially before user pulls any data
    self.dashboard_panel.visible = False

    # ---- Dataset Selection Dropdowns ----
    self.dataset_select.items = utils.get_dataset_dict()
    self.county_select.items = utils.get_county_dict()
    self.city_select.items = utils.get_city_dict()
    self.data_select_panel.visible = True

    # ---- Tabulator Data Table Filter ----
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
      self.dashboard_panel.visible = True
      ## Construct query
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
      # Defer plotting a tick so Mapbox can initialize
      anvil.timers.set_timeout(0.1, lambda: self._draw_map(query))
      self.tabulator.data = anvil.server.call('get_table_data', query)
      keys_list = list(self.tabulator.data[0].keys())
      self.fields_dropdown.items = keys_list

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

  def download_csv(self, **event_args):
    ## Construct query
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
    csv_media = anvil.server.call('export_csv', query)
    anvil.media.download(csv_media)

  def _draw_map(self, query):
    fig, self.latlon_to_address, cfg = utils.get_map_data(query)
    self.mapbox_map.config = cfg
    self.mapbox_map.figure = fig