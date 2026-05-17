# PropInsights Frontend Roadmap

This document is the frontend tactical plan for `propinsights-front-end`.

The canonical cross-repository roadmap lives in the PropInsights Notion hub:

https://www.notion.so/2feea071fbd2808fbea0eb115f55d6db

## Production Target: Reliable Adams MVP Frontend

The next client-ready frontend milestone is to safely expose Adams County / Absentee Owners using backend validation and freshness status.

Acceptance criteria:

- Frontend exposes only backend-approved dataset/county options.
- Freshness and validation status come from backend metadata, not mock dates.
- Adams / Absentee Owners can be queried, paged, filtered, mapped, and exported.
- Empty, stale, failed, or unavailable data states are clear to users.
- Uplink behavior is documented enough to support metadata queries safely.

## Current State

- `[x]` Anvil frontend exists with Material 3 theme.
- `[x]` Landing page, auth, account menu, contact form, and dashboard forms exist.
- `[x]` Data dashboard can query BigQuery through Uplink, stage Parquet media, page/filter results, render clustered maps, and export CSV/XLSX/JSON/Parquet.
- `[x]` Current hard-coded product target is Adams / Absentee Owners.
- `[ ]` Freshness display is still mocked in `server_code/ServerModule1.py`.
- `[ ]` Dataset/county/city availability is hard-coded in `client_code/utils.py`.
- `[ ]` Uplink workspace still needs direct inspection and documentation.

## Phase 1: Documentation Baseline

- `[x]` Replace stock Anvil README with PropInsights-specific frontend orientation.
- `[x]` Add frontend `AGENTS.md`.
- `[x]` Add frontend roadmap, data contract, and repo hygiene docs.
- `[ ]` Create or update Notion frontend repo page and link it from the hub.

## Phase 2: Uplink Inspection

Objective: understand how the frontend currently reaches BigQuery before wiring dynamic availability.

- `[ ]` Open and inspect `re-data-anvil-uplink`.
- `[ ]` Document `get_bigquery_media(query)`, credentials, security assumptions, query execution path, and operational limits.
- `[ ]` Decide whether frontend should query `Validation.DataProductStatus` through the existing Parquet media path or a new metadata-specific Uplink callable.

## Phase 3: Backend-Driven Availability

Objective: replace hard-coded availability and mocked freshness with backend metadata.

- `[ ]` Add a server callable that retrieves rows from `Validation.DataProductStatus`.
- `[ ]` Generate dataset/county options from rows where `validation_status = 'passed'`, `freshness_status = 'current'`, and `exposed_to_frontend = TRUE`.
- `[ ]` Replace `get_county_metadata` mocked dates with real metadata.
- `[ ]` Add UI states for unavailable, stale, failed, and unknown metadata.
- `[ ]` Keep Adams hidden until backend metadata intentionally flips `exposed_to_frontend = TRUE`.

## Phase 4: Reliable Adams UX

Objective: make the MVP user experience trustworthy and polished.

- `[ ]` Verify Adams / Absentee Owners query, paging, filtering, map, and exports against current backend output.
- `[ ]` Confirm city filtering includes backend self-describing values such as `Unincorporated`.
- `[ ]` Confirm `No Situs Address` rows behave acceptably in table/map/filter/export flows.
- `[ ]` Review mobile and desktop dashboard ergonomics.
- `[ ]` Add user-facing handling for no results, oversized results, timeouts, expired staged results, and Uplink failures.

## Phase 5: Expansion Readiness

- `[ ]` Add Jefferson only after backend validation/freshness metadata and derived-list availability are ready.
- `[ ]` Prepare UI for multiple lists/counties without hard-coded option churn.
- `[ ]` Revisit monetization, saved searches, and custom list builder after Adams MVP reliability is complete.
