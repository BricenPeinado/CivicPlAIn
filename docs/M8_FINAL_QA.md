# Milestone 8 final QA — 2026-11-08

**Release gate: BLOCKED / NOT COMPLETE.** Passing regressions do not close positive source/review gates or certify the full release matrix.

## Executed verification

Local branch and complete tracked diff were captured and change inventory inspected; existing uncommitted M8 work preserved. AGENTS, roadmap, shared contracts and stage reports were collected for this audit. This is not a claim of a complete line-by-line security review of every untracked module.

| Check | Actual result |
|---|---|
| Complete backend suite | `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q`: 503 passed, 341 library warnings, 29.95s |
| Complete frontend suite | `npm test --prefix apps/web`: 141 passed / 22 files |
| TypeScript | `npm run typecheck --prefix apps/web`: PASS |
| Production build | `npm run build --prefix apps/web`: PASS; large MapLibre chunk advisory remains |
| Whitespace | `git diff --check`: PASS |
| SQLite | Read-only integrity_check: ok; foreign_key_check: zero violations; 4.330s |
| Saved replay | `scripts/verify_m8_6.py` replayed 2 estimates, 4 priorities, 2 screenings, exact aggregate hash 38163a207d374a1f854c5b50554613e198d62f6cbf591eae08edbbe93a2e52c5 |
| Fresh install | NOT RUN; existing installed dependencies used. No clean-install claim |
| Browser | Existing localhost:5173 opened and rendered 829 street rows, attribution and unknown-utility disclosure. Planning summary returned Not Found from its existing running backend |

Replay used ignored `data/tmp/m86-integration-pilot.sqlite3`, base `nyc-4620b9e30c1c0bd5be4252fe27999c80`, explicit reference date 2026-11-08. Aggregate output is ignored `data/processed/m87-replay.json`. No new migration, import, approval, estimate or screening was created. Replay checks frozen calculation consistency, not independent authenticity or fresh-download equivalence of government data. Original source reacquisition and full ingestion reproducibility were not rerun.

## Performance

Twenty sequential in-process TestClient decision-summary reads on the bounded 4,150-road pilot: nearest-rank p95 **0.525 seconds** (range 0.393–0.549s). This exceeds the original 500ms target. This is server/in-process latency, not HTTP/network/browser timing; no guessed map FPS or cold-start duration. Full new-endpoint, five-cold-map and twenty-calculation performance matrix remains UNVERIFIED. Existing regression tests cover pagination, viewport refinement guards and explicit history truncation; not independently load-tested citywide.

## Workflow evidence and remaining verification

| Workflow | Evidence / current status |
|---|---|
| A actual road/source | Existing M8.1/M8.6 reports and current regression suite; full browser walkthrough not repeated in this audit |
| B ambiguous/missing condition | Regression PASS; pinned base has 0 eligible whole-road assessments / 4,150 Unknown, never Good by missingness |
| C repair estimates | Two frozen technical-QA estimates replay; explicit assumptions, no municipal pricing validation |
| D priorities | Four frozen runs replay; review policies do not establish physical risk or verified maintenance need |
| E permits | Administrative/candidate separation tested; no accepted physical footprint or actual schedule |
| F coordination | Two screenings replay; hypothetical example has one opportunity / six indeterminate pairs, not a verified actual conflict |
| G alternatives | Existing frozen schedule/policy/treatment alternatives replay and regressions pass |
| H unsupported scenarios | Explicit unavailable/indeterminate behavior covered by regressions; general official scenario engine unavailable |
| I original synthetic | Complete backend/frontend regressions PASS; full manual synthetic browser workflow not repeated |
| J no-key/injection | Complete AI regression suite PASS; previous M8.6 actual fallback evidence retained; not a new live-provider certification |

Full end-to-end browser matrix, screen-reader/keyboard/responsive/200%-zoom repeat, clean-install startup and production-browser verification remain UNVERIFIED. Earlier stage browser evidence is historical supporting evidence, not a fresh M8.7 pass. No original service was restarted or database deleted to hide the running-version mismatch.

## Findings and severity

- **High / release blocker:** existing browser runtime frontend/backend mismatch: new decision-summary request returns Not Found. The current factory tests expose the endpoint; inspect running process version/configuration and restart a matched isolated pair, then repeat A–J before release. Root cause is suspected stale runtime, not established by this audit.
- **High / evidence blocker:** whole-road pavement/classification applicability and positive real-work/municipal-cost/policy review requirements remain unresolved.
- **Medium:** summary p95 exceeds original 500ms target even in-process; full cold/concurrent performance matrix unverified. Earlier reports document client timeouts.
- **Medium:** clean installation, complete current browser matrix and production restore rehearsal not demonstrated.
- **Low:** dependency deprecation warnings and large frontend chunk advisory remain.

## Matches, capabilities and responsible AI

Earlier owner-reviewed pilot: 5 accepted partial pavement observations / 8,726, across 5 roads; 8,721 observations unresolved. Four project-policy observation grades Good, one Unknown; no supported whole-road current rating. These links are not transferred to a different base. Current larger-permit base: 6,052 candidate / 16,995 unlocated permits of 23,047; zero accepted work footprints or actual schedules. Matching precision of unreviewed candidates is unknown.

Enabled contracts: immutable official snapshot inspection/provenance; conservative condition history; reviewed/candidate associations; explicit-assumption patch/resurface estimates; explicit-policy review queues; supplied-plan spatial/date screening, alternatives and human notes; grounded deterministic/optional saved-result explanation. Runtime availability additionally requires matched deployed local processes and proper schema/pin.

Unavailable: automatic verified road-wide condition coverage in current pilot; authoritative NYC price catalog; independently verified work schedules/utility/depth inventory; excavation clearance; reconstruction; general official scenario CRUD/evaluation, portfolio optimization, autonomous approval/spending. Missing data stays unknown. AI selects validated fact references and server-rendered numbers; source prose cannot supply instructions or missing measurements. Tests support these boundaries; this audit does not independently establish every real-world numerical input's truth.

## Release decision and Milestone 9 recommendations

Do not mark Milestone 8 complete. First resolve the matched-runtime/browser matrix and installation/recovery/performance checks; then obtain authorized source/policy review for the positive evidence gates. Preserve frozen records and qualify all QA assumptions. Milestone 9 should prioritize reviewed feed/release compatibility and work evidence, validated municipal quantities/prices, bounded read performance, reproducible installation and operational recovery. Do not expand optimization or autonomous decisions before those foundations pass.

Files changed by this audit: this report, README and roadmap status only. Runtime reports remain ignored. No commit, push, deployment, dependency installation, database deletion, branch reset or history rewrite.
