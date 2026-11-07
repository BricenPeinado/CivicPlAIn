# M5 implementation and verification

Verified locally on 2026-11-07 on branch `feat/m5-responsible-ai`. M5 is complete within the bounded local-prototype scope below. M6 has not started. No commit, push, deployment, credential provisioning or paid provider request was performed.

## 1. Implementation summary

The existing React/FastAPI/SQLite modular monolith now explains saved repair estimates, saved conflict findings, and comparisons of two or three saved scenario evaluations. A contextual advisor also accepts bounded questions about roads, assessments, estimates, conflicts, projects and evaluations. The default path uses deterministic templates without a key or network. Optional OpenAI selects supported facts to emphasize; every displayed assertion is rendered by the server from validated typed fields or fixed review templates.

M1–M4 calculation engines, financial fixtures, schedules and immutable domain snapshots were preserved. The only existing regression-test changes update the expected additive schema version from 4 to 5. Existing views were extended rather than replaced.

## 2. Files created and modified

New backend files:

- `apps/api/app/schemas/ai.py`: strict requests, evidence, provider selection and public explanation contracts.
- `apps/api/app/services/ai/__init__.py`, `evidence.py`, `providers.py`, `explanations.py`: retrieval/projection, replay checks, optional provider, usage gate, selection validation, templates and orchestration.
- `apps/api/app/core/ai_repository.py`: immutable evidence projections, minimal interaction metadata and separate review notes.
- `apps/api/app/routes/ai.py`: reference-only AI endpoints and the human review-note endpoint.
- `apps/api/tests/test_ai.py`: 64 M5 tests, including parametrized adversarial and official-SDK mocked-HTTP cases.
- `scripts/verify_m5.py`: repeatable synthetic offline journey using a new temporary database.

Modified backend files:

- `apps/api/app/main.py`: dependency wiring, injectable provider/settings and routers.
- `apps/api/app/models/database.py`: additive migration 5, foreign keys and immutable audit triggers.
- `apps/api/app/core/planning_repository.py`: keyed assessment lookup.
- `apps/api/requirements.in`, `requirements.txt`: official OpenAI SDK and its pinned additional dependencies.
- `apps/api/tests/test_conflicts.py`, `test_planning.py`: schema-version expectations only.

New frontend files:

- `apps/web/src/types/ai.ts`: typed REST shapes.
- `apps/web/src/features/ai/AIAdvisor.tsx`, `ReviewNote.tsx`, `AIAdvisor.test.tsx`: contextual advisor, explicit human note form and component tests.
- `apps/web/src/services/ai.test.ts`: transport/reference boundary tests.

Modified frontend files:

- `apps/web/src/App.tsx`: road advisor and milestone label.
- `apps/web/src/features/estimates/RepairPlanner.tsx`: saved estimate explanation.
- `apps/web/src/features/conflicts/ConflictReview.tsx`: selected project/conflict explanation.
- `apps/web/src/features/scenarios/ScenarioResults.tsx`: evaluation/comparison advisors and review notes.
- `apps/web/src/services/api.ts`: centralized reference-only calls.
- `apps/web/src/styles.css`: existing-design advisor styling and scrollable fact lists.

Updated `.env.example`, `README.md`, and `docs/MVP_ROADMAP.md`, `ARCHITECTURE.md`, `AI_SYSTEM.md`, `RESPONSIBLE_AI.md`, `API_SPEC.md`, `DATA_MODEL.md`, `DEMO_PLAN.md`; added this report. No frontend dependencies or reviewed data fixtures changed. Runtime databases, generated builds and test data remain untracked.

## 3. AI architecture and data flow

Strict REST validation → existing repositories resolve references → `EvidenceBuilder` projects typed fields → context/hash/replay validation → deterministic default or optional provider → strict selection/citation/caveat checks → server rendering or deterministic fallback → atomic evidence/interaction audit persistence → existing REST envelope → React advisor.

