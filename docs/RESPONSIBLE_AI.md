# Responsible AI and municipal-use limits

Status: requirements for all implementation milestones, not a claim of completed controls or validated safety.

## Human accountability

CivicPlAIn is decision-support software because it presents alternatives and evidence for human interpretation. It has no authority, tools, or API endpoints to approve construction or spending. A planner, utility coordinator, and qualified engineering/budget reviewers must validate schedules, quantities, site conditions, and permissible actions using their established procedures. A local review note is not a signed municipal approval or verified identity.

The most tempting demo conclusion—delay resurfacing until utility work finishes—can be unsafe if pavement needs immediate intervention. The interface must surface condition evidence and unresolved safety questions alongside any cost advantage. It cannot optimize away an urgent repair or describe deferral as safe without accountable external review.

## Reliability, transparency, and explainability

- Every material observation/assumption has source evidence, dates when known, coverage limitations, and a synthetic-input label when applicable.
- Costs are itemized assumptions, not bids; bounds are sensitivity ranges unless supported by a real statistical model. Show inclusions/exclusions, currency, price basis, and method version.
- Distinguish a rule-triggered potential conflict from a verified engineering collision. Reveal spatial tolerance, CRS, schedule intervals, horizon, and both project references.
- A detected finding can coexist with incomplete coverage. Zero detected findings must display “No conflicts detected in the checked records; utility coverage may be incomplete” or equivalent qualified text.
- Present deterministic facts and generated explanation mode separately. Users can inspect the evidence without reading AI prose.

## Uncertainty and missing information

Use null plus an explicit unknown reason, not zero, guessed coordinates, or plausible-looking schedules. Unknown required estimate inputs block that estimate; incomplete evaluation totals are indeterminate. Coverage status is independent of finding count. Preserve source-specific condition scales and observation ages; do not convert an old condition rating into a current safety assessment.

Only documented source/assumption bounds support estimate ranges. Never interpret synthetic ranges as calibrated uncertainty, precision, or municipal cost accuracy. Show unknown utility depth/location even when a nearby work permit is available.

## Bias and geographic coverage

The Lower Manhattan study window is a bounded demonstration, not a representative city sample. Public datasets may overrepresent inspected streets, reported issues, certain work types, or well-documented agencies. Missing records can systematically hide needs. Do not rank neighborhoods by apparent absence of defects, wealth proxies, or reporting activity.

MVP comparison is among manually defined options for the selected roads, with no citywide allocation claim. Future prioritization needs documented policy weights, coverage audits by geography, sensitivity analysis, stakeholder input, and assessment of who experiences disruption. Include pedestrian/accessibility and emergency-access concerns as review questions; lane-closure-days alone does not represent their impact.

## Hallucination prevention and failure modes

Domain math never calls a model. The M5 adapter selects allowed templates and evidence references only; the server renders numbers/dates and enforces mandatory caveats. Unsupported references, instructions embedded in source data, malformed responses, or prohibited templates trigger deterministic fallback. Test these failures deliberately. Do not claim schema validation alone makes arbitrary prose truthful.

No-key, model outage, tile outage, missing source data, and incomplete estimates must be honest, usable demo states. A blank map or fallback summary must not quietly remove a warning or invent an input.

## Privacy, security, and auditability

Use public non-personal inputs and synthetic utility work for the demo. Exclude individual permittee contact details and sensitive subsurface maps from fixtures and model prompts. Keep provider keys backend-only and local env/database files ignored. Validate data and request limits; restrict CORS and bind the unauthenticated development server locally.

Audit imports, calculations, evaluations, explanations, and review notes using immutable input hashes and method/source versions. Append-only application records aid traceability but are not tamper-evident compliance infrastructure. Retention, authentication, encryption, tenant separation, backups, and incident response remain production requirements. Do not upload municipal confidential data or expose the local MVP publicly.

## Testing and evaluation gates

| Risk | Required evidence before demo completion |
| --- | --- |
| False numerical authority | Manually reconciled synthetic estimate and scenario totals; bounds and exclusions visible |
| Missed/false conflict | Threshold/date-boundary tests, missing geometry/schedule tests, qualified map findings |
| False clearance | Zero-finding and unknown-coverage UI/API tests |
| Unsafe deferral recommendation | Condition/safety review flag retained in coordinated scenario and explanation |
| Hallucinated AI facts | Fact-reference/template validation, injection and unsupported-output tests, deterministic fallback |
| Geographic/measurement overclaim | Study window, fixture labels, CRS and coverage disclosure visible |
| Credential/privacy leakage | Reviewed staged/tracked diff and secret patterns; redacted logs and prompts |
| Inaccessible warnings | Keyboard/list access and text/icon indicators in addition to color |

