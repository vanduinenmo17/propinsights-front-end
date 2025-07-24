import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
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
      style="streets"
    ),
    margin=dict(t=0, b=0, l=0, r=0)
  )

  fig = go.Figure(data=[trace], layout=layout)

  return {'figure': fig, 'lookup': lookup_dict}

@anvil.server.callable
def get_table_data(query):
  df = get_property_data(query)
  records = df.to_dict(orient="records")
  return records
