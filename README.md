# CivicPlAIn

BUHACKS 2026 Hackathon — municipal roadwork decision support.

CivicPlAIn is planned to help municipal planners avoid resurfacing a road shortly before overlapping utility work reopens it. Planners will compare cost, condition, disruption, and maintenance longevity using traceable inputs and explicit uncertainty. People retain responsibility for engineering, schedules, and spending.

## Current status

M0 documentation and directory scaffold only. There is no runnable frontend, backend, database, ingestion pipeline, AI integration, dependency manifest, or application test suite. All screens, schemas, and endpoints in the documentation are proposed. No feature is implemented by this foundation task.

The initial repository contained this README and IntelliJ project metadata. Existing IDE files are preserved. See [foundation inspection](docs/FOUNDATION_INSPECTION.md) for the baseline and discrepancies.

## Hackathon scope

One Lower Manhattan study window and a target of 20–30 road segments, with a hard cap of 30. Planned capabilities are a map and asset detail, condition records, assumption-based cost/duration estimates, spatial and schedule conflicts, potential utility-work conflicts, and budget-aware comparison of manually defined scenarios. Evidence and review limitations accompany every result. Optional AI explains validated results; deterministic summaries remain available without a key.

Road prioritization, traffic routing, and extra optimization constraints are stretch goals. Forecasting, live municipal integrations, additional infrastructure categories, and multi-tenant SaaS are post-MVP.

## Planned stack

| Layer | Plan |
| --- | --- |
| Web | React, TypeScript, Vite, Tailwind CSS, MapLibre GL JS |
| API | Python, FastAPI, Pydantic; REST modular monolith |
| Data | SQLite; GeoJSON exchange; Shapely calculations; GeoPandas ingestion when needed |
| Network | NetworkX reserved for stretch road-network analysis |
| AI | Optional backend OpenAI adapter; deterministic explanations by default |
| Optimization | Direct scenario enumeration first; OR-Tools only with a justified problem |

Versions and exact dependency sets will be chosen and locked in M1. These libraries are not installed or configured yet.

## Repository structure

```text
apps/web/src/       components, features, pages, hooks, services, types
apps/api/app/       routes, models, schemas, services, core
apps/api/tests/     future API and domain tests
data/raw/          ignored source downloads
data/processed/    ignored generated normalized outputs
data/demo/         future reviewed synthetic fixtures and manifest
docs/              specifications, roadmap, and demo plan
scripts/           future ingestion and development helpers
```

Empty directories use .gitkeep; Python package markers contain no application logic.

## Local setup

Only documentation can currently be reviewed locally. Open the Markdown files in an editor with Mermaid support for diagrams. `.env.example` lists proposed variable names; copying it does not produce a working application. There are no supported install, start, seed, or test commands yet. M1 will add the manifests, exact prerequisites, local run commands, and health/map smoke checks. No OpenAI API key will be required.

## Responsible AI

Calculations and conflict detection belong to deterministic services. AI may explain supplied evidence, never invent facts or approve work. Unknown utility coverage remains visible; absence of a detected conflict is not clearance. Costs, dates, and condition values in synthetic demo records must be labeled. Field verification and responsible human review precede any real municipal use.

## Documentation

- [Development rules](AGENTS.md)
- [Product specification](docs/PRODUCT_SPEC.md)
- [MVP roadmap](docs/MVP_ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data model](docs/DATA_MODEL.md)
- [Proposed API](docs/API_SPEC.md)
- [AI system](docs/AI_SYSTEM.md)
- [Responsible AI](docs/RESPONSIBLE_AI.md)
- [Data sources and study area](docs/DATA_SOURCES.md)
- [Demo plan](docs/DEMO_PLAN.md)
- [Foundation inspection and open questions](docs/FOUNDATION_INSPECTION.md)
