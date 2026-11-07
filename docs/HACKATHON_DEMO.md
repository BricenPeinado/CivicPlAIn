# CivicPlAIn hackathon demonstration

Verified 2026-11-07. This is a local, synthetic planning prototype. No municipal observations, city adoption, safety certification, priced coordination savings or construction approval is demonstrated. The three-minute allocation below is a presentation script, not a measured rehearsal duration or verified event rule.

## Start, rehearse and recover safely

Install Python 3.12 and Node 22.12+ dependencies using README. From the repository root:

```sh
.venv/bin/python scripts/demo.py
```

Open http://127.0.0.1:5173/ and select **Explore Demo**. The helper explicitly seeds a **new** ignored `data/tmp/m6-demo-*/demo.sqlite3` on every invocation, forces deterministic AI, waits for API health, then starts Vite. It does not use the ordinary database or import local frontend credentials. It refuses occupied ports and stops only its child processes. Ctrl+C stops the demo and retains its database. No dependency installation happens during startup.

For occupied ports, choose both explicitly:

```sh
.venv/bin/python scripts/demo.py --api-port 8016 --web-port 5186
```

For built assets, including the local map worker:

```sh
.venv/bin/python scripts/demo.py --production --api-port 8017 --web-port 5187
```

The frontend build embeds its API address. Changing that address requires another build; the helper does this in production mode. Normal persistent startup remains available in README. Both helper modes were exercised. Dependencies must already be installed; first installation needs registry access.

There is deliberately **no delete/reset command**. Existing demo IDs can contain user edits and immutable histories. Rerun the helper to initialize a fresh isolated environment, preserving every previous file and record. Do not delete an existing database to recover or upgrade. Avoid editing A/B/C during judging; use a newly created hypothetical plan for editing demonstrations.

## Three-minute script and expected interactions

| Time | Interaction | Narration and expected state |
| --- | --- | --- |
| 0:00–0:25 | Explore Demo → **1. Inspect demo road R-001** | “These are fictional inputs. A planner is considering resurfacing; another team plans excavation nearby.” Map highlights the selected segment; detail says Poor, synthetic 3/10, 2026-10-01, authored 100 × 8 m and unknown utilities. |
| 0:25–0:55 | Below coordination, **Compare Repair Options** → **Save & inspect Resurfacing or rehabilitation** | Preview and saved breakdown show $53,400 base, $44,760 low, $66,360 high and five preliminary days. Point out that resurfacing is **not indicated** by the poor-condition demo rule; reconstruction is the screened candidate and still needs engineering review. This is a coordination comparison, not a treatment recommendation. |
| 0:55–1:25 | Guide → **2. Review potential pavement rework** | Both supplied work zones are highlighted. Existing-project evidence shows geometric overlap, shared R-001 and a two-calendar-day gap. “This flags a sequencing question, not confirmed pavement damage or a calculated loss.” |
| 1:25–2:15 | Guide → **3. Compare saved scenarios**; check Compare A, B, C; **Compare selected (3/3)** | Columns appear A/B/C. All base costs equal $53,400. Base fits the $60,000 synthetic roadwork budget; high sensitivity exceeds it. A has reopening risk; B retains sequencing review; C retains concurrent-work and multiple-closure findings. “Coordination is a review opportunity; no discount or avoided rework has been priced.” |
| 2:15–2:45 | **Explain tradeoffs** → an **Inspect source** link | Server-rendered facts cite saved evaluations and hashes. Missing lifespan and utility depth/coverage remain explicit. Explain the deterministic calculation/optional AI separation. Source link expands evidence and moves keyboard focus. |
| 2:45–3:00 | Check **Request configured AI emphasis**, then **Explain tradeoffs** again | Default isolated demo returns DETERMINISTIC FALLBACK / not configured with authoritative values intact. Close with qualified human review and future validated data integrations. |

The guide only navigates loaded records. It does not seed through HTTP, create scenarios, invent results or reset records. Its road/rework actions are disabled if those records are absent. Normal navigation remains available.

## Exact records and verified numbers

Snapshot `demo-m1-v1`; road `demo-r-001`; assessment `demo-r-001-assessment-2026-10-01` with latest dated rating **3**, **2026-10-01**; option `demo-resurface`; existing projects `demo-road-project` and `demo-utility-project`; scenarios `demo-scenario-a`, `demo-scenario-b`, `demo-scenario-c`. Analysis, finding, estimate and evaluation IDs are returned by working APIs; choose their current saved references rather than pasting a machine-specific evaluation hash.

Sources: `demo-assumptions-v1`, `demo-maintenance-assumptions-v1`, `demo-project-assumptions-v1`, plus frozen scenario assumption sources. The four checksum manifests in `data/demo/` identify reviewed fixture bytes. No fixtures or calculation versions changed in M6.

