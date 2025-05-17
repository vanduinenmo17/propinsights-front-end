import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.secrets
import anvil.server

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
import pandas as pd
import plotly.graph_objects as go
# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
def get_absentee_owners_data():
  query = """
  SELECT LAT, LON, Address FROM `real-estate-data-processing.DataLists.AbsenteeOwners` LIMIT 5
  """
  df = anvil.server.call('get_bigquery_data', query)
  df = pd.DataFrame.from_dict(df)
  return df

@anvil.server.callable
def get_map_data():
  df = get_absentee_owners_data()
  map_data = go.Scattermapbox(lat=df['LAT'], lon=df['LON'], mode='markers')
  return map_data

@anvil.server.callable
def get_table_data():
  df = get_absentee_owners_data()
  records = df.to_dict(orient="records")
  return records
