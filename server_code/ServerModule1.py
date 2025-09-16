import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.secrets
import anvil.server
import anvil.media
import io, uuid, datetime as dt
import pandas as pd
import plotly.graph_objects as go

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
def get_clustered_map(result_id: str, max_points: int = 120_000):
  """
  Build a clustered Scattermapbox figure from the staged Parquet in tmp_results.
  Returns a Plotly Figure (sent to client).
  """
  row = app_tables.tmp_results.get(result_id=result_id)
  if not row:
    raise Exception("Result expired or not found")

  # Read just what we need; Parquet supports column projection (pyarrow)
  with anvil.media.TempFile(row['media']) as tmp:
    df = pd.read_parquet(tmp, columns=["LAT", "LON", "Address"])

  # Clean & (optional) cap to keep JSON size manageable
  df = df.dropna(subset=["LAT", "LON"])
  if len(df) > max_points:
    df = df.sample(n=max_points, random_state=0)

  # Build the trace
  trace = go.Scattermapbox(
    lat=df["LAT"],
    lon=df["LON"],
    mode="markers",
    text=df.get("Address", None),   # hover + we’ll use text for click-to-filter
    hoverinfo="text",
    marker=dict(size=9)
  )

  # Layout (use your token/center/zoom)
  layout = go.Layout(
    mapbox=dict(
      center=dict(lat=39.747508, lon=-104.987833),
      zoom=8,
      style="open-street-map",
    ),
    margin=dict(t=0, b=0, l=0, r=0),
  )
  fig = go.Figure(data=[trace], layout=layout)

  # 🔑 Enable clustering + (optional) styling
  fig.update_traces(
    cluster=dict(
      enabled=True,        # turn clustering ON
      size=28,             # cluster circle size (px)
      maxzoom=14,          # stop clustering beyond this zoom
      step=50              # threshold step for style changes (see Plotly ref)
    )
  )

  return fig

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
  
# --- exports ---------------------------------------------------------------
@anvil.server.callable
def export_csv(*, result_id=None, query=None, filename="data.csv"):
  media, _ = _resolve_media_for_export(result_id=result_id, query=query)
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)
  df = _normalize_dates(df)
  csv_bytes = df.to_csv(index=False).encode("utf-8")
  return anvil.BlobMedia("text/csv", csv_bytes, name=filename)  # client can anvil.media.download() :contentReference[oaicite:5]{index=5}

@anvil.server.callable
def export_excel(*, result_id=None, query=None, filename="data.xlsx"):
  media, _ = _resolve_media_for_export(result_id=result_id, query=query)
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)
  df = _normalize_dates(df)
  bio = io.BytesIO()
  with pd.ExcelWriter(bio, engine="xlsxwriter") as w:
    df.to_excel(w, index=False)
  bio.seek(0)
  # Official MIME for xlsx
  return anvil.BlobMedia(
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    bio.read(), name=filename
  )

@anvil.server.callable
def export_json(*, result_id=None, query=None, filename="data.json"):
  media, _ = _resolve_media_for_export(result_id=result_id, query=query)
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)
  df = _normalize_dates(df)
  js = df.to_json(orient="records", indent=2).encode("utf-8")
  return anvil.BlobMedia("application/json", js, name=filename)

# (optional) direct Parquet download of the staged file — fastest path
@anvil.server.callable
def export_parquet(*, result_id: str, filename="data.parquet"):
  row = app_tables.tmp_results.get(result_id=result_id)
  if not row:
    raise Exception("Result expired or not found")
  # Re-wrap to set a friendly filename in the download
  return anvil.BlobMedia("application/octet-stream", row['media'].get_bytes(), name=filename)
  
# --- helpers ---------------------------------------------------------------
def _resolve_media_for_export(*, result_id=None, query=None):
  """
  Return (media, columns) for an existing staged result (preferred),
  or run the Uplink once (fallback) if only query is provided.
  """
  if result_id:
    row = app_tables.tmp_results.get(result_id=result_id)
    if not row:
      raise Exception("Result expired or not found")
    return row['media'], row['columns']

  if query:
    # One-off: fetch directly from Uplink and infer columns
    media = anvil.server.call('get_bigquery_media', query)  # Uplink callable :contentReference[oaicite:3]{index=3}
    with anvil.media.TempFile(media) as tmp:
      df = pd.read_parquet(tmp)  # Parquet needs pyarrow/fastparquet installed in Anvil env :contentReference[oaicite:4]{index=4}
      cols = list(df.columns)
    return media, cols

  raise Exception("Provide result_id or query")

def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
  # Keep your table-friendly date format
  if 'LastSalesDate' in df.columns:
    s = pd.to_datetime(df['LastSalesDate'], utc=True, errors='coerce')
    df['LastSalesDate'] = s.dt.strftime('%Y-%m-%d')
  return df