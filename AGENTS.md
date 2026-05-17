# Agent Instructions

You are working in the **PropInsights frontend** repository. This is an Anvil app that presents investor-facing property lists built by the backend data pipeline.

For product context, see `.agent/project_context.md`. For current frontend sequencing, see `.agent/roadmap.md`. For backend/Uplink data expectations, see `.agent/data_contract.md`. For workspace hygiene, see `.agent/repo_hygiene.md`.

## Canonical Project Hub

The canonical cross-repository source of truth is the PropInsights Notion hub:

https://www.notion.so/2feea071fbd2808fbea0eb115f55d6db

Local docs are frontend working instructions. If local context conflicts with the Notion hub, prefer Notion and update local docs when frontend instructions need to change.

## Operating Model

- Read existing Anvil forms/helpers before changing behavior.
- Prefer existing Anvil patterns, Material 3 roles, and shared helpers over new abstractions.
- Keep frontend changes aligned with backend data contracts and Uplink capabilities.
- Treat `Validation.DataProductStatus` as the future source for frontend availability and freshness, but inspect Uplink before wiring it.
- Keep app behavior branch-safe: the user tests feature branches before production merge.

## Important Paths

- `client_code/DataDashboard/`: main data product experience.
- `client_code/utils.py`: current dataset/county/city options and SQL builder.
- `server_code/ServerModule1.py`: background data load, staging, filtering, map, exports, and mocked freshness.
- `theme/assets/theme.css`: Material 3 visual system.
- `anvil.yaml`: Anvil app configuration, services, dependencies, and encrypted secrets.

## Product Rules

- Frontend should expose only county/list combinations that backend validation marks as safe.
- Adams / Absentee Owners is the current MVP target.
- Jefferson and future counties should remain hidden until backend outputs, validation metadata, and frontend selection UI agree.
- Do not synthesize backend freshness in the UI once `Validation.DataProductStatus` is available through Uplink or a future API.

## Safety Rules

- Never commit unencrypted credentials, local Anvil data, or generated scratch files.
- Do not push unverified changes directly to `master`.
- Do not change Anvil services, secrets, or authentication behavior without documenting the reason.
- Preserve the existing Material 3 design language when adding or changing UI.
