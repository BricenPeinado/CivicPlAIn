# AI explanation system

Status: M5 implemented; M6 integration and responsible-AI regression verified locally. This is a bounded evidence advisor, not an engineering decision system. See [M5 implementation and verification](M5_IMPLEMENTATION.md). M1–M4 calculations, snapshots and fixture prices are unchanged. Useful deterministic explanations require neither a key nor network access.


## M7 official-data boundary (7.1 inspection implemented)

M7.1 ingestion does not alter this implemented provider/evidence contract. M7 official records use the separate six-classification municipal read contract in DATA_MODEL, not synthetic-only Road/Evidence inputs. No v2 AI endpoint is included: official map/project views display deterministic source values, lineage and missingness directly. Existing synthetic explanations/reviews remain available in their own context. Never change an official record's classification to call v1 AI, copy permit narrative/contacts/geometry into provider context, or treat a published administrative record as an observation.

A future real-data advisor requires a versioned evidence projection/classification/citation and review contract with source-revision hashes, field lineage, unknown/assumption propagation and replay validation. Preserve fact-reference-only selection, deterministic server rendering, no-key fallback, source-failure closed behavior and no mutation tools. It must not fabricate prices, schedules, utility locations or predictions. That extension is outside M7's official inspection scope and cannot be enabled by a frontend label change. See [M7 plan](M7_IMPLEMENTATION_PLAN.md).


## M8 planned official evidence extension (unimplemented)

M8.0 only audits/documents. Official AI remains unavailable in the runtime; [M8 plan](M8_IMPLEMENTATION_PLAN.md) gates a separate `municipal-ai-evidence-v1` projection in M8.7 after deterministic official results exist. No provider/key setup or live calls are needed. Keep all current synthetic contracts/audits/replays unchanged.

The new projection must carry the six DATA_MODEL classifications, base snapshot/intelligence release, accepted association/decision, policy/catalog/assumption/calculation versions and full source/input/result hashes. Validate frozen inputs and replay before building allowlisted facts. Raw source text, contacts, geometry, reviewer notes and user questions never become provider context. Model cannot assign matches/categories/recency/weights/prices/schedules or alter source facts. Only exact fact/template reference selection is allowed; deterministic server rendering inserts all mandatory unknown/coverage/assumption/review warnings independently of selection. No tools or autonomous actions.

Use useful deterministic official explanations without a key/network; provider refusal, timeout/429/bad citations/unsupported output fall back with reason, while source-integrity/replay failures fail closed. Preserve bounded projection/truncation disclosure, audit failure semantics and separate explicit human notes. New official interaction/note storage must reference official artifacts, not synthetic-only review FKs. No explanation or note approves work, safe deferral or spending; no GET/navigation creates an interaction. Tests and source privacy gates are A7 in the plan.

## Architecture and allowed tasks

The existing FastAPI monolith owns: reference validation → EvidenceBuilder → context integrity validation → optional LLMProvider → structured selection/citation validation → deterministic rendering or fallback → append-only audit. The React advisor receives only the public REST response. No model gets SQL, Python, mutation tools, web research, arbitrary files, raw utility geometry or database access.

Tasks are estimate explanation, saved conflict explanation, comparison of 2–3 saved evaluations, and bounded contextual questions about a road, assessment, estimate, conflict, project, evaluation or comparison. The server retrieves all authoritative records. Client amounts, evidence objects, unknown modes and extra fields are rejected. The API remains the existing local-only unauthenticated prototype; there is no new identity/role system.

## Evidence projection and revisions

`services/ai/evidence.py` projects typed allowlisted fields, not arbitrary source text. Every evidence record includes an evidence ID, entity/record ID, canonical complete-record hash, input hash/calculation version when applicable, dataset ID when present, source-content revision hashes, data kind and synthetic flag. Facts retain a field path, value, unit, classification and evidence ID. Source hashes identify the exact frozen contents, not merely a mutable source ID.

Estimates use their own frozen road, assessment, option, request and evidence; hashes and pure M2 replay must match. Conflicts replay the stored complete M3 analysis and verify both hashes and finding contents. Evaluations verify hashes and pure M4 replay from frozen inputs. Comparisons delegate basis compatibility to the unchanged M4 comparison service, including source, horizon, price, parameter and method checks. No live join replaces historical prices. A replay incompatible with the current calculation runtime fails with 409 rather than silently using new results.

Road/assessment/project contexts read current validated records and capture their content hashes. Repeated reads after source changes can produce a new evidence identity. Each request's immutable reduced projection is persisted for audit. Synthetic and observed are separate flags; current demonstration records are synthetic, while generic observed-source ingestion remains unsupported by the existing road/evidence contracts.

