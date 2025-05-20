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