M6 records actual results and limitations. Automated checks cannot establish engineering safety, complete utility coverage, unbiased citywide allocation, or regulatory compliance. Real municipal adoption requires field and utility verification, qualified professional review, source/license agreements, security review, and the municipality's formal authorization processes outside CivicPlAIn.

## Implemented M2 controls

No LLM/provider integration or key is used. Deterministic condition-screening rationale accompanies every comparison; all alternatives require engineering review, including cheap options. A score only screens a demonstration treatment; it cannot certify pavement structure, safe deferral or excavation. Missing/undated assessment and unknown/non-asphalt surface return requires_review. Synthetic condition dates are not inspections.

The UI labels synthetic costs on every option and estimate; shows assumptions, exclusions, source IDs, sensitivity basis, dimension provenance, currency rounding and active/setup/curing duration. Unknown dimensions remain null and block saved estimates unless the user explicitly supplies a positive metric planning assumption with a note. Those assumptions remain labeled in the immutable snapshot. Stored inputs/results preserve source contents, hashes and method version, independent of later catalog changes. Costs, schedules and suitability are not engineering certification, municipal observations, statistical confidence, approval or authorization. Utility coverage remains unknown throughout.

## Implemented M3 conflict controls

Conflict calculations and explanations are deterministic templates without an LLM, network dependency or provider key. The engine separates supplied project facts/provenance, computed spatial/date evidence, potential consequences and unverified assumptions. No safety score, excavation clearance, construction approval, financial loss or savings is computed. All priorities say coordination_review and all findings request accountable human verification.

Project location_status explicitly distinguishes source_reported, approximate and unknown; null geometry/dates carry reasons. Approximate polygon overlap is labeled potential, while positive area overlap remains inspectable as a computed fact. Even confirmed_geometric_overlap refers only to supplied polygons, never observed underground interference. Shared roads, centerline crossings, buffered corridor membership and proximity can all be false positives because actual excavation footprints/depth/grade/scope are unknown. Schedules from permits/demo assumptions are not actual construction commitments. Completed work requires actual dates for chronological screening.

The UI labels the seven fictional demo projects, their category/status, approximate or unknown location, incomplete schedules, source data, relevant dates/roads, method/tolerances and required review. A dashed project outline, thick selected outline, textual category labels, warning symbols and selected text accompany color. Keyboard project/road lists remain usable without a map. Hiding layers does not remove findings or incomplete checks. Positive findings can coexist with missing-data warnings. Qualified zero-result wording and unknown utility coverage remain visible for unrelated projects and empty data.

Saved analyses freeze complete inputs, source contents, parameters and library versions; input/result hashes and stable finding IDs support reproducibility. Same input returns the first saved result/time; changed inputs produce distinct history. Append-only SQLite triggers are application controls, not tamper-proof audit infrastructure. General review-note/AuditEvent workflows, observed ingestion, coverage verification and M5 provider controls remain unimplemented.

The only demonstrated project/utility records are fictional. No private utility maps, permits, precise observed underground locations, personal contacts or external municipal data were imported. Broad shared-road/corridor screens require review of actual work scope, traffic/access and accessibility implications. A potential rework finding cannot establish that delaying a needed repair is safe. M3 itself did not add scenario planning or generative AI; M4 controls are recorded below.

## M3.5 proposed-action and hypothetical-screening controls

M4 implements these controls as detailed below; unpriced catalog extensions and general observed adapters remain unsupported. Proposed actions must expose scope, quantity derivation, exact input sources, synthetic status and unknowns. Whole-road dimensions cannot silently price a partial patch/trench; a supplied area assumption is not a survey. Current prices and rate-only sensitivity remain authoritative. Unsupported patch/restoration methods and unsourced lifespans stay unavailable; partial known subtotals never become complete affordable scenarios.

Preliminary active/setup/curing days do not imply calendar dates, confirmed schedules or closure duration. Supplied calendars and closure intervals remain explicit assumptions. Shared mobilization requires priced, sourced replacement lines, never an automatic saving or reduced setup allowance. Budget affordability is a numerical result when cost is complete; safety/deferral review remains independently required even when within budget.

Hypothetical conflict results retain a separate context label and original source provenance. A synthetic flag alone cannot distinguish a proposal from an existing fictional fixture. Existing-project screenings are also derived findings, not observations of actual collisions. Explicit exclusions/replacements affect only the evaluation snapshot and remain visible with originals/reasons; they cannot erase project records, prove coverage or remove safety review. Missing schedules/geometry or unsupported reopening classification produce incomplete checks. A zero-result or not-run screen is never excavation clearance.

