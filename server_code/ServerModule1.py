import anvil.email
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
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.compute as pc
import plotly.graph_objects as go

PREFERRED_ORDER = [
  'Address','City','County','State','OwnerName','OwnerAddress','OwnerCity','OwnerState',
  'OwnerZip','BuildingDescription','SF','Bedrooms','Bathrooms','YearBuilt','AssessedValue',
  'LastSalesPrice','LastSalesDate','LAT','LON'
]

DATASET_TABLES = {
  "AbsenteeOwners": "`real-estate-data-processing.DataLists.AbsenteeOwners`",
}

DATASET_LABELS = {
  "AbsenteeOwners": "Absentee Owners",
}

DATA_PRODUCT_TABLES = {
  "absentee_owners_adams_co": "AbsenteeOwners",
}

DATA_PRODUCT_NAMES = {
  "absenteeowners": "AbsenteeOwners",
  "absentee owners": "AbsenteeOwners",
  "absentee_owners": "AbsenteeOwners",
}

# --- Expectation: Uplink provides `get_bigquery_media(query)` that returns a Parquet as an Anvil Media object.
@anvil.server.background_task
def bg_prepare_result(query: str):
  """Ask Uplink for a Parquet Media of the full result, record it in a temp table, return ids+meta."""
  media = anvil.server.call('get_bigquery_media', query)  # <-- from your Uplink
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)
    df = _reorder_df(df) 
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
    df = _reorder_df(df)
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

@anvil.server.callable
def get_county_metadata(county_names: list):
  """
  Return the latest successful refresh date for the selected exposed products.
  """
  if not county_names:
    return "Unknown"

  status_rows = _get_status_rows()
  selected_counties = set(county_names or [])
  matching_rows = [
    row for row in status_rows
    if row.get("county") in selected_counties
    and row.get("validation_status") == "passed"
    and row.get("freshness_status") == "current"
    and row.get("last_successful_refresh_at")
  ]

  if not matching_rows:
    return "Unavailable"

  latest = max(row.get("last_successful_refresh_at") for row in matching_rows)
  return _format_metadata_date(latest)

@anvil.server.callable
def get_frontend_availability():
  """
  Return data products the backend has explicitly exposed to the frontend.
  Uplink filters this to exposed rows in Validation.DataProductStatus.
  """
  try:
    rows = _get_status_rows()
  except Exception as exc:
    print(f"get_frontend_availability failed: {exc}")
    return {
      "available": False,
      "datasets": [],
      "counties": [],
      "message": "Data availability is temporarily unavailable. Please try again later.",
      "error": str(exc),
    }

  product_rows = []
  for row in rows:
    if row.get("validation_status") != "passed" or row.get("freshness_status") != "current":
      continue

    dataset_value = _dataset_value_for_status(row)
    if not dataset_value:
      continue

    product_rows.append({
      "dataset_key": DATASET_LABELS.get(dataset_value, dataset_value),
      "dataset_value": dataset_value,
      "county_key": row.get("county"),
      "county_value": row.get("county"),
      "state": row.get("state"),
      "entity_id": row.get("entity_id"),
      "row_count": row.get("row_count"),
      "last_successful_refresh_at": row.get("last_successful_refresh_at"),
    })

  datasets = _unique_options(
    {"key": row["dataset_key"], "value": row["dataset_value"]}
    for row in product_rows
    if row.get("dataset_key") and row.get("dataset_value")
  )
  counties = _unique_options(
    {"key": row["county_key"], "value": row["county_value"]}
    for row in product_rows
    if row.get("county_key") and row.get("county_value")
  )

  return {
    "available": bool(datasets and counties),
    "datasets": datasets,
    "counties": counties,
    "products": product_rows,
    "message": "Select a data product and county." if product_rows else "No validated data products are currently exposed.",
  }

@anvil.server.callable
def get_available_cities(dataset_values: list, county_names: list):
  """Return city options for the selected exposed dataset/county pair."""
  if not dataset_values or not county_names:
    return []

  dataset = dataset_values[0]
  table = DATASET_TABLES.get(dataset)
  if not table:
    raise ValueError("Selected dataset is not available.")
  if not _is_exposed_selection(dataset, county_names):
    raise ValueError("Selected dataset/county is not exposed.")

  query = f"""
    SELECT DISTINCT City
    FROM {table}
    WHERE County {_sql_in_phrase(county_names)}
      AND City IS NOT NULL
      AND TRIM(City) != ''
    ORDER BY City
  """
  media = anvil.server.call('get_bigquery_media', query)
  with anvil.media.TempFile(media) as tmp:
    df = pd.read_parquet(tmp)

  return [
    {"key": _display_city(row["City"]), "value": row["City"]}
    for _, row in df.iterrows()
    if row.get("City")
  ]