| Evidence | Verified value / qualification |
| --- | --- |
| Roads and projects | 24 schematic roads, six in each condition category; seven fictional projects |
| Full existing-project screen | 8 findings; 10 incomplete pair checks; 16 candidates / 21 possible pairs |
| R-001 resurfacing scope | 100 m × 8 m = 800 m², authored dimensions independent of schematic geometry |
| Base estimate components | $36,000 bundled roadwork + $6,000 mobilization + $2,500 traffic = $44,500 subtotal; $8,900 contingency; $53,400 total |
| Rate sensitivity | Bundled rate $36 / $45 / $58.50 per m²; fixed allowances unchanged; totals $44,760 / $53,400 / $66,360 |
| Preliminary duration | ceil(800/600) = 2 active + 2 setup + 1 curing = 5 days; no calendar date inferred |
| Existing road / utility intervals | Road [2027-04-01, 2027-04-08); utility [2027-04-10, 2027-04-15); gap 2 calendar days |
| A road interval / hypothetical result | [2027-04-01, 2027-04-08); reopening_risk |
| B road interval / hypothetical result | [2027-04-15, 2027-04-22); sequencing_review, gap 0; adjacency is not overlap |
| C road interval / hypothetical results | [2027-04-10, 2027-04-17); concurrent_work + multiple_closures |
| Each scenario | Same $44,760 / $53,400 / $66,360; five preliminary days, seven supplied calendar days, seven declared lane-closure-days |
| Budget / headroom | $60,000 synthetic roadwork-only; low/base/high headroom $15,240 / $6,600 / −$6,360; high sensitivity over budget |
| Supported savings | **None quantified. Cost differences are zero.** Restoration, utility construction, delay and shared mobilization benefits are unpriced. |

Every plan explicitly replaces the original road-project snapshot only inside its hypothetical screen. Existing records remain intact. Scenario findings are hypothetical; the existing-project screen also uses fictional source records. Unknown utilities never become known because a selected two-project scope has no incomplete checks.

## Offline and failure procedure

- Baseline operation uses local SQLite, local map assets and deterministic templates. No paid API or external tiles are required. After installation, leave the optional AI provider disabled. Checking optional emphasis demonstrates `fallback/not_configured`; a configured provider outage also falls back, as tested using mocks.
- If the API is slow/unavailable, preserve the screen, read its error, restore the API and use the relevant **Retry**. A real paused-API timeout and retry were verified. Do not repeatedly click Save: estimates are intentionally append-only and an interrupted request may already have persisted.
- If startup fails, inspect the clear terminal message. Confirm the documented dependencies and unused local ports, then rerun. The helper leaves existing servers and databases alone. A frontend build/typecheck failure prevents launching the production demo.
- If map/WebGL rendering fails, use **Keyboard accessible road list**, search R-001 and press Enter. Domain panels use the same API records. Automated map-failure tests cover this path; no remote basemap is necessary.
- If data is missing or previously edited, start a fresh isolated helper run. Do not erase user records, fabricate replacement values, or conceal unavailable metrics.
- If a source fails validation, the advisor returns an error rather than endorsing an inconsistent snapshot. Provider fallback cannot repair missing or corrupted source evidence.

## Responsible-AI talking points and judges' questions

**What does AI do?** Optional AI selects bounded fact/template references for emphasis. The server renders all numbers, units, dates and caveats. Default offline explanations are deterministic. No model computes estimates, screen geometry, optimize schedules, approve work or mutate project records.

**How is this more than a map?** The same selected road flows through transparent costing, reproducible spatial/date screening, saved hypothetical alternatives, budget sensitivity, source citations and audit metadata.

**Does C save money?** This demo does not quantify a saving: all three selected resurfacing actions cost the same. A potential coordination benefit requires separately reviewed quantities, restoration scope, rates and team confirmation.

**Why not automatically choose B?** Deferral may be inappropriate for the actual road condition. B retains sequencing review; affordability is independent of suitability and safety. No universal winner is computed.

**Can an injected project note change the answer?** Narrative notes and raw questions are excluded from provider context. Strict selection/citation/hash/caveat validation rejects unsupported output; invalid provider output falls back. These tested restrictions do not prove source truth or perfect hallucination prevention.

**How do you reproduce a result?** Saved inputs retain source contents, assumptions, quantities, parameters, library/method versions and hashes. Pure services replay frozen calculations; SQLite snapshots are append-only through application triggers. Hashes are not cryptographic source signatures.

**What is missing before city use?** Verified municipal/utility ingestion and coverage, qualified engineering validation, identity/authorization/tenancy, privacy/retention/backup controls, operational deployment/security review and municipal procurement processes. This local demo has none of that authorization.
