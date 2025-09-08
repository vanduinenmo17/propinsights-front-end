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
from .. import user_ui
# NOTE: removed setTimeout; not used with background tasks

class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Refresh User Account/Login button every time page is opened
    user_ui.init_header(self)

    self.task_timer = Timer(interval=0)
    self.task_timer.set_event_handler('tick', self.task_timer_tick)
    self.dashboard_panel.add_component(self.task_timer)
    
    # Download menu setup
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

    # Tabulator options
    self.tabulator.options = {
      "pagination": True,
      "paginationSize": 25,
      "paginationSizeSelector": [10, 25, 50, 100, True],
      "layout": "fitData",
      "height": "520px",
      "columnDefaults": {"resizable": True},
    }
    self.cols = [
      {
        "title": "LastSalesDate",
        "field": "LastSalesDate",
        "formatter": "luxon_datetime",
        "formatter_params": {"inputFormat": "iso", "outputFormat": "yyyy-LL-dd"}
      }
    ]
    self.tabulator.columns = self.cols

    # Hidden until user pulls data
    self.dashboard_panel.visible = False

    # Dataset selection
    self.dataset_select.items = utils.get_dataset_dict()
    self.county_select.items = utils.get_county_dict()
    self.city_select.items = utils.get_city_dict()
    self.data_select_panel.visible = True

    # Table filter dropdown
    self.type_dropdown.items = ['=','>','<','>=','<=','like','!=']

    # Holds the running background Task object
    self._load_task = None

  def select_data_button_click(self, **event_args):
    self.data_select_panel.visible = not self.data_select_panel.visible

  def pull_data_button_click(self, **event_args):
    # Ensure user is logged in
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user:
        return

    if not self.dataset_select.selected:
      alert('Please select a dataset'); return
    if not self.county_select.selected:
      alert('Please select a county'); return

    query = utils.build_query(
      self.dataset_select.selected,
      self.county_select.selected,
      self.city_select.selected
    )

    # Show the dashboard shell immediately
    self.dashboard_panel.visible = True

    # -- IMPORTANT --
    # Launch the background task from a *server callable* and
    # get a task_id back. Then get a Task handle on the client.
    self._load_task = anvil.server.call('start_long_load', query)
    # Start polling once per second
    self.task_timer.interval = 1.0

  def task_timer_tick(self, **event_args):
    if not self._load_task:
      self.task_timer.interval = 0
      return
  
    # Use state or (if available in your runtime) termination status.
    state = self._load_task.get_state()  # 'running' | 'completed' | 'failed'
  
    if state == 'running':
      # still working - keep polling
      return
  
    if state == 'failed':
      # stop polling and surface error
      self.task_timer.interval = 0
      msg = self._load_task.get_error() or "Background task failed."
      alert(f"Data load failed:\n{msg}")
      self._load_task = None
      return
  
    # state == 'completed' (or anything that's not running/failed)
    # It's possible get_return_value() is not ready yet; guard it
    result = self._load_task.get_return_value()
    if result is None:
      # Task reports completed but the value isn't materialized yet – keep polling
      return
  
    # We have a real result: now stop polling
    self.task_timer.interval = 0
    self._load_task = None
  
    # Map
    self.latlon_to_address = result.get('lookup', {})
    self.mapbox_map.config = {'scrollZoom': True}
    self.mapbox_map.figure = result.get('figure')
  
    # Table
    data = result.get('records', [])
    self.tabulator.replace_data(data)
    self.tabulator.data = data
    self.tabulator.redraw(True)
  
    # Filter dropdown fields
    if data:
      self.fields_dropdown.items = list(data[0].keys())
  
      state = self._load_task.get_state()  # 'running' | 'completed' | 'failed'
  
      if state == 'running':
        # Optional progress: if you later add a Label named progress_label, you can uncomment:
        # prog = self._load_task.get_progress() or {}
        # stage = prog.get('stage')
        # if stage:
        #   self.progress_label.text = f"Loading… {stage}"
        return
  
      # Stop polling
      self.task_timer.interval = 0
  
      if state == 'failed':
        msg = self._load_task.get_error() or "Background task failed."
        alert(f"Data load failed:\n{msg}")
        self._load_task = None
        return
  
      # Completed: get the result bundle and render
      result = self._load_task.get_return_value()
      self._load_task = None
  
      # Map
      self.latlon_to_address = result.get('lookup', {})
      self.mapbox_map.config = {'scrollZoom': True}
      self.mapbox_map.figure = result.get('figure')
  
      # Table
      data = result.get('records', [])
      self.tabulator.replace_data(data)
      self.tabulator.data = data
      self.tabulator.redraw(True)
  
      # Filter dropdown fields
      if data:
        self.fields_dropdown.items = list(data[0].keys())

  def filter_button_click(self, **event_args):
    field = self.fields_dropdown.selected_value
    symbol = self.type_dropdown.selected_value
    value = self.value_box.text
    self.tabulator.set_filter(field, symbol, value)

  def reset_filter_button_click(self, **event_args):
    self.tabulator.clear_filter()
    self.value_box.text = ""

  def mapbox_map_click(self, points, **event_args):
    if points:
      clicked_point = points[0]
      lat = round(clicked_point['lat'], 6)
      lon = round(clicked_point['lon'], 6)
      key = f"{lat},{lon}"
      address = self.latlon_to_address.get(key, "Unknown address")
      self.tabulator.set_filter('Address', '=', address)

  def download_csv(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: return
    if not self.dataset_select.selected:
      alert('Please select a dataset'); return
    if not self.county_select.selected:
      alert('Please select a county'); return
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    csv_media = anvil.server.call('export_csv', query)
    anvil.media.download(csv_media)

  def download_excel(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: return
    if not self.dataset_select.selected:
      alert('Please select a dataset'); return
    if not self.county_select.selected:
      alert('Please select a county'); return
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    excel_media = anvil.server.call('export_excel', query)
    anvil.media.download(excel_media)

  def download_json(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: return
    if not self.dataset_select.selected:
      alert('Please select a dataset'); return
    if not self.county_select.selected:
      alert('Please select a county'); return
    query = utils.build_query(self.dataset_select.selected, self.county_select.selected, self.city_select.selected)
    json_media = anvil.server.call('export_json', query)
    anvil.media.download(json_media)
