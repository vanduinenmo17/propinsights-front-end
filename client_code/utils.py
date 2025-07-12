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
