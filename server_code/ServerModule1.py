import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.secrets
import anvil.server
import io, uuid, datetime as dt
import pandas as pd

# --- Expectation: Uplink provides `get_bigquery_media(query)` that returns a Parquet as an Anvil Media object.

@anvil.server.background_task
def bg_prepare_result(query: str):
  """Ask Uplink for a Parquet Media of the full result, record it in a temp table, return ids+meta."""
  media = anvil.server.call('get_bigquery_media', query)  # <-- from your Uplink
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)
    row_count = len(df)
    cols = list(df.columns)

  rid = str(uuid.uuid4())
  app_tables.tmp_results.add_row(
    result_id=rid, media=media, row_count=row_count, columns=cols, created=dt.datetime.utcnow()
  )
  return {"result_id": rid, "row_count": row_count, "columns": cols}

@anvil.server.callable
def get_result_page(result_id: str, page: int, page_size: int = 1000):
  """Read a page from staged Parquet and return just that slice as rows."""
  row = app_tables.tmp_results.get(result_id=result_id)
  if not row:
    raise Exception("Result expired or not found")

  start, end = max(0, (page-1)*page_size), (page-1)*page_size + page_size
  with anvil.media.TempFile(row['media']) as tmp:
    df = pd.read_parquet(tmp)
    page_df = df.iloc[start:end].copy()

  # normalize dates to ISO if needed:
  if 'LastSalesDate' in page_df.columns:
    s = pd.to_datetime(page_df['LastSalesDate'], utc=True, errors='coerce')
    page_df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')

  return {"columns": row['columns'], "rows": page_df.to_dict(orient="records"), "row_count": row['row_count']}

@anvil.server.callable
def delete_result(result_id: str):
  row = app_tables.tmp_results.get(result_id=result_id)
  if row:
    row.delete()

# CHANGED: start the *prepare* task (staging) instead of building one giant bundle
@anvil.server.callable
def start_long_load(query: str):
  """Launch the staging Background Task and return the Task object (client will poll it)."""
  task = anvil.server.launch_background_task('bg_prepare_result', query)
  return task