At most 96 facts are retained, using a stable prefix and a 48,000-byte canonical JSON budget before the snapshot-hash field. Omitted facts set `truncated=true` and `omitted_fact_count`; missing-data warnings are collected before truncation. Oversized mandatory metadata returns 422 and requests a smaller context. Full source records remain available through the existing estimate/analysis/evaluation views. Hashes are identity/integrity checks, not signatures or tamper-proof provenance.

## Provider and public contracts

`ProviderSelection` is a strict Pydantic schema: evidence_snapshot_hash, summary_template_id=`bounded_summary`, 1–12 claim selections `{fact_id,evidence_id,template_id:fact_value}`, all four limitation codes, and one context-compatible review code. No prose, values, units, dates, claims of approval or tool arguments are permitted. Extra keys, wrong hashes, duplicate/out-of-context references, unsupported templates, missing caveats and inappropriate review codes reject the entire selection.

The model selects emphasis. The server renders every factual sentence from the fact catalog, retains the remaining facts, and independently inserts mandatory uncertainty/review text. It never accepts an LLM monetary assertion simply because it cites a real source. Numerical/date/unit substitutions are unrepresentable in valid provider output; attempts fail schema validation. Unsupported narrative is rejected, not labeled as verified. Conditional interpretations and human-review language use predefined application templates.

`Explanation` is the separate public response: explanation/task IDs, evidence hash, summary, key_findings with fact/evidence references and classifications, tradeoffs, uncertainties, missing_information, suggested_review_actions, citations, complete bounded evidence projection, provider/validation status, fallback reason, model label, UTC timestamp, source classification, mandatory review flag, warnings and audit reference. Classifications distinguish record facts, deterministic calculations, conditional interpretation and required human review. A synthetic record fact is a fact about that record, not a municipal observation.

## Contextual questions and injection controls

Raw questions (1–500 nonblank characters) are handled locally by conservative intent routing. Only the resolved intent and bounded evidence package reach the model. Unknown topics, future delay/condition predictions, approvals, secrets, warning suppression and instruction-override requests return `insufficient_evidence`; they do not trigger a model call. Matching a topic produces the attached catalog and review considerations, not an unrestricted answer. The matcher is intentionally limited and may decline legitimate paraphrases or display broader evidence than the question needs.

Road notes, project descriptions, source descriptions, scenario names/assumption prose and reviewer notes are excluded from model context and explanation text. System instructions identify context as untrusted. IDs and typed fields are data; selection cannot alter values or warnings. These tested controls reduce the source-text injection surface. They are not universal injection detection, entailment verification or a guarantee of complete/accurate inputs. Future free-form generation requires a separate reviewed design and evaluation.

## Configuration and availability

Default: `CIVICPLAIN_AI_PROVIDER=deterministic`; all requests default to `mode=deterministic`. To opt in on the server, select `openai`, set server-side `OPENAI_API_KEY`, and optionally `OPENAI_MODEL`. Environment variables are exported by the launching shell; no automatic dotenv loader exists. Never use frontend `VITE_*` credentials. Obtaining or changing a key is a separate task; no key or paid smoke call was used for M5 verification.

Official Python SDK **openai 2.54.0** uses `AsyncOpenAI.responses.parse` with a Pydantic format, `store=false`, no tools and the fixed official HTTPS API base URL. Default model: **gpt-5.4-mini-2026-03-17**, verified against the [official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini). See [official Structured Outputs guidance](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). The default model is configurable; account access/latency is not verified by documentation or the status endpoint.

Calls have an 8-second wall-clock deadline and SDK timeout, zero automatic retries, 1,200 maximum output tokens, two concurrent calls maximum, and a default 20-call/hour per-process ceiling (`CIVICPLAIN_AI_MAX_CALLS_PER_HOUR`, 0–100). Failed attempts count toward the ceiling. The request/input bounds and call ceiling constrain usage, not exact dollars; restarting the process resets counters. Set provider-side project budgets for a financial ceiling. The SDK may spend processing time within a call before cancellation; no billing cancellation guarantee is claimed.

No key, disabled provider, timeout, 429, network/model failure, refusal/incomplete response, invalid output/citation/context, missing caveats, exhausted usage or busy provider returns explicit deterministic fallback with a sanitized reason. No partial failed output is displayed. A source-integrity failure returns an error instead of explaining unvalidated records. An audit write failure returns storage 503; an answer is not reported as successfully audited when persistence failed.

## Privacy, audit and human accountability

M5 stores deduplicated reduced evidence projections (`ai_evidence`), interaction metadata (`ai_interactions`) and explicit human notes (`review_events`). Interaction metadata includes task/context/source references, evidence hash, configured model/provider when attempted, output mode, validation result/error category, timestamp, request correlation ID, contract version and output hash. No raw question, prompt, response prose, secret, hidden reasoning, contact data or geometry is stored in AI interactions. A human voluntarily submitted note/alias stays in the separate local review table, never the model context. Do not put sensitive information in a review note.

