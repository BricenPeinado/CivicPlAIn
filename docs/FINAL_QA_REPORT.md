# Milestone 6 final QA report

Verified locally on **2026-11-07**. **M6 complete for the bounded synthetic hackathon demonstrator. Ready for local judging after the documented startup/rehearsal.** This is not production authorization or engineering safety validation. No commit, push, deployment, migration, dependency change or post-hackathon feature was performed.

## Scope, baseline and preservation

Initial checkout: `70bfd20`, branch `feat/m5-responsible-ai`, clean worktree. Work is on requested `feat/m6-final-integration`. Read AGENTS, README and all `docs/` before edits; reviewed existing frontend, backend, repository/storage, fixtures and tests. Adapted the existing React/Vite/MapLibre → FastAPI → SQLite modular monolith and REST contracts.

Verified existing implementation: M1 local schematic map/road inventory; M2 assessment history, treatment screening and saved deterministic cost/duration estimates; M3 persisted projects and saved spatial/temporal conflict analysis; M4 scenario editing, immutable evaluation and budget comparison; M5 bounded explanation selection, deterministic fallback, citations, audit and human review notes. No second application or AI calculation path was introduced.

Baseline: **205 backend tests passed**, **54 frontend tests passed in 9 files**, frontend typecheck and production build passed. No baseline test failure; existing Starlette/httpx test-client deprecation and Vite large-chunk advisory were recorded. Original single JS entry was 1,368.43 kB raw / 379.23 kB gzip.

All **17 original SQLite table counts and canonical row hashes are unchanged** after work; original six saved scenario evaluations replayed with matching results. Integrity check `ok`; foreign-key violations `0`. All **eight fixture/manifest files** are byte-identical after regenerating four fixture sets. Browser saves and audits went only into fresh ignored helper databases. No reset, deletion, data rewrite or IDE metadata change occurred.

## Changes delivered

- Lightweight **Explore Demo** navigates API-loaded synthetic R-001, its actual reopening finding and the existing scenario editor. It disables unavailable records; no client-generated results or automatic mutations.
- Scenario navigation opens/scrolls the mounted planner instead of toggling it away and losing an unsaved form. Compact navigation has accessible names and active-page semantics; a skip link reaches main content.
- Source links open collapsed supporting evidence, scroll and focus the exact cited record. Accessible comparison/breakdown regions support keyboard scrolling; A/B/C display order and human-readable units improve interpretation.
- Condition/severity text remains alongside color; selected map features/working areas remain visibly highlighted. Metadata, focus, wrapping, mobile stacking and warnings are clearer. Added explicit road-selector label.
- Lazy map and scenario chunks, panel error boundaries and loading states; a cleared conflict selection no longer leaves a stale loading flag. Project geometry is not resubmitted for every finding selection.
- Local transport guard rejects foreign browser mutation origins, bodies above 1 MiB (including chunked bodies), invalid Content-Length and body-read timeout. CORS and the normal sanitized error envelope remain. No authentication claim.
- Standard-library demo helper starts a fresh retained database, idempotently seeds, pins loopback URLs, forces no-key deterministic AI, checks occupied ports, waits for API readiness and stops only owned child groups. Production mode builds matching frontend assets. No unsafe reset option.

Changed implementation: `apps/api/app/main.py`, new `core/http_limits.py`, new `tests/test_m6.py`; `apps/web/src/App.tsx`, its tests, AI advisor/tests, conflict hook, map and shared colors, scenario planner/results, styles, new `components/FeatureBoundary.tsx`; new `scripts/demo.py`. Updated README, roadmap, architecture, API/AI/responsibility/product/source/demo documents; added hackathon script, limitations, presentation outline and this report. Existing domain algorithms, versions, data model and fixture bytes are unchanged.

## Commands and actual results

Commands below run from the repository root unless otherwise stated. Timings are observations, not guarantees.

