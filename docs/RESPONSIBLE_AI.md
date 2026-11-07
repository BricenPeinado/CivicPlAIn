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
