# Final hackathon presentation outline

A concise eight-part pitch. Use the three-minute product sequence in [HACKATHON_DEMO](HACKATHON_DEMO.md); adapt total talk length to actual event rules, which were not verified here.

1. **Problem — uncoordinated infrastructure work.** Road and utility teams can plan related work in separate systems. A planner needs to ask about sequencing before committing a pavement plan.
2. **Consequences — explain the mechanism.** Reopening newly repaired pavement can require additional restoration and disruption. The demo flags this potential mechanism; it does not prove an actual municipal loss, frequency or dollar saving.
3. **Solution — CivicPlAIn.** One evidence-linked planning workspace combines road condition, transparent repair alternatives, spatial/date conflict screening and hypothetical scenario comparison. The differentiator is the reproducible connection from source inputs through alternatives and review, beyond displaying dots on a map.
4. **Live product.** Select synthetic R-001; inspect condition and the $53,400 resurfacing example; reveal the two-day potential rework gap; compare before/after/coordinated plans under a $60,000 synthetic budget; show identical costs, differing dates/findings and high-case over-budget status. Ask for an explanation and inspect its saved source references. Demonstrate offline fallback.
5. **Technical architecture.** React/TypeScript/Vite and local MapLibre → REST → one modular FastAPI application → SQLite. Pydantic boundaries; Decimal costing; Shapely/pyproj projected spatial screens; immutable evaluation snapshots and versioned replay. A small bounded problem does not need microservices or an optimization platform.
6. **Responsible AI.** Deterministic code owns quantities, costs, dates, budgets and conflicts. Optional server-side AI selects allowlisted evidence/template references; server rendering and strict validation own every claim. Missing utilities, synthetic provenance, uncertainty and human review remain mandatory. Invalid output/provider failure uses deterministic fallback. No arbitrary mutation tools, construction approval or spending authority exists. Tested safeguards do not imply perfect hallucination prevention.
7. **Potential municipal value.** Help reviewers discover coordination questions earlier, compare explicit alternatives and communicate assumptions across teams. Quantitative value needs validated real inputs and a prospective evaluation; do not claim proven savings, city adoption, market size or safety certification.
8. **Future company growth — clearly future.** With permission and domain validation, connect municipal asset/assessment systems, permit feeds and utility-owner planned work; develop provenance-aware ingestion, interoperable exports and cross-team review. Commercial work would require identity/roles/tenancy, security/privacy/retention, reliable deployment and accountable municipal/engineering processes. Citywide allocation and forecasting require new evidence and validation.

## Questions to be prepared for

- **Why AI?** It provides a bounded evidence-navigation/explanation layer; the useful product continues operating without it. It is not a substitute for deterministic engineering calculations.
- **Why are the costs equal?** The three scenarios use the same 800 m² resurfacing scope and catalog. Schedule changes alone do not establish a discount. Potential avoided rework is unpriced.
- **Why is resurfacing shown for a poor road?** It demonstrates the sequencing question using the same scope across alternatives. The UI retains the not-indicated suitability warning and reconstruction candidate; qualified staff choose treatment.
- **What was verified?** 212 backend tests, 57 frontend tests, typecheck/build, isolated dependency installation, SQLite/replay/idempotence, actual dev/production browser workflow and timeout recovery. See [FINAL_QA_REPORT](FINAL_QA_REPORT.md) for exact boundaries and results.
- **What is not ready?** Real municipal data, complete utility coverage, engineering certification, production authorization and public deployment. See [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md).

Never describe a hypothetical coordination opportunity as guaranteed savings or a safe-work recommendation.
