# M3.5 compatibility and architecture preparation

Completed locally on 2026-11-07 on `bp/m3-5-compatibility`, based on `b116e90` (M3). The starting working tree was clean. No commit/push, migration, runtime API/domain/UI change, fixture edit, new pricing method, scenario evaluator or calendar optimizer was made. M4 has not started.

## Frontend portability fix

The four Node filesystem imports are in App.test.tsx, services/api.test.ts, features/conflicts/testData.ts and features/estimates/RepairPlanner.test.tsx. Before the fix, the checkout could resolve Node declarations from a parent directory even though its own package/lockfile omitted them. An isolated checkout failed with TS2591.

Added exact development dependency `@types/node` 22.20.5, consistent with supported Node 22.12+ and the existing tooling peer ranges. Its sole added transitive package is `undici-types` 6.21.0. Added `node` to the shared tsconfig's explicit type list because this configuration includes the Node-based tests and Vite configuration as well as the browser sources. No runtime import or frontend secret configuration was added. TypeScript 7.0.2 and every preexisting lockfile package/version/metadata remain unchanged.

## Actual validation

Environment: macOS, Python 3.12.5, Node 24.5.0, npm 11.6.0. The frontend clean copy was `/private/tmp/civicplain-m35.61EgYb/isolated`, containing apps/web and data/demo, without copied node_modules, build output or local environment files. Its npm cache was initially empty. NODE_PATH and NODE_OPTIONS were unset and separate empty npm user/global configurations were used. Initial use of /dev/null for both npm config scopes was rejected before installation; distinct config paths corrected that verification setup.

Actual isolated commands (from that copy):

```sh
env -u NODE_PATH -u NODE_OPTIONS npm ci --prefix apps/web --cache /private/tmp/civicplain-m35.61EgYb/npm-clean-cache --userconfig /dev/null --globalconfig /private/tmp/civicplain-m35.61EgYb/empty-global.npmrc --no-audit --no-fund --fetch-retries=0 --fetch-timeout=20000
env -u NODE_PATH -u NODE_OPTIONS npm run typecheck --prefix apps/web
env -u NODE_PATH -u NODE_OPTIONS npm run build --prefix apps/web
env -u NODE_PATH -u NODE_OPTIONS npm test --prefix apps/web
```

The clean npm ci installed 197 packages successfully. Typecheck and the complete production-build script both exited 0. All 32 frontend tests across five files passed. A compiler-file-path check resolved @types/node from this copy's own node_modules and verified that all 376 compiler dependency paths under node_modules realpath into this installation. No parent installation was involved. Dependency installation required registry access; no live municipal/provider data was requested. A package security audit was not run (`--no-audit`); no vulnerability-free claim is made.

From the actual repository, after installing the same lockfile offline from that verified cache:

```sh
npm ci --prefix apps/web --offline --cache /private/tmp/civicplain-m35.61EgYb/npm-clean-cache --no-audit --no-fund
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/api .venv/bin/python -B -m pytest apps/api/tests -q -p no:cacheprovider
npm test --prefix apps/web
npm run typecheck --prefix apps/web
npm run build --prefix apps/web
git diff --check
```

Results: **93 backend tests passed**, **32 frontend tests passed**, typecheck passed, production build passed, whitespace check passed. Existing nonblocking warnings remain: Starlette's httpx TestClient deprecation and the MapLibre bundle exceeding Vite's 500 kB advisory. No browser source changed; M3.5 did not repeat the earlier interactive-browser audit or claim new UI functionality. The production JS/CSS/worker filenames and sizes match the prior audit's bundle.

## Data preservation and reproducibility

A read-only SQLite baseline captured complete sorted rows of every table before changes. Both `PRAGMA integrity_check` (ok) and `PRAGMA foreign_key_check` (no rows) passed. All 14 original table row counts and canonical row hashes remained identical, and the original database file SHA-256 remained identical. Original counts: 24 roads, 5 maintenance records, 26 assessments, 3 options, 3 evidence sources, 7 work projects, 6 project-road links, 1 analysis, 8 findings and 0 estimates, plus the retained manifest/migration tables.