Additive migration 5 preserves existing payloads. Foreign keys and update/delete rejection triggers protect append-only records within the application. Local administrators can alter the database; there is no production retention policy, authentication, tenant isolation or cryptographic audit guarantee. No explanation, model selection or review note authorizes construction, spending or safe deferral. Actual decisions require qualified humans and municipal processes outside CivicPlAIn.


## M6 validation and demo evidence

The full regression suite retains all M5 selection, citation, unsupported money/date/unit/prose, provider failure, timeout, rate-limit, audit and no-mutation cases. M6 additionally tests malicious scenario names/descriptions through save → evaluation → evidence projection → mocked provider and malicious user questions. Raw narrative never reaches provider input or rendered verified claims; unsupported questions return insufficient evidence without another call. Existing road-note/project-description injection tests remain passing.

Actual browser checks used API-backed estimate, conflict and comparison explanations, source disclosure/focus, optional-AI not-configured fallback, and unavailable-local-API timeout/retry recovery. No paid/live OpenAI request was made. Deterministic mode and no-key fallback require only local services; no OS-wide network settings were changed during testing. The 1 MiB transport cap complements the smaller 48,000-byte/96-fact AI projection limit. See FINAL_QA_REPORT for measured local API timings and limits; these tests do not establish perfect hallucination prevention or truthful source inputs.

### M8.1 deterministic inspection boundary

M8.1 adds no provider call, prompt, tool, official AI evidence package or audit mutation. Road condition summaries are pure typed read projections over immutable source/association context, explicit date and labeled recency assumptions. Source decimal values and timestamps remain exact; unsupported classifications and ambiguous links/pass/scope remain unknown. Existing v1 deterministic explanation/provider fallback behavior is unchanged. New official AI support remains a later gated stage.


### M8.1 owner-approved pilot checkpoint

The [M8.1 pilot policy](M8_1_PILOT_IMPLEMENTATION.md) is a pure deterministic server calculation, outside AI. Project-owner association approvals are hash-bound local annotations, never model-generated links or municipal endorsements. Pilot-derived observation grades, accepted reference scope and unavailable road-wide condition remain distinct. No official data is added to provider context or official advisor enabled by this checkpoint; existing deterministic/no-key synthetic explanations and mutation restrictions remain unchanged.


## M8.3 deterministic estimate path

Official-road estimates run without any model/provider or network calculation. Entered source citations remain unverified planning metadata; they are not sent to a provider or fetched. This milestone does not enable the official-data AI advisor or allow an explanation to create/modify numeric inputs, approve treatments or save calculations. Server-derived results retain their independent typed input/result snapshots.


## M8.4 ranking is outside AI

`maintenance-priority-v1` has no provider call, model-generated weight/factor/score, network lookup or AI mutation path. Human policy rationale is metadata, never executable instructions. Results/explanations are deterministic server facts/templates; official AI advice remains unavailable. No OpenAI API key is required. Missing traffic/risk/schedule evidence cannot be supplied by prose.

## M8.5 deterministic official screening

`official-screen-v1` computes evidence-qualified construction screening entirely without AI. There is no official explanation-provider endpoint or AI mutation tool. Work/permit provenance, assumptions, unknowns and review status remain structured and replayable; no generated prose can populate missing geometry, schedule, grade, utility depth or numerical findings. Schedule alternatives never imply optimized outcomes, savings, safe excavation or municipal approval. Existing synthetic advisor behavior remains unchanged.

## M8.6 official saved-result explanations

Explicit v2 decision-support explanation requests replay one selected estimate, priority run or screening before constructing `official-scalar-projection-v1` using existing `ai-evidence-v1`. Context types reuse estimate/evaluation/conflict; task `explain_official`. Static labels and validated result scalars only; no work titles, permit narrative, geometry, review notes, citations' free text, policy rationale or raw user question is sent. Missing values remain explicit null facts. Output is `derived`, never a new observation or independently approved plan.

Existing provider chooses fact/evidence IDs/templates only; server validates exact evidence hash, citations, all caveat codes and required review action, then renders all material facts from deterministic values. No numerical generation, tools, approvals, arbitrary-source instruction authority or missing-input substitution. No-key mode works locally; optional AI with no key returns `fallback/not_configured`. Invalid/provider-failure output falls back with reason; audit failure fails closed. Full source references and provenance are available from the frozen result, separate from model context. See [M8.6 report](M8_6_IMPLEMENTATION.md). Historical statements that *all* official explanation is unavailable are superseded only for these replay-verified saved contracts; arbitrary official records/general scenarios remain unsupported.
