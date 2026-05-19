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
- `[x]` Working dashboard fixes have been merged to `master`; follow-up cleanup work should branch from current `master`.
- `[x]` Current product target is Adams / Absentee Owners.
- `[x]` Freshness display is backed by `Validation.DataProductStatus`.
- `[x]` Dataset/county availability is metadata-driven.
- `[x]` City availability is queried from the selected exposed list table.
- `[x]` Uplink workspace has been inspected and documented. The live Uplink key mismatch was fixed on the VM, and Anvil should treat Uplink as the required BigQuery bridge.

## Phase 1: Documentation Baseline

- `[x]` Replace stock Anvil README with PropInsights-specific frontend orientation.
- `[x]` Add frontend `AGENTS.md`.
- `[x]` Add frontend roadmap, data contract, and repo hygiene docs.
- `[x]` Create or update Notion frontend repo page and link it from the hub.

## Phase 2: Uplink Inspection

Objective: understand how the frontend currently reaches BigQuery before wiring dynamic availability.

- `[x]` Open and inspect `re-data-anvil-uplink`.
- `[x]` Document `get_bigquery_media(query)`, credentials, security assumptions, query execution path, and operational limits.
- `[x]` Use a metadata-specific Uplink callable, `get_data_product_status()`, for frontend availability.

## Phase 3: Backend-Driven Availability

Objective: replace hard-coded availability and mocked freshness with backend metadata.

- `[x]` Add a server callable that retrieves rows from `Validation.DataProductStatus`.
- `[x]` Generate dataset/county options from rows where `validation_status = 'passed'`, `freshness_status = 'current'`, and `exposed_to_frontend = TRUE`.
- `[x]` Replace `get_county_metadata` mocked dates with real metadata.
- `[x]` Add basic unavailable and unknown metadata states.
- `[x]` Flip Adams Absentee Owners to `exposed_to_frontend = TRUE`; keep Adams master hidden.

## Phase 4: Reliable Adams UX

Objective: make the MVP user experience trustworthy and polished.

- `[x]` Verify Adams / Absentee Owners query, paging, filtering, map, and exports against current backend output.
- `[ ]` Confirm city filtering includes backend self-describing values such as `Unincorporated`.
- `[ ]` Confirm `No Situs Address` rows behave acceptably in table/map/filter/export flows.
- `[ ]` Review mobile and desktop dashboard ergonomics.
- `[ ]` Add user-facing handling for no results, oversized results, timeouts, expired staged results, and Uplink failures.
- `[x]` Remove the attempted direct BigQuery fallback from Anvil; the Anvil runtime does not include the required BigQuery client libraries, so Uplink remains the supported data path.

## Phase 5: Expansion Readiness

- `[ ]` Add Jefferson only after backend validation/freshness metadata and derived-list availability are ready.
- `[ ]` Prepare UI for multiple lists/counties without hard-coded option churn.
- `[ ]` Revisit monetization, saved searches, and custom list builder after Adams MVP reliability is complete.
