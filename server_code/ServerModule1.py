import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.secrets
import anvil.server
import pandas as pd
import plotly.graph_objects as go
# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
def get_property_data(query: str):
  df = anvil.server.call('get_bigquery_data', query)
  df = pd.DataFrame.from_dict(df)
  return df

# @anvil.server.callable
# def get_map_data(query: str):
#   df = get_property_data(query)
#   map_data = go.Scattermapbox(lat=df['LAT'], lon=df['LON'], mode='markers', text=df['Address'], hoverinfo='text', customdata=df[['Address']])
#   return map_data

@anvil.server.callable
def get_map_data(query: str):
  df = get_property_data(query)

  # Create mapping: (lat, lon) → address
  lookup_dict = {
    (round(row['LAT'], 6), round(row['LON'], 6)): row['Address']
    for _, row in df.iterrows()
  }

  map_data = go.Scattermapbox(
    lat=df['LAT'],
    lon=df['LON'],
    mode='markers',
    text=df['Address'],  # still shows on hover
    hoverinfo='text',
    marker=dict(size=10)
  )

  return {'figure': map_data, 'lookup': lookup_dict}

@anvil.server.callable
def get_table_data(query):
  df = get_property_data(query)
  records = df.to_dict(orient="records")
  return records
