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
from anvil.js.window import setTimeout

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
    self.menu_item_download_excel = m3.MenuItem(text="XLSX")
    self.menu_item_download_excel.add_event_handler("click", self.download_excel)
    self.menu_item_download_json = m3.MenuItem(text="JSON")
    self.menu_item_download_json.add_event_handler("click", self.download_json)
    self.btn_download_data.menu_items = [
      self.menu_item_download_csv,
      self.menu_item_download_excel,
      self.menu_item_download_json
    ]

    ## Tabulator table options
    self.tabulator.options = {
      'layout': 'fitData',
      "columnDefaults": {"resizable": True}
    }
    self.cols = [
    {
      "title": "LastSalesDate",
      "field": "LastSalesDate",
      "sorter": "datetime",
      "formatter": "datetime",
      "formatter_params": { "format": "%Y-%m-%d" }
    }]
    self.tabulator.columns = self.cols
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
      
      ## Construct query
      query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
      self.dashboard_panel.visible = True
      def later():
        fig, self.latlon_to_address, cfg = utils.get_map_data(query)
        self.mapbox_map.config = cfg or {}
        self.mapbox_map.figure = fig
        #Load table after the figure to reduce contention
        data = anvil.server.call('get_table_data', query)
        self.tabulator.replace_data(data)
        self.tabulator.data = data
        self.tabulator.redraw(True)
        if data:
          self.fields_dropdown.items = list(data[0].keys())
      setTimeout(later, 100)

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
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    csv_media = anvil.server.call('export_csv', query)
    anvil.media.download(csv_media)

  def download_excel(self, **event_args):
    ## Construct query
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    excel_media = anvil.server.call('export_excel', query)
    anvil.media.download(excel_media)

  def download_json(self, **event_args):
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    json_media = anvil.server.call('export_json', query)
    anvil.media.download(json_media)