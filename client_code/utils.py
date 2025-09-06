import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

DATA_LIST_COLUMNS = ['Address','City','County','State','OwnerName','OwnerAddress','OwnerCity','OwnerState',
                     'OwnerZip','BuildingDescription','SF','Bedrooms','Bathrooms','YearBuilt','AssessedValue',
                     'LastSalesPrice','LastSalesDate','LAT','LON']

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

def list_to_select_phrase(lst: list, with_quotes: bool = False) -> str:
  """
  Converts string list into a sql "SELECT ..." phrase
  Args: lst (list): items to convert
        with_quotes (bool, optional): whether to quote the items. Defaults to true
  Returns: str: "SELECT ..." phrase
  """
  if with_quotes:
    quoted = [f"'{p}'" for p in lst]
  else:
    quoted = [f"{p}" for p in lst]
  return f" SELECT {', '.join(quoted)} "

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
      {list_to_select_phrase(DATA_LIST_COLUMNS)} FROM `real-estate-data-processing.DataLists.{dataset[0]}`
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
  print(query)
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
