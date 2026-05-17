# PropInsights Frontend

This repository contains the **PropInsights Anvil web app**. It is the user-facing product for real estate investors who want searchable, exportable property lists built from county tax assessor data.

Canonical cross-repository project memory lives in the PropInsights Notion hub:

https://www.notion.so/2feea071fbd2808fbea0eb115f55d6db

Use this README for frontend-specific orientation. See `.agent/project_context.md` for product context, `.agent/roadmap.md` for current frontend sequencing, `.agent/data_contract.md` for backend/Uplink expectations, and `.agent/repo_hygiene.md` for workspace rules.

## Current Product Shape

- Framework: Anvil.works.
- Theme: Material Design 3 via the Anvil Material 3 dependency and `theme/assets/theme.css`.
- Main startup form: `LandingPage`.
- Primary app experience: `DataDashboard`.
- Authentication: Anvil Users service.
- Data access: Anvil server code calls an Uplink-provided callable named `get_bigquery_media(query)`, which returns Parquet media from BigQuery.
- Current exposed MVP target: Adams County, CO / Absentee Owners.

## Repository Layout

- `client_code/`: Anvil client forms and shared client helpers.
  - `DataDashboard/`: dataset/county/city selection, background load polling, table paging, filtering, map rendering, and export buttons.
  - `utils.py`: current hard-coded dataset/county/city options and BigQuery query builder.
  - `user_ui.py`: shared header/login/account behavior.
- `server_code/`: Anvil server callables and background tasks.
  - `ServerModule1.py`: Uplink data fetch, Parquet staging, filtering, map figure generation, exports, and mocked freshness metadata.
  - `contact_us_module.py`: contact form persistence and email notification.
- `theme/`: Material 3 theme files and static assets.
- `.agent/`: local agent context, roadmap, data contract, and repo hygiene notes.
- `anvil.yaml`: Anvil app configuration, services, dependencies, data tables, and encrypted secrets.

## Data Flow

1. A user selects dataset, county, and optionally city in `DataDashboard`.
2. `client_code/utils.py` builds a BigQuery SQL query against `real-estate-data-processing.DataLists`.
3. `server_code/ServerModule1.py` launches `bg_prepare_result`.
4. The background task calls Uplink callable `get_bigquery_media(query)`.
5. Uplink returns Parquet media, which the app stores in the Anvil `tmp_results` table.
6. The dashboard pages/filter/exports from staged Parquet and renders a clustered Plotly map.

## Current Gaps

- Dataset/county/city options are hard-coded in `client_code/utils.py`.
- Freshness display is mocked in `get_county_metadata`.
- Frontend availability is not yet driven by `real-estate-data-processing.Validation.DataProductStatus`.
- Uplink behavior still needs direct inspection in the `re-data-anvil-uplink` workspace.
- `exposed_to_frontend` is currently `false` for Adams metadata until frontend availability is intentionally wired.

## Development Notes

- The `master` branch is tied to the live production site. Work on feature branches and let the user test before merging.
- Keep Material 3 visual language consistent. Avoid ad hoc styling unless it belongs in `theme/assets/theme.css`.
- Do not commit local Anvil data, generated files, credentials, or unencrypted secrets.
- When changing data availability, coordinate with backend `Validation.DataProductStatus` and the Uplink query path.