# ---- GLOBAL FILTERING OVER WHOLE PARQUET -------------------------------
@anvil.server.callable
def filter_result(result_id: str, field: str, op: str, value, page: int = 1, page_size: int = 1000):
  """
  Return one page of rows matching (field op value) from the ENTIRE staged result.
  Falls back to Pandas if we cannot build a pushdown-friendly expression.
  """
  row = app_tables.tmp_results.get(result_id=result_id)
  if not row:
    raise Exception("Result expired or not found")

  # Normalize operator spellings
  op = (op or '').strip().lower()

  # We'll always read all columns for the page we return
  # (we could project fewer and re-join later, but keep it simple)
  with anvil.media.TempFile(row['media']) as tmp:
    # Try Arrow Dataset + predicate pushdown first (works well for =, !=, >, <, >=, <= on many types)
    try:
      dataset = ds.dataset(tmp, format="parquet")

      # Build a dataset expression if supported
      expr = _build_ds_expr(field, op, value)
      if expr is None:
        raise ValueError("no-dataset-expr")  # use Pandas fallback

      # Get filtered table; if your pyarrow is recent, you can pass limit/offset in to_table()
      # If that's not available in your runtime, we'll table->pandas->slice below.
      tbl = dataset.to_table(filter=expr)  # projection could be added via columns=[...]

      df = tbl.to_pandas(types_mapper=pd.ArrowDtype)  # keep types precise where possible
    except Exception:
      # Fallback: Pandas read and filter
      df = pd.read_parquet(tmp)

      # Apply vectorized filter in Pandas
      df = _apply_pandas_filter(df, field, op, value)

  # Total after filter
  total = int(len(df))

  # Page slice
  start = max(0, (page - 1) * page_size)
  end = start + page_size
  page_df = df.iloc[start:end].copy()

  # Normalize date columns like before
  page_df = _normalize_dates(page_df)
  page_df = _reorder_df(page_df)  

  return {
    "rows": page_df.to_dict(orient="records"),
    "row_count": total,
    "columns": list(df.columns),
  }
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

def _build_ds_expr(field: str, op: str, value):
  """
  Build a pyarrow.dataset expression when we can (good for pushdown).
  Return None to force Pandas fallback (e.g., LIKE).
  """
  f = ds.field(field)

  # Try to coerce numeric strings where appropriate
  val = _coerce_value(value)

  if op in ('=', '=='):
    return f == val
  if op in ('!=', '<>'):
    return f != val
  if op == '>':
    return f > val
  if op == '<':
    return f < val
  if op == '>=':
    return f >= val
  if op == '<=':
    return f <= val

  # "like" (substring/regex) isn’t a pushdown-friendly predicate; handle in Pandas
  if op == 'like':
    return None

  # Unknown operator → fallback
  return None


def _apply_pandas_filter(df: pd.DataFrame, field: str, op: str, value):
  if field not in df.columns:
    return df.iloc[0:0]  # empty

  s = df[field]

  # Try numeric compare if both sides numeric
  v_num = pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]
  col_numeric = pd.api.types.is_numeric_dtype(s)
  if pd.notna(v_num) and col_numeric and op in ('=', '==','!=','<','>','<=','>='):
    v = v_num
  else:
    v = value

  if op in ('=', '=='):
    return df[s == v]
  if op in ('!=', '<>'):
    return df[s != v]
  if op == '>':
    return df[s > v]
  if op == '<':
    return df[s < v]
  if op == '>=':
    return df[s >= v]
  if op == '<=':
    return df[s <= v]
  if op == 'like':
    # case-insensitive substring; fast vectorized contains
    return df[s.astype(str).str.contains(str(v), case=False, na=False)]

  # Unknown operator → return empty
  return df.iloc[0:0]

def _coerce_value(v):
  # Try numeric
  try:
    if isinstance(v, str):
      vv = float(v) if '.' in v else int(v)
      return vv
  except Exception:
    pass
  # Leave as-is (string, date-ish, etc.)
  return v

def _reorder_df(df: pd.DataFrame) -> pd.DataFrame:
  # Bring preferred columns to the front (only those that exist),
  # then append any extras at the end to avoid KeyErrors.
  preferred = [c for c in PREFERRED_ORDER if c in df.columns]
  extras = [c for c in df.columns if c not in PREFERRED_ORDER]
  return df[preferred + extras]

def _get_status_rows():
  rows = anvil.server.call('get_data_product_status')
  return rows or []

def _dataset_value_for_status(row: dict):
  entity_id = (row.get("entity_id") or "").lower()
  if entity_id in DATA_PRODUCT_TABLES:
    return DATA_PRODUCT_TABLES[entity_id]

  for key in ("dataset_name", "table_name", "display_name"):
    value = row.get(key)
    if not value:
      continue

    normalized = str(value).strip().lower()
    if normalized in DATA_PRODUCT_NAMES:
      return DATA_PRODUCT_NAMES[normalized]
    if value in DATASET_TABLES:
      return value

  return None

def _is_exposed_selection(dataset, counties):
  selected_counties = set(counties or [])
  for row in _get_status_rows():
    if row.get("validation_status") != "passed" or row.get("freshness_status") != "current":
      continue
    if _dataset_value_for_status(row) != dataset:
      continue
    if row.get("county") in selected_counties:
      return True
  return False

def _unique_options(options):
  seen = set()
  unique = []
  for option in options:
    value = option.get("value")
    if value in seen:
      continue
    seen.add(value)
    unique.append(option)
  return unique

def _sql_in_phrase(values):
  quoted = [f"'{str(value).replace(chr(39), chr(39) + chr(39))}'" for value in values]
  return f"IN ({', '.join(quoted)})"

def _display_city(city):
  if not city:
    return city
  city = str(city)
  if city.isupper():
    return city.title()
  return city

def _format_metadata_date(value):
  try:
    if isinstance(value, dt.datetime):
      parsed = value
    else:
      parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.strftime("%B %d, %Y")
  except Exception:
    return str(value)
