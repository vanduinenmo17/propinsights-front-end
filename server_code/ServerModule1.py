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
# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
def get_property_data(query: str):
  df = anvil.server.call('get_bigquery_data', query)
  df = pd.DataFrame.from_dict(df)
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
      # style="streets"
      style = "open-street-map"
    ),
    margin=dict(t=0, b=0, l=0, r=0)
  )

  fig = go.Figure(data=[trace], layout=layout)

  return {'figure': fig, 'lookup': lookup_dict}

@anvil.server.callable
def get_table_data(query):
  df = get_property_data(query)
  print(df['LastSalesDate'])
  print(df.dtypes)
  s = pd.to_datetime(df['LastSalesDate'], utc=True, errors='coerce')
  df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')  # or '%Y-%m-%d'
  print(df.dtypes)
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
  blob = anvil.BlobMedia(content=excel_buffer.read(), content_type="application/vnd.ms-excel", name='data.xlsx')
  return blob

@anvil.server.callable
def export_json(query):
  df = get_property_data(query)
  json_string = df.to_json(orient='records', indent=2)
  blob = anvil.BlobMedia('application/json', json_string.encode('utf-8'), name='data.json')
  return blob

# NEW: background task that does all heavy work off the 30s call path
@anvil.server.background_task
def bg_build_map_and_table(query: str):
  # Optional progress breadcrumbs users can see from the client
  anvil.server.task_state['stage'] = 'querying BigQuery via Uplink'

  # Call your existing Uplink function (runs on your GCE VM)
  df_records = anvil.server.call('get_bigquery_data', query)
  df = pd.DataFrame.from_dict(df_records)

  anvil.server.task_state['stage'] = 'formatting dataframe'
  # Fix LastSalesDate to ISO yyyy-mm-dd strings (keeps Tabulator happy)
  if 'LastSalesDate' in df.columns:
    s = pd.to_datetime(df['LastSalesDate'], utc=True, errors='coerce')
    df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')

  # Build the lookup dict for quick “click-to-filter” by address
  anvil.server.task_state['stage'] = 'building map'
  lookup_dict = {}
  if {'LAT','LON','Address'}.issubset(df.columns):
    lookup_dict = {
      f"{round(row['LAT'], 6)},{round(row['LON'], 6)}": row['Address']
      for _, row in df.iterrows()
    }

  # Plotly Mapbox figure (same as your current get_map_data)
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

  # Return a single bundle: figure, lookup, and table rows
  return {
    "figure": fig,
    "lookup": lookup_dict,
    "records": records,
  }