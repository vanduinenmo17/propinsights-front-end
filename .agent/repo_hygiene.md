# Repository Hygiene

This repo should stay predictable for Anvil sync, local agent work, and future product changes.

## Root Rules

- Keep root files limited to Anvil config, README, AGENTS.md, license, package init, and standard repo config.
- Do not add generated files, local experiments, exports, or scratch data to the root.
- Do not commit `.anvil-data`, `__pycache__`, `.pyc`, local credentials, or unencrypted secrets.
- Treat `anvil.yaml` carefully. It contains app configuration and encrypted secret blobs; do not hand-edit secrets.

## App Structure Rules

- Client UI code belongs in `client_code/`.
- Server callables/background tasks belong in `server_code/`.
- Shared visual styles/assets belong in `theme/`.
- Agent/project docs belong in `.agent/`.
- Keep Uplink-specific implementation details out of this repo unless they are part of the frontend contract.

## Data Availability Changes

Any change that exposes a new dataset, county, or city should include:

- backend validation/freshness source confirmed
- frontend option update or dynamic metadata integration
- query builder review
- dashboard table/map/export verification
- roadmap/data-contract doc update

Do not expose new county/list options just because a BigQuery table exists. Use validation/freshness status as the release gate.

## Branching

The `master` branch is production-linked. Use feature branches for unverified work and let the user test before production merge.
