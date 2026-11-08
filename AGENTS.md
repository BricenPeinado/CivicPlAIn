# CivicPlAIn development instructions

## Before changing the repository

- Read README.md and the documents relevant to the task. Start implementation from docs/MVP_ROADMAP.md; use docs/DATA_MODEL.md and docs/API_SPEC.md as shared contracts.
- Inspect Git status and preserve existing changes, IDE metadata, and working functionality. Adapt existing modules rather than creating a second application.
- Implement one milestone at a time. State the milestone and acceptance criteria before feature work. Update documentation when behavior or contracts change.
- M0–M6 are completed historical work. M7 starts at docs/M7_IMPLEMENTATION_PLAN.md and docs/M7_DESIGN_SYSTEM.md alongside the shared contracts. M7.0 is documentation/audit only: do not implement functionality, install dependencies, execute migrations or deploy. M7.1–M7.4 must pass their individual gates in MVP_ROADMAP before proceeding.
- Preserve the modular monolith, REST boundary, and separation of deterministic domain calculations from AI explanations. Explain major architectural deviations and their tradeoffs before making them.

## Engineering and data rules

- Do not fabricate infrastructure observations, utility locations, schedules, costs, or measurement accuracy. Label synthetic fixtures at record and screen level; retain provenance when deriving values.
- Treat missing utility information as unknown. A search with no finding never establishes that excavation is safe.
- For M7 use the six field-level classifications in DATA_MODEL: official_observation, imported_administrative_record, derived_calculation, planning_assumption, synthetic_fixture and unknown. Official publication does not make every field an observation. Preserve source values, dates, units, IDs, release, raw checksum and transform/match lineage. Keep data/demo fixtures and v1 replay unchanged; never coerce official records into synthetic-only schemas.
- Ingest official data through an explicit reviewed local adapter, with dry-run, quarantine, reproducible manifest and atomic publication. No ingestion on startup, user-provided URL fetcher or automatic refresh. Runtime downloads/processed extracts stay ignored; use small explicitly synthetic adapter test fixtures unless redistribution is reviewed.
- M7.1 is implemented through app.migrate/app.ingest and read-only /api/v2; see docs/M7_1_IMPLEMENTATION.md for exact verified sources, source-specific caveats, commands and test evidence. M7.2 reads pinned official snapshots in a separate presentation path; see docs/M7_2_IMPLEMENTATION.md. M7.3 adds source-backed Overview, exact permit filters, shareable context/record/camera state and protected on-demand scenario workflows; see docs/M7_3_IMPLEMENTATION.md. Navigation/GET must never create analysis, evaluation or AI audit writes; retain per-context drafts and keep/discard protection. Preserve its safe context selection, source disclosures, keyboard fallback and explicit synthetic screening. No official planning-engine calls or external tiles in automated tests.
- M7 preserves SQLite through additive, explicitly invoked versioned migration and verified backup/recovery. No table/payload rewrite, reseed requirement, destructive downgrade or automatic activation of a new snapshot. See ARCHITECTURE for the migration gate.
- Preserve existing calculations and regressions in synthetic mode. Official-data mode must not use demo rates/projects or claim real estimates/scenario execution before a separate versioned calculation/source gate. Show unknowns/unavailable capabilities honestly.
- Redesign the existing client into distinct map, dashboard, projects and scenarios views. Reuse feature modules; keep domain math server-side. Do not add demo experiences, guided tours, presentation scripts or judge-specific UI; retain historical reports and existing synthetic functionality.
- Keep estimates, spatial/temporal rules, and scenario evaluations deterministic, versioned, independently testable, and reproducible from a saved input snapshot.
- Keep validated facts separate from generated prose. AI may explain only supplied evidence; it cannot create measurements, approve projects, authorize spending, or call mutation tools.
- Preserve a useful deterministic explanation path without an OpenAI API key or network access. Never place a provider key in frontend configuration or source code.
- Expose estimate assumptions, units, bounds, limitations, and review requirements. Do not present demo savings or condition ratings as municipal observations.
- Use typed boundary validation. Reject invalid geometry, reversed intervals, negative budgets, unknown references, and inconsistent units explicitly.
- Write and run tests appropriate to the milestone, especially boundary cases, incomplete inputs, reproducibility, and AI failure. Report commands and actual outcomes; distinguish unrun checks from passing checks.
- Avoid unnecessary dependencies. OR-Tools requires a documented optimization problem that simpler enumeration cannot reasonably handle. Do not introduce microservices or Kubernetes for the MVP.
- Do not install dependencies, add migrations, implement features, or deploy during M0. Subsequent tasks should follow the milestone's authorized scope.

## Git, credentials, and delivery

- No destructive Git operations: no reset --hard, clean, history rewriting, or discarding another person's work. Do not commit or push without explicit user permission.
- Never expose credentials, local environment values, personal data, or sensitive utility geometry in logs, prompts, fixtures, or responses. Use .env.example for placeholder variable names only.
- Keep generated data and runtime databases untracked. Intentionally reviewed synthetic fixtures belong in data/demo/ with a manifest.
- Report changed files, commands, test results, unresolved questions, and the next milestone. Do not claim a proposed endpoint, planned screen, or unrun test works.

## Specification authority

PRODUCT_SPEC defines scope; DATA_MODEL defines shared data semantics; API_SPEC defines transport; ARCHITECTURE defines module boundaries. AI_SYSTEM and RESPONSIBLE_AI constrain all milestones. Resolve contradictions explicitly and update affected documents together. TBD means unresolved, not implemented.
