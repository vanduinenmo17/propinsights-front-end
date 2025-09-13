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
  """
    Build a BigQuery SELECT with required dataset+county and optional city filter.
    - dataset: list with the chosen dataset name at [0]
    - county: list of one or more county names (REQUIRED)
    - city: list of 0+ city names (optional). Empty/None -> all cities (no city filter)
    """
  # Validate required inputs
  if not dataset or not dataset[0]:
    raise ValueError("You must select a dataset.")
  if not county:
    raise ValueError("You must select at least one county.")

  select_sql = list_to_select_phrase(DATA_LIST_COLUMNS)
  table_sql = f"`real-estate-data-processing.DataLists.{dataset[0]}`"

  # Always filter by county
  where_clauses = [f"County {list_to_in_phrase(county)}"]

  # Add city filter only if provided (non-empty)
  if city:
    where_clauses.append(f"City {list_to_in_phrase(city)}")

  where_sql = " WHERE " + " AND ".join(where_clauses)
  query = f"{select_sql} FROM {table_sql}{where_sql}"
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