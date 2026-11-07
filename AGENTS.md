# CivicPlAIn development instructions

## Before changing the repository

- Read README.md and the documents relevant to the task. Start implementation from docs/MVP_ROADMAP.md; use docs/DATA_MODEL.md and docs/API_SPEC.md as shared contracts.
- Inspect Git status and preserve existing changes, IDE metadata, and working functionality. Adapt existing modules rather than creating a second application.
- Implement one milestone at a time. State the milestone and acceptance criteria before feature work. Update documentation when behavior or contracts change.
- Preserve the modular monolith, REST boundary, and separation of deterministic domain calculations from AI explanations. Explain major architectural deviations and their tradeoffs before making them.

## Engineering and data rules

- Do not fabricate infrastructure observations, utility locations, schedules, costs, or measurement accuracy. Label synthetic fixtures at record and screen level; retain provenance when deriving values.
- Treat missing utility information as unknown. A search with no finding never establishes that excavation is safe.
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
