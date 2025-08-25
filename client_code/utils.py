import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
# This is a module.
# You can define variables and functions here, and use them from any form. For example, in a top-level form:
#
#    from .. import Module1
#
#    Module1.say_hello()
#

def list_to_in_phrase(lst: list, with_quotes: bool = True) -> str:
  """
    Converts string list into a sql "IN (...)" phrase
    Args: lst (list): items to convert
          with_quotes (bool, optional): whether to quote the items. Defaults to true
    Returns: str: "IN (...)" phrase
    """
  if with_quotes:
    quoted = [f"'{p}'" for p in lst]
  else:
    quoted = [f"{p}" for p in lst]
  return f" IN ({', '.join(quoted)}) "

def get_dataset_dict():
  dict = [
    {"key": "Absentee Owners", "value": "AbsenteeOwners"}
  ]
  return dict

def get_county_dict():
  dict = [
    {"key": "Adams", "value": "Adams"}
  ]
  return dict

def get_city_dict():
  dict = [
    {"key": "Thornton", "value": "THORNTON"},
    {"key": "Westminster", "value": "WESTMINSTER"},
    {"key": "Bennett", "value": "BENNETT"},
    {"key": "Commerce City", "value": "COMMERCE CITY"},
    {"key": "Brighton", "value": "BRIGHTON"},
    {"key": "Federal Heights", "value": "FEDERAL HEIGHTS"},
    {"key": "Aurora", "value": "AURORA"},
    {"key": "Northglenn", "value": "NORTHGLENN"},
    {"key": "Arvada", "value": "ARVADA"},
    {"key": "Lochbuie", "value": "LOCHBUIE"},
  ]
  return dict

def build_query(dataset: list, county: list, city: list):
  query = f"""
      SELECT * FROM `real-estate-data-processing.DataLists.{dataset[0]}`
      """
  ## County if statement
  if not city:
    county_where_query = ''
  else: 
    county_where_query = f'WHERE County {list_to_in_phrase(county)}'
    ## City if statement
    if not city:
      city_where_query = ''
    elif county_where_query == '':
      city_where_query =  f'WHERE City {list_to_in_phrase(city)}'
    else:
      city_where_query = f'AND City {list_to_in_phrase(city)}'
      ## Construct full query
  query = query + county_where_query + city_where_query
  return query

def get_map_data(query: str):
  # Call and unpack result
  map_result = anvil.server.call('get_map_data', query)
  # Assign full figure to the Plot component
  figure = map_result['figure']
  # Save lookup dictionary
  latlon_to_address = map_result['lookup']
  config = {'scrollZoom': True}
  return figure, latlon_to_address, config
