# Frontend Data Contract

This document captures what the Anvil frontend expects from the backend pipeline and Uplink.

## Current MVP Product

- Dataset: Absentee Owners.
- County: Adams, CO.
- Table: `real-estate-data-processing.DataLists.AbsenteeOwners`.
- Backend status table: `real-estate-data-processing.Validation.DataProductStatus`.
- Current backend status: Adams master and Adams Absentee Owners are `passed` / `current`; `exposed_to_frontend` remains `false` until frontend availability is intentionally wired.

## List Columns

The dashboard currently expects these list columns, in preferred display order:

```text
Address, City, County, State, OwnerName, OwnerAddress, OwnerCity, OwnerState,
OwnerZip, BuildingDescription, SF, Bedrooms, Bathrooms, YearBuilt, AssessedValue,
LastSalesPrice, LastSalesDate, LAT, LON
```

`client_code/utils.py` and `server_code/ServerModule1.py` both encode this preferred order.

## Availability Metadata Target

The frontend should eventually generate available options from `Validation.DataProductStatus` rows where:

- `entity_type = 'derived_list'`
- `validation_status = 'passed'`
- `freshness_status = 'current'`
- `exposed_to_frontend = TRUE`

Relevant fields:

- `entity_id`
- `display_name`
- `dataset_name`
- `table_name`
- `county`
- `state`
- `workflow_name`
- `last_successful_refresh_at`
- `last_validation_at`
- `validation_status`
- `freshness_status`
- `row_count`
- `exposed_to_frontend`
- `error_message`
- `updated_at`

## Current Implementation Gap

Current frontend behavior is hard-coded:

- `get_dataset_dict()` returns Absentee Owners.
- `get_county_dict()` returns Adams.
- `get_city_dict()` returns a static city list.
- `get_county_metadata()` returns a mocked date.

Before changing this, inspect the Uplink workspace and decide whether metadata should be fetched through:

- the existing `get_bigquery_media(query)` Parquet path, or
- a narrower metadata callable that returns structured rows directly.

## Query Path

Current query flow:

1. `client_code/utils.py` builds SQL.
2. `server_code/ServerModule1.py` calls Uplink callable `get_bigquery_media(query)`.
3. Uplink returns Parquet media.
4. Server stores media in `tmp_results`.
5. Client pages, filters, maps, and exports from staged Parquet.

## Data Semantics To Preserve

- `LastSalesDate` may be null when source sales history is missing.
- Adams `City = 'Unincorporated'` is a valid self-describing backend value.
- Adams `Address = 'No Situs Address'` is a valid self-describing backend value for source records without a situs street address.
- Frontend should not hide or rewrite these values without a documented product decision.