The evidence package has version `ai-evidence-v1`, context references, content-derived evidence IDs, complete-record hashes, input hashes, calculation versions, dataset IDs, source-content revision hashes, facts with units/classifications, unknowns, limitations and synthetic flags. Frozen estimates replay M2; saved conflicts replay their complete M3 analysis; evaluations replay M4. The unchanged M4 comparison service rejects incompatible bases. Current road/assessment/project contents are hashed rather than represented as immutable historical observations.

A stable prefix retains at most 96 facts within 48,000 canonical JSON bytes before the snapshot-hash field. Missing-data notices are collected before truncation. Truncation counts are explicit; oversized mandatory metadata is rejected. Empty projections return insufficient evidence without contacting a provider. Source notes, descriptions, assumption prose, arbitrary geometry and raw questions do not enter model context.

No architectural deviation from the monolith/REST/domain-service boundaries was introduced. The explicit M5 request replaces the older unimplemented `/explanations` proposal with `/api/v1/ai/*`; API_SPEC and DATA_MODEL reconcile that change. The generalized future AuditEvent stream remains distinct from the implemented scoped AI/review tables.

## 4. Provider model and configuration

Official Python SDK `openai==2.54.0`, `AsyncOpenAI.responses.parse`, strict Pydantic Structured Outputs, official HTTPS base URL, no tools, `store=false`. The configurable default is `gpt-5.4-mini-2026-03-17`, checked against the [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini); the response mechanism follows [official Structured Outputs guidance](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

| Server setting | Behavior |
| --- | --- |
| `CIVICPLAIN_AI_PROVIDER` | `deterministic` default; `openai` enables optional provider selection |
| `OPENAI_API_KEY` | Optional server-side secret; absent during verification |
| `OPENAI_MODEL` | Configurable model identifier; default above |
| `CIVICPLAIN_AI_MAX_CALLS_PER_HOUR` | Default 20; allowed 0–100; per API process |

Export variables in the API shell; there is no dotenv loader. Never place a key in a frontend variable. Requests also require `mode=ai` to attempt the configured provider. Defaults are deterministic even with a configured key. Fixed defaults: 8-second SDK/wall deadline, zero automatic retries, 1,200 output tokens, maximum two concurrent provider calls. Failed attempts count. Restarting resets local usage counters; these are not a financial ceiling. Provider project budgets require separate setup. Status reports configuration, never proof of connectivity or account access.

## 5. Structured output contract

The model may return only an exact evidence hash, the `bounded_summary` template ID, 1–12 `{fact_id,evidence_id,template_id:fact_value}` selections, all four mandatory limitation codes, and one context-compatible review code. Extra fields are forbidden. There are no provider fields for invented prose, values, dates, units, SQL or tool calls.

The public `Explanation` includes ID/task/hash/summary; findings with claim text, fact and evidence references and classification; tradeoffs; uncertainties; missing information; suggested review; citations and the bounded evidence projection; provider mode; validation result; fallback reason; model label; timestamp; source classification; mandatory human-review flag; warnings; audit reference. The server retains all projected facts and mandatory caveats regardless of selected emphasis. Record facts and deterministic calculations are separated in the UI; conditional/review statements use fixed templates.

## 6. Validation and safety controls

- Strict input cardinality/length/enum/extra-field validation; no client-supplied authoritative evidence or money.
- Source/hash/context checks and replay before explanation; failed integrity returns 409 rather than explaining inconsistent results.
- Exact fact-to-evidence membership, requested-context membership, evidence hash, template, review-code and complete-caveat validation. Fabricated citations and duplicated selections fail closed.
- Numerical/date/unit claims are server-rendered from the catalog. Provider attempts to submit alternate amounts, dates or units fail the strict schema even with a genuine citation.
- Unknowns, truncation, synthetic status, utility uncertainty and human review remain server-controlled. Potential rework is never quantified as confirmed damage or municipal savings.
- Road notes/project descriptions and other free source narrative are excluded. Local conservative question routing sends only a resolved intent to a provider. Unsupported prediction, approval, secret and instruction-override requests return insufficient evidence.
- No SQL, Python, web research, mutation tools, autonomous execution or model path to source-record writes. Separate explicit human notes cannot authorize work.
- Provider errors are sanitized categories, not raw response/error logs. Audit storage failure returns 503.

These are tested restrictions, not universal hallucination prevention, source truth verification or engineering certification. See section 12 and RESPONSIBLE_AI.

## 7. Fallback behavior

No-key default requests return `provider_status=deterministic`. An explicit AI request with no configured provider returns `fallback/not_configured`. Timeouts, rate limits, outages, refusal/incomplete output, schema/citation failures, missing caveats, usage exhaustion and concurrent saturation use deterministic templates and a sanitized reason. Failed output is never partially displayed. Source-integrity failures return an error; unsupported questions and empty projections return `insufficient_evidence` without a model call.

All three explanation workflows and missing-data summaries work offline. The UI labels deterministic mode separately from actual AI-selected emphasis and fallback. Future delay effects are unavailable unless independently calculated/supplied; the assistant does not invent a hypothetical result.

## 8. API endpoints

All paths below use `/api/v1`, existing `{data,meta}` envelopes and correlation IDs.

| Method/path | Body / function |
| --- | --- |
| POST `/ai/explain-estimate` | `{estimate_id,mode?}` |
| POST `/ai/explain-conflict` | `{conflict_id,mode?}` |
| POST `/ai/explain-scenario-comparison` | `{evaluation_ids:[2–3 distinct IDs],mode?}` |
| POST `/ai/ask` | `{context:{type,record_ids},question,mode?}` |
| GET `/ai/status` | Configuration and limits; no provider probe |
| GET `/ai/interactions/{id}` | Minimal saved audit metadata |
| POST `/scenario-evaluations/{id}/reviews` | Explicit alias/note/limitation codes; immutable note, `authorizes_work=false` |

Non-comparison contexts require exactly one ID. IDs are 1–150 nonblank characters, questions 1–500. Unknown references return 404; invalid inputs/oversized mandatory evidence 422; incompatible or unverifiable snapshots 409; unavailable persistence 503. The existing prototype has no authentication/authorization system to extend and must remain local.

## 9. Frontend AI functionality

Functional estimate, conflict and comparison explanation buttons; road/project/evaluation advisors; contextual question form; explicit optional-AI toggle; loading/error/retry; synthetic and fallback labels; separated calculation/record facts; uncertainty/missing information; source links, exact hashes and typed evidence details; human-review text; How AI works and configuration status. Explicit review notes have a separate form and success/error state. Context changes abort pending requests and discard stale responses. No client-side financial arithmetic or fabricated model response was added.

Manual browser verification used the actual REST API on loopback ports 8015/5185 and a separate temporary synthetic database. It exercised selected poor-condition road → saved resurfacing estimate → potential utility rework conflict → three-scenario comparison → Explain tradeoffs → evidence inspection → missing-data warning → How AI works/status. Explicit optional-AI requests demonstrated no-key fallback for the estimate and comparison. The existing user servers/database were left intact. Browser tests did not make a live OpenAI request. The future-delay insufficient-evidence and human-note submission paths are covered by automated tests; the repeatable API demo also checks future-delay behavior.

## 10. Audit logging behavior

Migration 5 adds `ai_evidence`, `ai_interactions`, `review_events`, foreign keys, and update/delete rejection triggers. It rewrites no existing domain payload. Evidence is deduplicated by canonical hash. Each successful explanation stores task/context/source IDs, evidence hash, attempted model/provider where relevant, output mode, validation/error category, timestamp, request correlation, contract version and output hash. The reduced immutable evidence projection supports traceability.

Raw questions/prompts, provider prose, hidden reasoning, secrets, contact details and geometry are not stored in interaction metadata. Explicit human note text/alias is stored separately, never sent to the model, and does not verify identity or grant approval. There is no general cross-module audit retrofit, production retention policy or cryptographic audit guarantee. Validation errors before an explanation do not create an interaction record.

## 11. Tests and actual results

Baseline before implementation: backend **141 passed**, frontend **44 passed / 7 files**, typecheck/build passed. Existing Starlette deprecation and Vite bundle-size advisory were present.

Final commands and outcomes:

| Command/check | Actual outcome |
| --- | --- |
| `PYTHONPATH=apps/api .venv/bin/python -m pytest apps/api/tests -q` | **205 passed**, 1 existing Starlette/httpx deprecation warning, 15.86 seconds |
| `npm test --prefix apps/web` | **54 passed / 9 files** |
| `npm run typecheck --prefix apps/web` | Passed |
| `npm run build --prefix apps/web` | Passed; existing MapLibre-containing chunk-size advisory |
| `.venv/bin/python -m pip check` | No broken requirements |
| `.venv/bin/python -m compileall -q apps/api/app` | Passed |
| `git diff --check` | Passed |
| Lint | Not run: repository has no configured lint command |
| `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m5.py` | Passed on new temporary DB: 5 audit entries, source tables unchanged, integrity OK, no FK violations |
| `PYTHONPATH=apps/api .venv/bin/python scripts/verify_m4.py` | Passed on original local DB: 6 immutable evaluations replay with matching hashes; integrity OK; no FK violations |
| Read-only original SQLite table hash comparison | All **17 original table hashes unchanged**, integrity OK, no FK violations |

The clean frontend copy at `/private/tmp/civicplain-m5-clean-nzfgxfml/apps/web` contained only declared package/config/source inputs and reviewed fixtures, with no inherited parent node_modules. An initial offline `npm ci` failed because `@types/node@22.20.5` was not cached (`ENOTCACHED`). A normal registry-backed `npm ci --prefix /private/tmp/civicplain-m5-clean-nzfgxfml/apps/web --cache /private/tmp/civicplain-m5-npm-cache --no-audit --no-fund` installed 197 packages successfully. Its independent test run passed **54 tests / 9 files**; typecheck and production build passed. No manifest or lockfile repair was needed.

M5 backend cases cover all seven contexts, unknown records, strict body limits, immutable source consistency/replay, changed live catalogs, tampered hashes, incomplete inputs, synthetic provenance, deterministic truncation/empty evidence, incompatible comparisons, malformed/fabricated citations, money/date/unit/prose substitutions, warning suppression, fabricated approval, source-note/project-description injection, unsupported questions, no key, timeouts, 429/unavailability, output limits, usage ceilings, immutable review/audit storage and sanitized storage failure. The actual official SDK is exercised through `httpx.MockTransport` for success and failure responses, checking strict schema, tokens, no tools, no retries and no secrets in model input. Tests make no paid calls.

Frontend cases exercise three explain-button contexts, question/mode requests, disclosures/status, source references, loading/error/retry, stale-context cancellation, insufficient/truncated output, review notes and reference-only transport. The full existing suites retain M1 map/list, M2 costs, M3 conflicts and M4 scenario regression coverage.

## 12. Security and reliability limitations

- Live OpenAI credentials, account entitlement, latency and billing were **not verified**. A real server integration exists and is SDK/HTTP-mock tested; no live-service success is claimed.
- Per-process rate/concurrency limits are not distributed or durable. Restarting resets them; no exact dollar cap is enforced locally.
- Source hashes/replay detect inconsistency, not truthful measurements or malicious database administrators. Existing fixtures are fictional. Current source ingestion remains synthetic-only.
- Allowlisted templates and excluded narrative reduce injection exposure but omit free-text nuance. Conservative intent matching may decline valid phrasing or show broader attached evidence. No universal entailment or injection guarantee is claimed.
- A capped projection may omit facts; the user must inspect original snapshots when truncation is flagged. Unknown utility coverage never establishes safe excavation.
- Review aliases are unverified; the local API is unauthenticated. No tenant isolation, production access control, retention policy, distributed usage budget or deployment was added.
- Outputs are preliminary planning explanations; no physical safety, future deterioration, delay effect, regulatory compliance, universal optimum, approved spending or confirmed loss follows from them.
- Existing Starlette deprecation and frontend chunk advisory remain. Comprehensive performance, accessibility and demo-presentation acceptance belong to M6 and were not claimed complete.

## 13. Acceptance criteria

| # | Criterion | Result and evidence |
| --- | --- | --- |
| 1 | Explanation service implemented | PASS — validated evidence/provider/render/audit orchestration |
| 2 | Real provider integration exists | PASS — official SDK Responses Structured Outputs; mocked HTTP verified; live account unverified |
| 3 | Server-side secrets | PASS — backend settings only, secret repr hidden, no frontend key |
| 4 | Application operates without a key | PASS — deterministic default, complete tests and browser journey |
| 5 | Offline fallback works | PASS — estimate/conflict/comparison and missing-input tests/demo |
| 6 | Traceable evidence | PASS — exact records, source hashes, versions, typed facts and saved projections |
| 7 | Structured validation | PASS — strict Pydantic selection and public response contracts |
| 8 | Invalid citations rejected | PASS — fabricated, mismatched and out-of-context selection tests |
| 9 | Unsupported numerical claims rejected | PASS — money/date/unit extra fields rejected; catalog rendering only |
| 10 | Missing information visible | PASS — retained before trimming; UI disclosures and empty/truncated tests |
| 11 | AI cannot modify municipal records | PASS within implemented boundary — no tools/writer access; source-table equality tests |
| 12 | Estimate explanations work | PASS — exact cost components/ranges/duration and browser inspection |
| 13 | Conflict explanations work | PASS — projects/roads/geometry rationale/dates/review; no confirmed loss |
| 14 | Comparison explanations work | PASS — three saved evaluations, costs/headroom/schedules/findings/missing data |
| 15 | Questions bounded | PASS — local intent, limits, unsupported/unsafe topics insufficient without model call |
| 16 | Frontend advisor integrated | PASS — existing road/estimate/project/conflict/evaluation/comparison views |
| 17 | Inspectable sources | PASS — source links, exact hashes, field catalog, browser inspection |
| 18 | Synthetic provenance disclosed | PASS — per-source flags plus response/screen labels |
| 19 | Audit persisted | PASS — immutable metadata/evidence and separate human note tests |
| 20 | Automated tests pass | PASS — backend 205, frontend 54, typecheck/build, isolated install |
| 21 | M1–M4 regression preserved | PASS — full suites, 6 frozen replays, 17 original table hashes unchanged |
| 22 | Documentation matches implementation | PASS — required eight documents, environment example and this report updated; historical/proposed contracts identified |

## 14. Remaining blockers

No blocker remains for this local M5 scope. Optional live-provider verification remains unrun and would require separately authorized credentials and an explicit bounded provider budget. Production municipal use is outside this milestone and requires the security, privacy, provenance and domain-review work above. M6 remains unimplemented.

The user's existing API process was not restarted or its database migrated during verification. Restart that API after installing the pinned requirements to activate M5 routes and the additive startup migration. No reset or reseed of the existing database is required.

## 15. Exact M6 next steps (not started)

1. Re-read the M6 roadmap gate and inspect status; preserve M5 changes and freeze the reviewed fixture manifest.
2. Add repeatable end-to-end coverage for the complete map → road → estimate → conflict → three-scenario comparison → evidence → human-review journey, including empty/unknown and provider-failure paths.
3. Verify fresh documented backend/frontend setup and a no-key/no-network-data run using isolated data; keep any reset helper restricted to explicitly disposable demo databases.
4. Reconcile every displayed demo amount, unit, date and source against frozen snapshots; re-run integrity/FK checks and saved-result replay.
5. Measure local performance on documented hardware; inspect keyboard, focus, non-color and responsive flows; fix demonstrated integration/accessibility issues without changing domain semantics.
6. Rehearse DEMO_PLAN, write presentation notes and disclose synthetic data, unavailable checks, tested safeguards and residual limits.
7. Run the complete regression/build/typecheck/secret checks and publish the actual M6 acceptance evidence. Do not deploy or claim production readiness. Commit/push still require explicit permission.