Original roads, all data/demo files, backend implementation/tests and frontend src files remain byte-identical. All three fixture manifests' checksums verified. The original database had no saved estimates, so there were none to replay there. On a temporary database backup, a new R-001 estimate was created through the existing API and replayed from its saved road/assessment/option/source snapshot: input/result hashes and $44,760/$53,400/$66,360 totals matched. A second FastAPI application instance retrieved the same saved estimate, seven projects and original analysis. This is application-instance restart verification, not a new browser/process-start test.

The original saved M3 analysis replayed from its complete frozen inputs with identical input/result hashes: 8 findings (4 concurrent_work, 2 multiple_closures, 1 reopening_risk, 1 sequencing_review), 10 incomplete checks, 16 candidates out of 21 pairs. Its synthetic labels, sources and required review persisted. All three R-001 option totals and duration components matched the revised DEMO_PLAN table. The proposed `/api/v1/scenarios` route still returned 404.

A lockfile comparison verified that only the two new type packages were added; all preexisting entries are unchanged. Review of changed files and common credential/private-key patterns found no secret additions; no environment file was added. This is a scoped diff review, not a claim of an exhaustive security audit.

## Contract decisions

- DATA_MODEL: proposed scenario-v1 and scenario-action-v1 distinguish whole/partial/trench/unknown scopes, sourced/assumed/derived quantities, null unknowns, related projects, explicit overrides and planning constraints. Existing M2 area input/API is unchanged; future direct-area support must factor and reuse its single costing implementation.
- Catalog/demo: implemented preventive/resurface/reconstruct options and rate-only sensitivity remain authoritative. The old $120,000/$48,000/$19,200 narrative and unsourced lifespan values are retired. Proposed repair-option-v2 specifies patch/restoration source requirements, not numerical prices.
- Scheduling: active workdays and setup/curing allowances stay distinct from supplied calendar dates/closures. Optional work calendars are recorded assumptions, not date generation. Explicit mobilization groups represent priced replacement lines and allocations, not automatic savings or reduced setup days.
- ARCHITECTURE: proposed hypothetical-conflict-adapter-v1 validates immutable snapshots, retains originals and explicit exclusions/replacements, projects actions into current M3 input types and delegates once to conflict-screen-v1. It preserves evidence/hashes/versioning, labels hypothetical versus existing-project screening and never writes hypotheses into project/conflict tables. Current Road/Evidence source-shape limits and unsupported reopening mappings are explicit.
- API_SPEC: future requests use the nested versioned contract; legacy flat draft fields are retired. Current estimate/project/conflict transports remain unchanged. A valid incomplete future draft may be saved, while evaluation exposes unavailable/indeterminate values. No scenario endpoint or runtime schema has been implemented.
- PRODUCT_SPEC/RESPONSIBLE_AI: numerical affordability and unresolved safety review are independent; no price, geometry finding or supplied schedule grants safety or approval.

## Files changed

- apps/web/package.json
- apps/web/package-lock.json
- apps/web/tsconfig.json
- README.md
- docs/DATA_MODEL.md
- docs/API_SPEC.md
- docs/ARCHITECTURE.md
- docs/MVP_ROADMAP.md
- docs/DEMO_PLAN.md
- docs/RESPONSIBLE_AI.md
- docs/PRODUCT_SPEC.md (clarify affordability versus safety)
- docs/M3_5_COMPATIBILITY.md (this verification record)

## Remaining M4 work and source gates

No unresolved M3.5 implementation blocker remains. M4 must implement and test the proposed schemas, quantity/cost helper reuse, hypothetical adapter, immutable evaluation storage and comparison UI; those designs are not working features today. Shared-mobilization adjustment must be implemented explicitly or rejected, not ignored. No new infrastructure or AI key is needed for that milestone.

The fully priced immediate/coordinated/staged story remains blocked on reviewed patch/restoration methods, quantities and sources. Current contracts deliberately permit unavailable costs and indeterminate totals, so honest incomplete rows can be implemented without inventing rates. Lifespan remains unknown without a reviewed source. Optional calendars have no generator/optimizer. Current observed municipal ingestion remains unsupported and requires a separate provenance/schema extension. These are explicit future scope/source limits, not hidden completed functionality.