| Check / command | Actual result |
| --- | --- |
| `.venv/bin/python -m pytest apps/api/tests -q` with `PYTHONPATH=apps/api` | **212 passed**, 1 existing Starlette/httpx warning; 17.87 s final main run |
| Targeted `apps/api/tests/test_m6.py` | **7 passed**: integrated replay/no source mutation/idempotency/integrity; two oversize-body paths; three foreign origins; scenario/question injection |
| `npm test --prefix apps/web -- --run` | **57 passed, 9 files** |
| `npm run typecheck --prefix apps/web` | Passed |
| `npm run build --prefix apps/web` | Passed, with remaining map-size advisory; production helper also built successfully |
| Fresh virtualenv → `python -m pip install -r apps/api/requirements.txt` | Pinned install succeeded, 30 packages; no requirement/lock changes |
| `python -m pip check` in existing and fresh environments | No broken requirements; this is not a vulnerability scan |
| Fresh copied source, new npm cache, `npm ci --prefix apps/web` without inherited Node injection options | Installed 197 packages; isolated **57 tests**, typecheck and build passed |
| Fresh virtualenv against isolated copied backend source: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=apps/api /private/tmp/civicplain-m6/api-venv/bin/python -B -m pytest apps/api/tests -q -p no:cacheprovider` | **212 passed**, 1 warning, 16.63 s; additional fresh-interpreter run against checkout also passed |
| `npm audit --prefix apps/web --json` | Current advisory service reported **0 vulnerabilities**; not a code penetration test or Python package advisory scan |
| `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m4.py` | All six existing saved evaluations replayed; integrity `ok`, FK violations `0` |
| `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m5.py` | Fresh isolated estimate/conflict/comparison explanations, no-key fallback, insufficient-evidence handling, five traceable audits; source tables unchanged |
| Four `scripts/create_*_fixture.py` generators and before/after file hashes | All four fixture/manifest pairs identical; no synthetic values changed |
| Canonical count/hash of all original DB tables + `PRAGMA integrity_check`, `PRAGMA foreign_key_check` | 17/17 unchanged; `ok`; no FK rows |
| Helper `--help` and occupied QA ports | Help passed; occupied port refused with exit 2 and clear recovery, preserving existing processes/data |
| Changed Python syntax parsing, Markdown file-link targets and `git diff --check` | Passed; frontend source/build credential-marker scan had no matches |

Regression coverage includes endpoint validation, persistence and restart, Decimal costing/rounding, missing measurements, geometry/time boundaries, deterministic conflicts, immutable/replayable scenarios, budgets, AI citation/hash/caveat validation, provider errors/timeouts/429, reduced audits and non-mutation. Frontend coverage includes API/error states, selection, map failure/list fallback, estimates, findings, scenario editor/comparison, advisor/fallback, source focus and repeated navigation.

During implementation, a new test initially assumed hash-sorted comparison results followed input order; fixed its oracle to match by scenario ID. A new UI test used a TypeScript-incompatible Testing Library option; removed that option and reran tests/typecheck/build. Both were introduced test issues, not altered domain results. No unresolved test failure remains. No lint command is configured.

## Actual browser and end-to-end checks

Used a real in-app browser against isolated **development API 8016 / frontend 5186**, then **production API 8017 / preview 5187**. Requests went through the actual frontend HTTP client and working servers. Default viewport 1280×720 and responsive 390×844 were inspected; production console query returned no errors/warnings at inspection.

| Workflow | Verified observation |
| --- | --- |
| Local startup, map and selection | Both helper modes started, seeded and passed health readiness. Map rendered 24 roads and local WebGL worker. Clicking a rendered line selected R-008; guide and keyboard road buttons selected loaded records. R-001 highlighted with rating 3/10, date, dimensions and provenance. |
| Alternatives and saved estimate | Three alternatives previewed. Actual Save/GET opened R-001 resurfacing: $36,000 + $6,000 + $2,500 = $44,500 subtotal, $8,900 contingency, **$53,400 base**, **$44,760–$66,360**, **5 preliminary days**. Poor-condition rule still marks resurfacing not indicated; no suitability override. |
| Existing conflict evidence | Seven project records, eight findings and ten incomplete checks. Guide opened actual reopening risk with highlighted work zones, shared road, polygon overlap, zero spatial distance, road April 1–8 and utility April 10–15, two-day gap. |
| A/B/C saved comparison | Selected all three and used real compare/evaluation APIs. All costs equal; $60,000 synthetic budget gives $6,600 base headroom and −$6,360 high sensitivity. Existing and hypothetical findings distinguished; A reopening, B sequencing, C concurrent/multiple closures. No priced savings. |
| Scenario create and evaluate | Created `M6 browser review plan` via actual form/API with budget $60,000, April 1–May 1 horizon and R-001 resurfacing. Saved/reloaded/evaluated at $53,400 base; missing action dates/closure and four incomplete checks remained unknown. Only isolated user-created records were written. |
| Advisor and provenance | Explained estimate, conflict and comparison with citations. Inspect Source expanded evidence and focused its source element. Optional emphasis with no configured provider returned deterministic fallback; unsupported information stayed unknown. |
| Real timeout/retry | Temporarily paused only the owned demo API. Explanation hit the real 10-second client timeout and displayed an understandable error; resumed API, clicked Retry and received deterministic evidence. Server resumed and owned processes were shut down after verification. |
| Invalid/missing input | Keyboard-selected R-004, requested/saved resurfacing; actual 422 for missing authored length displayed clearly. It did not fabricate geometry-derived dimensions or persist an invalid estimate. |
| Responsive/keyboard | Mobile document width stayed 390 px; road detail stacked. Comparison scrolled inside its 330 px focusable region, with keyboard ArrowRight. No document-level horizontal overflow. Keyboard selection and citation focus verified. |
| Production modules | Built preview loaded actual map/guide and lazy scenario comparison successfully. Final comparison screenshot retained as review evidence. |

Automated tests cover map initialization failure/list fallback; no GPU-failure injection was performed in the browser. No OS-wide network disconnect, live paid provider, screen-reader audit, cross-browser matrix or measured three-minute rehearsal was performed. Baseline map/assets and deterministic advisor make no external network requests. API outage was genuinely exercised; provider outages were mocked.

## Performance observations

Host: macOS 14.5 arm64, Python 3.12.5, Node 24.5.0, npm 11.6.0. Five warm loopback HTTP samples per operation on the 24-road/seven-project fixture, one local process and no concurrent load. Deduplicated saved evaluations were warm. These measurements do not establish cold startup, map frame rate, mobile latency, percentile SLA or citywide scaling.

| Operation | Median / maximum observed |
| --- | --- |
| Road GeoJSON | 11.49 / 12.43 ms |
| Full project conflict analysis | 17.10 / 19.64 ms |
| Scenario A evaluation | 23.98 / 24.16 ms |
| Three-scenario comparison | 4.86 / 17.21 ms |
| Deterministic evidence explanation | 30.09 / 30.82 ms |

Build artifact sizes: shell **272.84 kB raw / 83.08 kB gzip** versus baseline combined entry 1,368.43 / 379.23; deferred RoadMap **1,068.58 / 290.07**, ScenarioPlanner **33.04 / 8.78**, CSS **102.27 / 17.71**, local worker **519.37 kB raw**. This is deferred loading, not a claim the total map payload vanished. MapLibre retains Vite's >500 kB advisory. Avoided project-source geometry reload on highlight changes. No new large dependency or speculative caching was added. **Cold map readiness within three seconds remains unmeasured.**

## Targeted security and responsible-AI review

Reviewed server settings/CORS, SQL construction and parameters, configured DB path, errors/logging, frontend environment usage, provider construction/budgets/projection and audit writes. Fixed browser mutation-origin and request-body bounds. Runtime binds loopback; generic database failures expose sanitized envelopes/request IDs rather than raw SQL. DB path is server configuration, not a request-supplied file path. Dynamic query fragments use fixed allowlists and values remain parameterized. Existing geometry/reference/interval/budget validators remain passing. No unrestricted mutation tool is exposed to AI.

No credential was obtained or paid API called. Frontend consumes only its API base URL; no provider key is bundled. Helper strips inherited frontend variables and provider credentials and rejects secret-shaped frontend configuration before build. Public-facing authentication, authorization, encryption, general request rate limits, browser extensions/local malware and malicious administrators remain outside these guards. No penetration test or Python advisory scan was performed. npm's current advisory response was zero; this is not a production security certification.

All four injection surfaces are tested: road notes, utility/project descriptions, scenario names/descriptions and user questions. Provider receives only a bounded, allowlisted numeric/enum/fact package; narrative, raw question, credentials and free-form geometry are excluded. Money/date/unit/prose additions, unknown citations, altered hashes and omitted mandatory caveats fail validation. Provider failures fall back; source corruption fails closed. Failed output is never displayed as verified guidance. Optional AI can only select fixed fact/template references; server renders authoritative values. Calculations, budgets, scenarios and projects cannot be approved or modified by the model. Reduced audits trace evidence/request/method versions without raw prompts or keys.

Validated facts, deterministic explanation and optional provider emphasis are visibly distinguished. Synthetic provenance and missing utility/lifespan warnings survive all three evidence types. No monetary coordination benefit was added. Tests establish these safeguards for covered cases; **they do not guarantee perfect hallucination prevention, source truth, semantic completeness, physical safety or prompt-injection immunity**. Live-provider account, billing and latency remain unverified.

## Final acceptance checklist

All checks apply to the local bounded MVP, with the explicit scope and unrun checks above.

| # | Acceptance criterion | Result / evidence |
| --- | --- | --- |
| 1 | M1–M5 integrated | Pass — actual browser road → estimate → conflict → scenario → advisor |
| 2 | Main workflows end to end | Pass — dev full workflow and persisted create/evaluate; production map/comparison |
| 3 | Frontend/backend startup reliable | Pass — both isolated helper modes, health wait, installed-dependency rebuild |
| 4 | No known critical crashes | Pass in tested local flows — regression and browser checks; coverage limits documented |
| 5 | Reproducible fixtures | Pass — idempotent seed, fresh environments, eight matching file hashes |
| 6 | Road/map selection | Pass — rendered map click, guide, keyboard list and highlight |
| 7 | Deterministic repair estimates | Pass — regression, saved replay and exact browser breakdown |
| 8 | Tested conflict accuracy | Pass — spatial/time boundary regression and actual fixture evidence |
| 9 | Reproducible comparisons | Pass — immutable snapshots/replay and A/B/C display |
| 10 | Evidence-grounded AI within safeguards | Pass — validation/injection/audit suites; live provider unrun |
| 11 | Offline fallback | Pass — actual no-key fallback, local assets; mocked provider network failures |
| 12 | Synthetic labeling | Pass — fixture metadata, map/details, estimate and hypothetical scenario screens |
| 13 | Navigation | Pass — guide, primary navigation, retained editor and working citation links |
| 14 | Usable polished presentation | Pass — desktop/mobile inspection, readable tables/warnings/focus; not accessibility certification |
| 15 | Backend suite | Pass — 212 |
| 16 | Frontend suite | Pass — 57 across 9 files |
| 17 | Typecheck/build | Pass — current and clean installs |
| 18 | SQLite integrity | Pass — integrity ok and FK 0, original and isolated databases |
| 19 | Core browser demo | Pass — interaction/request evidence described above |
| 20 | Accurate setup | Pass — isolated pip/npm install and both helper modes |
| 21 | Demo script | Pass — HACKATHON_DEMO exact records, values, fallback and recovery |
| 22 | Limitations | Pass — KNOWN_LIMITATIONS |
| 23 | Final QA | Pass — this actual-results report |
| 24 | Presentation outline | Pass — eight-part PRESENTATION_OUTLINE, no fabricated savings/adoption |

## Remaining issues and handoff

**Critical/high local demo bugs: none known after verification.** Medium production/engineering blockers: synthetic/unvalidated data, absent identity/authorization, incomplete utility coverage, planning-only rates/calendars and no live operational deployment. Low local issues: map chunk advisory, TestClient deprecation, limited history/editor persistence and unmeasured cold map performance. See KNOWN_LIMITATIONS for ranked effects and unrun checks.

Start with `.venv/bin/python scripts/demo.py`, open the printed URL and follow HACKATHON_DEMO. Use a fresh isolated run for judging; preserve previous databases. The screenshot and saved test artifacts are review evidence, not runtime dependencies. The next step is rehearsal/presentation of this final MVP; no later product milestone was started. Public municipal use requires a separately authorized engineering/security/data program.
