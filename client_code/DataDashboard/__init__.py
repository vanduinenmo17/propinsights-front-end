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
from anvil.js.window import setTimeout
from tabulator.Tabulator import Tabulator
from anvil import media
from .. import utils
from .. import user_ui
import plotly.graph_objects as go
import math

class DataDashboard(DataDashboardTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    user_ui.init_header(self)

    # Polling timer (programmatic)
    self.task_timer = Timer(interval=0)
    self.task_timer.set_event_handler('tick', self.task_timer_tick)
    self.dashboard_panel.add_component(self.task_timer)

    # Download menu
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

    # Table options (we page on the server; keep client pagination off)
    self.tabulator.options = {
      "pagination": False,
      "layout": "fitData",
      "height": "520px",
      "columnDefaults": {"resizable": True},
    }
    self.cols = [{
      "title": "LastSalesDate",
      "field": "LastSalesDate",
      "formatter": "luxon_datetime",
      "formatter_params": {"inputFormat": "iso", "outputFormat": "yyyy-LL-dd"}
    }]
    self.tabulator.columns = self.cols

    # Minimal pager UI
    self.pager_row = FlowPanel()
    self.btn_prev = Button(text="‹ Prev", enabled=False, role="outlined-button")
    self.lbl_page = Label(text="Page – of –")
    self.btn_next = Button(text="Next ›", enabled=False, role="filled-button")
    self.btn_prev.set_event_handler("click", self._prev_page_click)
    self.btn_next.set_event_handler("click", self._next_page_click)
    self.pager_row.add_component(self.btn_prev)
    self.pager_row.add_component(self.lbl_page)
    self.pager_row.add_component(self.btn_next)
    self.dashboard_panel.add_component(self.pager_row)

    # Hidden until user pulls data
    self.dashboard_panel.visible = False

    # Dataset selection
    self.dataset_select.items = utils.get_dataset_dict()
    self.county_select.items = utils.get_county_dict()
    self.city_select.items = utils.get_city_dict()
    self.data_select_panel.visible = True

    # Client-side filter (affects current page only)
    self.type_dropdown.items = ['=','>','<','>=','<=','like','!=']

    # State
    self._load_task = None
    self._result_id = None
    self._page_size = 1000
    self._current_page = 1
    self._total_rows = 0
    self.latlon_to_address = {}
    self._fields_populated = False
    self._clustered_map_mode = False

  # ---------------- UI events ----------------
  def select_data_button_click(self, **event_args):
    self.data_select_panel.visible = not self.data_select_panel.visible

  def pull_data_button_click(self, **event_args):
    self.pull_data_button.enabled = False
    try:
      user = anvil.users.get_user()
      if not user:
        user = user_ui.login_with_form_and_refresh(allow_cancel=True)
        if not user:
          return

      if not self.dataset_select.selected:
        alert('Please select a dataset')
        return
      if not self.county_select.selected:
        alert('Please select a county')
        return

      query = utils.build_query(
        self.dataset_select.selected,
        self.county_select.selected,
        self.city_select.selected
      )

      self.dashboard_panel.visible = True

      # Start the staging task (server launches @background_task)
      self._load_task = anvil.server.call('start_long_load', query)
      self.task_timer.interval = 1.0   # poll once per second
    finally:
      if not self.task_timer.interval:
        self.pull_data_button.enabled = True

  def task_timer_tick(self, **event_args):
    task = getattr(self, "_load_task", None)
    if task is None:
      self.task_timer.interval = 0
      self.pull_data_button.enabled = True
      return

    state = task.get_state()
    if state == 'running':
      return

    if state == 'failed':
      self.task_timer.interval = 0
      err = task.get_error() or "Background task failed."
      self._load_task = None
      alert(f"Data preparation failed:\n{err}")
      self.pull_data_button.enabled = True
      return

    result = task.get_return_value()
    if result is None:
      return  # not yet materialised (per docs)

    # Success: stash ids/meta and draw first page
    self.task_timer.interval = 0
    self._load_task = None

    self._result_id = result.get('result_id')
    self._total_rows = int(result.get('row_count') or 0)
    self._fields_populated = False
    self._current_page = 1

    # NEW: fetch & render clustered map for ALL points (capped by server)
    clustered_fig = anvil.server.call('get_clustered_map', self._result_id)
    def _apply_clustered():
      self.mapbox_map.config = {'scrollZoom': True}
      self.mapbox_map.figure = clustered_fig
      self._clustered_map_mode = True
      
    setTimeout(_apply_clustered, 50)
    
    self._load_page(self._current_page)
    self.pull_data_button.enabled = True

  def filter_button_click(self, **event_args):
    # This filters only the rows currently in the table (one page).
    field = self.fields_dropdown.selected_value
    symbol = self.type_dropdown.selected_value
    value = self.value_box.text
    self.tabulator.set_filter(field, symbol, value)

  def reset_filter_button_click(self, **event_args):
    self.tabulator.clear_filter()
    self.value_box.text = ""

  def mapbox_map_click(self, points, **event_args):
    # With "basic" wiring we plot only the current page of points.
    if points:
      pt = points[0]
      # If the user clicked a single marker, 'text' holds the address.
      # If they clicked a cluster bubble, 'text' may be None/empty.
      address = pt.get('text')
      if address:
        self.tabulator.set_filter('Address', '=', address)

  # Downloads (unchanged)
  def download_csv(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: 
        return
    if self._result_id:
      media_obj = anvil.server.call('export_csv', result_id=self._result_id, filename="data.csv")
    else:
      # fallback (will query once on the server)
      q = self._ensure_query()
      media_obj = anvil.server.call('export_csv', query=q, filename="data.csv")
    anvil.media.download(media_obj)

  def download_excel(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: 
        return
    if self._result_id:
      media_obj = anvil.server.call('export_excel', result_id=self._result_id, filename="data.xlsx")
    else:
      q = self._ensure_query()
      media_obj = anvil.server.call('export_excel', query=q, filename="data.xlsx")
    anvil.media.download(media_obj)

  def download_json(self, **event_args):
    user = anvil.users.get_user()
    if not user:
      user = user_ui.login_with_form_and_refresh(allow_cancel=True)
      if not user: 
        return
    if self._result_id:
      media_obj = anvil.server.call('export_json', result_id=self._result_id, filename="data.json")
    else:
      q = self._ensure_query()
      media_obj = anvil.server.call('export_json', query=q, filename="data.json")
    anvil.media.download(media_obj)

  # --------------- helpers ----------------
  def _ensure_query(self):
    # helper to reuse your existing widgets → SQL builder
    return utils.build_query(self.dataset_select.selected,
                            self.county_select.selected,
                            self.city_select.selected)
    
  def _load_page(self, page:int):
    """Fetch one page from the staged Parquet and render table + map."""
    if not self._result_id:
      return
    out = anvil.server.call('get_result_page', self._result_id, page, self._page_size)
    rows = out.get("rows", [])
    self._total_rows = int(out.get("row_count", self._total_rows) or 0)

    # set columns dropdown once
    if rows and not self._fields_populated:
      self.fields_dropdown.items = list(rows[0].keys())
      self._fields_populated = True

    # table
    self.tabulator.replace_data(rows)
    self.tabulator.data = rows
    self.tabulator.redraw(True)

    # If we’re showing the global clustered map, don’t overwrite it
    if not self._clustered_map_mode:
      self._render_map_from_rows(rows)

    # pager
    self._current_page = page
    self._update_pager()

  def _render_map_from_rows(self, rows):
    # Build lookup for current page (for click-to-filter)
    self.latlon_to_address = {}
    lats, lons, texts = [], [], []
    for r in rows:
      if r.get('LAT') is None or r.get('LON') is None:
        continue
      lat = round(float(r['LAT']), 6)
      lon = round(float(r['LON']), 6)
      lats.append(lat)
      lons.append(lon)
      texts.append(r.get('Address') or '')
      self.latlon_to_address[f"{lat},{lon}"] = r.get('Address') or ''

    trace = go.Scattermapbox(
      lat=lats, lon=lons, mode='markers',
      text=texts, hoverinfo='text', marker=dict(size=10)
    )
    layout = go.Layout(
      mapbox=dict(
        accesstoken="pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw",
        center=dict(lat=39.747508, lon=-104.987833),
        zoom=8, style="open-street-map"
      ),
      margin=dict(t=0, b=0, l=0, r=0)
    )
    self.mapbox_map.config = {'scrollZoom': True}
    self.mapbox_map.figure = go.Figure(data=[trace], layout=layout)

  def _update_pager(self):
    total_pages = max(1, (self._total_rows + self._page_size - 1) // self._page_size)
    self.lbl_page.text = f"Page {self._current_page:,} of {total_pages:,}"
    self.btn_prev.enabled = self._current_page > 1
    self.btn_next.enabled = self._current_page < total_pages

  def _prev_page_click(self, **event_args):
    if self._current_page > 1:
      self._load_page(self._current_page - 1)

  def _next_page_click(self, **event_args):
    total_pages = max(1, (self._total_rows + self._page_size - 1) // self._page_size)
    if self._current_page < total_pages:
      self._load_page(self._current_page + 1)

  # tidy up staged media when leaving
  def form_hide(self, **event_args):
    rid = getattr(self, "_result_id", None)
    if rid:
      try:
        anvil.server.call('delete_result', rid)
      except Exception:
        pass
