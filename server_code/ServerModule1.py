import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.secrets
import anvil.server
import io
import pandas as pd
import plotly.graph_objects as go
import datetime as dt

# Helper: fetch DataFrame via Uplink
def get_property_data(query: str):
  df_records = anvil.server.call('get_bigquery_data', query)  # uplink call (GCE VM)
  df = pd.DataFrame.from_dict(df_records)
  return df

@anvil.server.callable
def get_map_data(query: str):
  df = get_property_data(query)

  # Create lookup dict with string keys
  lookup_dict = {
    f"{round(row['LAT'], 6)},{round(row['LON'], 6)}": row['Address']
    for _, row in df.iterrows()
  }

  # Build full Plotly Mapbox Map figure
  trace = go.Scattermapbox(
    lat=df['LAT'],
    lon=df['LON'],
    mode='markers',
    text=df['Address'],
    hoverinfo='text',
    marker=dict(size=10)
  )

  layout = go.Layout(
    mapbox=dict(
      accesstoken="pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw",
      center=dict(lat=39.747508, lon=-104.987833),
      zoom=8,
      style="open-street-map"
    ),
    margin=dict(t=0, b=0, l=0, r=0)
  )

  fig = go.Figure(data=[trace], layout=layout)
  return {'figure': fig, 'lookup': lookup_dict}

@anvil.server.callable
def get_table_data(query):
  df = get_property_data(query)
  s = pd.to_datetime(df['LastSalesDate'], utc=True, errors='coerce')
  df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')  # or '%Y-%m-%d'
  records = df.to_dict(orient="records")
  return records

@anvil.server.callable
def export_csv(query):
  df = get_property_data(query)
  csv_text = df.to_csv(index=False)
  blob = anvil.BlobMedia("text/csv", csv_text.encode("utf-8"), name="data.csv")
  return blob

@anvil.server.callable
def export_excel(query):
  df = get_property_data(query)
  excel_buffer = io.BytesIO()
  df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
  excel_buffer.seek(0)
  blob = anvil.BlobMedia(content=excel_buffer.read(),
                         content_type="application/vnd.ms-excel",
                         name='data.xlsx')
  return blob

@anvil.server.callable
def export_json(query):
  df = get_property_data(query)
  json_string = df.to_json(orient='records', indent=2)
  blob = anvil.BlobMedia('application/json', json_string.encode('utf-8'), name='data.json')
  return blob

# --- NEW: Background Task to do the heavy work off the 30s call path ---
@anvil.server.background_task
def bg_build_map_and_table(query: str):
  # progress breadcrumb (optional)
  anvil.server.task_state['stage'] = 'querying BigQuery via Uplink'

  # Fetch via Uplink
  df_records = anvil.server.call('get_bigquery_data', query)
  df = pd.DataFrame.from_dict(df_records)

  # Format dates (for Tabulator)
  anvil.server.task_state['stage'] = 'formatting dataframe'
  if 'LastSalesDate' in df.columns:
    s = pd.to_datetime(df['LastSalesDate'], utc=True, errors='coerce')
    df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')

  # Build lookup
  anvil.server.task_state['stage'] = 'building map'
  lookup_dict = {}
  if {'LAT','LON','Address'}.issubset(df.columns):
    lookup_dict = {
      f"{round(row['LAT'], 6)},{round(row['LON'], 6)}": row['Address']
      for _, row in df.iterrows()
    }

  # Plotly Mapbox figure
  trace = go.Scattermapbox(
    lat=df['LAT'] if 'LAT' in df else [],
    lon=df['LON'] if 'LON' in df else [],
    mode='markers',
    text=df['Address'] if 'Address' in df else [],
    hoverinfo='text',
    marker=dict(size=10),
  )
  layout = go.Layout(
    mapbox=dict(
      accesstoken="pk.eyJ1IjoidmFuZHVpbmVubW8xNyIsImEiOiJjbTkzMmg4OTIwaHZjMmpvamR2OXN1YWp1In0.SGzbF3O6SdZqfDsAsSoiaw",
      center=dict(lat=39.747508, lon=-104.987833),
      zoom=8,
      style="open-street-map",
    ),
    margin=dict(t=0, b=0, l=0, r=0),
  )
  fig = go.Figure(data=[trace], layout=layout)

  anvil.server.task_state['stage'] = 'serializing results'
  records = df.to_dict(orient="records")

  # Return a single bundle
  return {"figure": fig, "lookup": lookup_dict, "records": records}

# --- NEW: Server-callable that launches the background task (required) ---
@anvil.server.callable
def start_long_load(query: str) -> str:
  """
  Launch bg_build_map_and_table on the server and return its task_id.
  Tasks must be launched from server code, not client code.
  """
  task = anvil.server.launch_background_task('bg_build_map_and_table', query)
  return task   # ← return the Task object itself
