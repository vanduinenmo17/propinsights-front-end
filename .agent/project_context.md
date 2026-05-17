# PropInsights Project Context

## Overview
PropInsights (prop-insights.com) is a web application designed to provide real estate investors with user-friendly, intuitive, and affordable access to property data sourced from various county tax assessor websites. It serves as a cost-effective alternative to competitors like ListSource and PropStream.

## Core Value Proposition
- Intuitive and cheaper access to county-level property data.
- Pre-curated lists (e.g., Absentee Owners) to generate viable real estate leads and provide market insight.

## Current State & Tech Stack
- **Front-end Framework:** Anvil.works (Python-only full-stack framework).
- **Design System:** Material Design 3 (using Anvil's Material 3 Theme).
- **Key Dependencies:** Tabulator (for data tables), Plotly (for map visualizations), Anvil Extras.
- **Backend Data Source:** BigQuery tables produced by `tax_assessor_data_collections_and_transformations`.
- **Uplink Dependency:** Server code expects an Uplink callable named `get_bigquery_media(query)` that returns Parquet media for a BigQuery query.
- **Current Features:**
  - Landing page.
  - Sidebar navigation with auxiliary pages.
  - Out-of-the-box user authentication (Login/Signup via Anvil Users service).
  - **Data Dashboard:**
    - Allows users to select Dataset, County, and City to pull specific properties.
    - Triggers background server tasks (`anvil.server.background_task`) to pull large datasets asynchronously.
    - Displays data in a responsive Tabulator data grid with filtering and server-side pagination.
    - Displays interactive property locations on an interactive, clustered Plotly Mapbox map.
    - Supports exporting tabular data to CSV, Excel, JSON, and Parquet.

## Current MVP Data Status
- Current frontend option target is **Adams County, CO / Absentee Owners**.
- Dataset/county/city options are currently hard-coded in `client_code/utils.py`.
- Freshness display is currently mocked in `server_code/ServerModule1.py`.
- Backend now publishes validation/freshness metadata in `real-estate-data-processing.Validation.DataProductStatus`.
- The frontend should eventually use rows where `validation_status = 'passed'`, `freshness_status = 'current'`, and `exposed_to_frontend = TRUE`.
- As of the latest backend validation, Adams master and Adams Absentee Owners are `passed` / `current`, but `exposed_to_frontend = false` until frontend availability is deliberately wired.

## Target Audience
Real estate investors looking for leads, specific property lists, and broad market insights without having to manually scrape or prepare the data themselves.

## Development Roadmap Goals
1. **Reliable Adams MVP:** Replace mocked freshness and hard-coded availability with backend validation metadata.
2. **Uplink Documentation:** Inspect and document the `re-data-anvil-uplink` workspace before wiring dynamic metadata.
3. **Data Expansion:** Increase the number of available counties only after backend validation/freshness and frontend availability agree.
4. **More Curated Lists:** Increase the number of out-of-the-box datasets/lists available to users.
5. **Custom List Builder:** Allow users to build custom property lists with comprehensive filtering UI.
6. **UI/UX Modernization:** Modernize the layout, look and feel of the website and UI (specifically the landing page and dashboard).
7. **Monetization (Stripe):** Implement a subscription payment structure and paywalls via Stripe using Anvil's native Stripe Services, Stripe pricing tables, and Customer Portal integration, controlling access based on the built-in Anvil Users table.

## Design & Aesthetics Constraint
**CRITICAL:** It is a strict requirement that any new features, panels, or pages added to the front end must flawlessly maintain the existing color scheme and design language of the website. The primary styling is dictated by Anvil's Material 3 Theme (`theme/assets/theme.css`). Future agents must ensure absolute visual consistency regarding layouts, fonts, and colors when making UI modifications.

## Git Workflow & Deployment Constraint
**CRITICAL:** The `master` branch is tied directly to the live production website. You must NEVER commit and push unverified changes directly to `master`. All development work must be done on a newly created, descriptively named Git branch (e.g., `feature/phase1-core-ux`). The user will personally test and verify all changes on this branch before manually merging them into production.
