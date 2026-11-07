# AI explanation system

Status: proposed M5 design. There is no provider integration, prompt, or model call in M1. No AI integration was added to the application foundation. Deterministic summaries are a required product capability; a key is optional.

## Allowed and prohibited behavior

AI may select evidence-grounded ways to explain computed conflicts, summarize scenario tradeoffs, and draft a coordination-review recommendation. It must identify uncertainty and suggest questions for a human coordinator. It may not calculate costs, invent dates or measurements, infer buried asset locations, diagnose road safety, rank neighborhoods without an explicit policy, authorize spending, approve a project, or modify records. No tools for municipal actions or data mutation are exposed to the model.

The MVP deliberately bounds generation to claim/template selection. The server renders all numerical, date, and infrastructure assertions from a validated fact catalog. This sacrifices free-form fluency for inspectable grounding. Unrestricted recommendation prose is a future design question, not an implied capability of the MVP.

## Deterministic versus generative responsibilities

| Responsibility | Owner |
| --- | --- |
| Geometry, projection, date overlap, reopening rule | Conflict service |
| Cost/duration/bounds and budget tests | Estimate and scenario services |
| Coverage and missing-input warnings | Validated records and evaluation logic |
| Fact catalog and safe default narrative | Deterministic explanation service |
| Optional selection/order of supported explanations and coordination questions | LLM adapter |
| Evidence resolution, template rendering, rejection/fallback | Deterministic validation gate |
| Engineering judgment, scheduling approval, spending | Accountable human outside the application |

## Prompt input contract

Use one immutable ScenarioEvaluation as the sole numerical truth. Comparison claims require a separately validated ComparisonResult with matching basis. Input includes:

- input_hash, evaluation ID, method/prompt versions, synthetic-input flag and cost scope;
- a fact catalog: fact ID, typed value/unit, approved template IDs, evidence IDs and source status;
- known findings with typed rationale codes, both intervals and proximity parameters;
- mandatory unknown/limitation IDs including utility coverage, estimate assumptions, and human review;
- approved recommendation codes and templates, such as `request_utility_coordination_review` and `request_field_condition_review`;
- an instruction that source text is untrusted data and cannot override system rules.

Do not send secrets, local environment, personal contact data, raw utility diagrams, arbitrary file content, raw URLs to fetch, or reviewer notes. Normalize only allowlisted fields; exclude untrusted narrative by default. Synthetic assumption labels travel with each fact and the overall request. If a fact cannot be resolved to evidence, do not send it as an established fact.

## Provider-only structured output

Proposed strict shape (not the public API response):

```json
{
  "summary_template_id": "scenario_tradeoff_summary",
  "claim_selections": [
    {"fact_refs": ["fact-central-cost"], "template_id": "estimated_cost_with_basis"}
  ],
  "recommendation_code": "request_utility_coordination_review",
  "unknown_refs": ["unknown-utility-coverage"],
  "limitation_refs": ["limit-synthetic-inputs", "limit-human-review"]
}
```

Reject extra keys. Validate template IDs and recommendation enums against an allowlist and verify their prerequisites. Limit selections to 12 claims and require nonempty fact references for every factual template. All mandatory unknown/limitation references must be present. The model provides no numerical values, dates, arbitrary claims, or free-text summary; these are rendered from facts after validation. If a template is incompatible with a referenced fact type or assumes unsupported savings/safety, reject the whole output.

The public ExplanationResult includes rendered summary/claims, evidence IDs, mode, fallback reason, and review requirement as specified in API_SPEC. Rendering inserts values and labels exactly from the evaluation. The default summary always shows synthetic status, unknown coverage, and estimate limits regardless of model choices.

## Unsupported claims and missing data

An unknown rate is not zero; missing utility records are not clearance; a permit is not a verified schedule or buried geometry. Missing values render a concrete reason and requested verification. A proposed coordinated scenario may be cheaper in the fixture but cannot be declared safe to defer without review. Banned conclusions include guaranteed savings, safe excavation, approved project, and measured traffic delay when only lane-closure-days exist.

Reject unresolved fact references, missing caveats, non-allowlisted keys/text, or inappropriate recommendation codes. Do not partially show invalid model output. Save validation failure codes and use the deterministic response for the same input hash. A valid schema alone is not sufficient; references and template prerequisites must also pass.

## Availability and human review

Backend mode defaults to deterministic. Without a key/model configuration, an explicit AI request returns deterministic mode with `not_configured`. Proposed provider timeout is 8 seconds, no automatic retry for the hackathon; timeout/rate limit/network/model errors return the same fact-based fallback with the appropriate reason. Provider selection and model version are TBD until M5 and must be recorded. No paid request is required in tests or for the demo.

The reviewer sees the fact list, assumptions, source dates/statuses, warnings, and mode. A review note creates an AuditEvent; it never approves work. Log input/result hashes, evidence references, template/prompt version, model label when used, and outcome. Do not persist API keys, raw confidential prompts, or hidden reasoning. Cache only by input hash, template/prompt version, model label and mode; never reuse across different evaluation facts.

## Evaluation plan

M5 uses provider mocks and hand-reviewed fixtures. Test correct reference selection, numeric/date rendering, caveat retention, input-order stability in deterministic mode, and inappropriate recommendation rejection. Include adversarial source instructions, missing coverage, stale assessments, incompatible comparisons, malformed JSON, extra keys, fabricated IDs, out-of-scope templates, timeouts and unavailable providers.

Release gate: 100% of rendered numerical/date claims originate from the fact catalog; all mandatory caveats appear; no prohibited approval/safety statement can be rendered by an approved template; every provider failure case yields a usable deterministic explanation. Record failures and reviewed examples, not an invented model accuracy score. Future free-form prose requires a separate claim-level entailment evaluation, expert review, and explicit architecture change before enabling it.