No model generates repair quantities, schedules, prices, lifespans, override decisions or mobilization savings. No source text or AI prose may mutate a project, and proposed findings must not enter the existing-project history. The current synthetic-only Road/Evidence schemas cannot be presented as an observed municipal ingestion capability. New observed adapters require reviewed provenance semantics and a separate versioned change.

## Implemented M4 planning controls

Plans are explicitly hypothetical and synthetic independently of finding context. Evaluations freeze sources, authorship assumptions, source-record field/value links, scopes, quantities, catalog versions, prices, schedules, overrides and all line/contingency calculations. Proposed actions and findings never mutate or masquerade as real project/history records. Unknown geometry, schedules, closures, methods and quantities remain explicit incomplete checks. No positive utility coverage or safe-deferral conclusion exists, including when all supplied inputs are complete or costs fit the budget.

Budget labels apply only to the declared roadwork actions and catalog exclusions. Potential rework is not automatically monetized or inserted as a repair action. An explicit unpriced restoration/patch action blocks complete totals and affordability; a known subtotal is labeled incomplete. Low/high cases are bundled-rate sensitivities rather than probability bounds. Every supported method retains the M2 suitability warning and exclusions; choosing a cheaper method is not engineering validation. No avoided rework, shared-mobilization saving, lifespan, traffic delay or economic disruption cost is invented.

Comparison may identify dominance only for its named numeric objectives under matching scope, assumptions, budgets and complete inputs/checks. It cannot select a universally best or safest plan, validate physical harm, approve projects or spending, or alter calendars. A coordinated label does not suppress concurrent-work or closure findings. The demo's after-utility option still carries a sequencing-review finding. Numerical feasibility and safety review remain independent.

M4 adds no model calls, provider keys, prompts or AI explanation endpoint. Deterministic computed tradeoff sentences only restate saved metrics. The optional model/claim-validation/audit-review work remains unimplemented M5 scope.

## Implemented M5 safeguards and limits

The responsible-AI advisor is implemented in the current monolith. It is not certified for engineering decision-making. The optional model selects only source-backed fact/template IDs; strict Pydantic output validation, exact request-hash/citation membership and context-compatible review codes are enforced before rendering. All numbers, units and dates come from deterministic source projections; injected numerical/prose/approval fields reject the selection. The server independently preserves missing-data/synthetic/utility/review caveats and all projected facts. Invalid provider output is never partially displayed.

Immutable estimate/analysis/evaluation evidence is hash-checked and replayed from frozen inputs. Live prices do not replace historical rates. Missing references/integrity errors return sanitized errors; unknown dimensions, dates, rates, closures, lifespan and utility coverage remain explicit. Potential rework never becomes confirmed damage or monetary loss. Comparison uses existing M4 compatibility checks and does not create savings or a universal winner.

Tested controls include source-note/project-description injection attempts to override instructions, alter costs, suppress warnings, fabricate citations, reveal keys and approve spending; unsupported numbers/dates/units/free prose; missing/out-of-context citations/caveats; stale hashes; timeout, 429, unavailable/invalid/incomplete provider responses; no key; bounded usage; source preservation; and immutable audits. These are regression examples and deterministic structural controls, not a universal hallucination-prevention or prompt-injection guarantee. The model never receives raw questions, untrusted narrative, reviewer notes, secrets or geometry, and has no tools. Arbitrary future extensions could reintroduce risks and require review.

The local intent matcher deliberately declines delay predictions and unsupported questions. It can misunderstand legitimate phrasing; users must inspect attached evidence and source views. Fixed templates may omit nuance from free-form source notes, which remain in the original application views and are never endorsed as facts by AI. Synthetic facts describe fictional records only. The system cannot establish source completeness, measurement accuracy, fairness, physical feasibility, regulatory compliance or safe deferral.

Deterministic mode is the default and stays useful offline. Optional server-side OpenAI calls use timeouts, zero retries, bounded context/output, two concurrent calls and a per-process hourly ceiling. Billing/account access and live latency remain unverified; no paid call is required to test safeguards. Provider project budgets are necessary for a financial ceiling. Configuration status does not mean provider connectivity was tested.

Reduced evidence projections and metadata are append-only local records; raw questions/prompts/prose and sensitive geometry are not logged. Human-submitted notes/aliases remain separate from model output and never authorize work. Avoid sensitive information in notes. There is no production retention/access-control system or tamper-proof storage. Keep the unauthenticated API on loopback; production authentication, tenancy, backups, retention and professional review remain separate release gates.
