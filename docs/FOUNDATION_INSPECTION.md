# Foundation inspection and decision log

Review date: 2026-11-07. This is a repository baseline and M0 decision record, not an application release report.

## Existing repository before edits

- Root: `/Users/bpeinado/Desktop/CivicPlAIn/CivicPlAIn`.
- Branch: main, clean tracked/untracked status, tracking origin/main at `a6cdbd9`.
- Remote fetch/push: `https://github.com/BricenPeinado/CivicPlAIn`.
- Tracked content: 36-byte README with project name and BUHACKS 2026 label; CivicPlAIn.iml; .idea/.gitignore, misc.xml, modules.xml and vcs.xml.
- Ignored local content: .idea/workspace.xml; inspected as IDE state, preserved and not copied into documentation.
- No source code, tests, package/dependency manifests, env template, root ignore file, application frameworks, database or migrations existed. IDE project metadata is not evidence of an application framework.
- No existing application functionality or uncommitted source work needed migration. README is expanded; IDE files are preserved byte-for-byte. No preexisting tracked files are removed.

Inspection used file inventory including hidden paths, Git status/branches/remotes/log, all tracked text files, local IDE-state inspection, and a SHA-256 snapshot of existing non-Git files for final preservation checks. Git internals and credentials were not dumped. No remote fetch was needed or performed.

## Discrepancies and adaptation

The requested stack and features did not exist. Therefore the planned React/Vite/FastAPI modular monolith can be adopted without conflicting configuration or duplicating applications. The initial scaffold adds only documentation, directory keepers, and empty Python package markers. Dependency manifests, runnable entry points, migrations, source adapters and fixtures are intentionally deferred to their milestones.

The requested feature branch is `chore/project-foundation`, created from the clean main baseline. No commit or push is part of this task. The generic branch-prefix default is superseded by the user's explicit branch name.

## Decisions for the MVP

| Decision | Reason / downstream contract |
| --- | --- |
| Modular monolith with one web client and one API process | Solo-team delivery; domain calculations stay testable without model/network access |
| At most 30 segments in one Lower Manhattan window | Bounded demonstrator; DATA_SOURCES fixes bounds and selection limitations |
| Local fixtures before live integration | Reliable demo and honest source verification; observed fields only after validated import |
| EPSG:4326 exchange, EPSG:32618 metre calculations | Avoid degree-based distance/area math in the NYC window |
| Half-open local civil-date work intervals | Adjacent schedules do not overlap; calendar-day arithmetic is explicit |
| Manual scenario enumeration, roadwork-only cost scope | Makes comparisons inspectable; no unsupported global optimum or automatic loss estimate |
| Optional AI with bounded template/fact selection | Provides grounded explanations and an identical no-key factual path |
| Nulls plus explicit reasons and separate utility coverage | Prevents absence of data from appearing to be clearance |

## Unresolved questions and recommendations

| TBD | Recommendation / milestone that must resolve it |
| --- | --- |
| Runtime versions, dependency manager and test tooling | M1: select supported local Python/Node versions, one manager per language and committed locks; document actual commands |
| Basemap style, tile provider, attribution and offline rights | M1: plain local style + GeoJSON fallback first; review terms before depending on or packaging tiles |
| Actual public dataset payloads, releases, schema/terms and join keys | M1–M2: validate a small extract and source manifest; synthetic fallback remains sufficient for demo |
| Actual segment count and official geometry mapping | M1–M2: reproducible bounded selection; do not force a count with mislabeled observations |
| Persistence driver/ORM and schema evolution mechanism | M2: favor standard sqlite3 with a small repository layer unless typed ORM benefits justify the dependency; migrations only when persistence exists |
| Condition freshness and treatment suitability | M2: display age and require human review; do not invent a safety threshold or treatment rule |
| Spatial tolerance and reopening horizon calibration | M3: 5 m / 30 days are demo screening assumptions; verify against source quality and label limitations |
| Unit rates, uncertainty, durations and lifespan basis | M2–M4: use explicit synthetic assumptions in DEMO_PLAN until qualified sources are reviewed; never promise real cost accuracy |
| Provider/model and whether optional AI adds enough demo value | M5: deterministic path first; choose a model only for an authorized integration task, record version/cost limits, never require a key |
| Free-form generated prose | Defer; template selection is MVP recommendation. Any expansion needs claim-level evaluation and an architecture review |
| Hackathon presentation length and required submission format | M6: confirm actual rules and adapt rehearsal/presentation artifacts |

Production identity/authorization, multi-tenancy, live utility integrations, and municipal engineering approvals are future release gates, not unresolved prerequisites for this local demo.

## Exact next implementation milestone

M1: choose and lock runtime/dependency versions, initialize the single web/API applications, implement only the health route and selectable bounded map with a small labeled geometry fixture/manifest, add local configuration and plain-style fallback, and verify/document local setup and smoke checks. Do not implement estimates, conflicts, persistence business logic, scenario evaluation, or provider integration during M1.

## M0 validation record

Validation completed on 2026-11-07:

- `git status --short --branch`, `git branch -avv`, `git remote -v`, `git ls-files`, `git status --ignored --short`, and `git log -3 --oneline` established the baseline. `git switch -c chore/project-foundation` created the requested branch; Git metadata required sandbox escalation. No commit or push command was run.
- `git diff --check` passed. `git diff --cached --name-only` was empty; HEAD remained `a6cdbd9`. All new files remain untracked and README remains an unstaged modification for user review.
- One-off Python standard-library checks verified local Markdown links, all 12 required entity sections, required scaffold paths and document coverage, empty Python package markers, valid illustrative request JSON, and whitespace in newly authored Markdown. Passed.
- SHA-256 comparison against the pre-edit non-Git snapshot verified all six existing non-README files, including ignored workspace.xml, remained byte-for-byte unchanged. README was the only deliberately modified original file. There was no existing application source to overwrite.
- Decimal/date checks independently reconciled DEMO_PLAN totals, sensitivity ranges, and elapsed-day examples. Passed. This validates illustrative arithmetic, not municipal accuracy or an implemented calculation engine.
- `git check-ignore -q` assertions passed for 12 secret/environment/cache/build/database/download paths and five retained template/demo/keeper paths.
- A heuristic credential-pattern scan of newly authored/updated content found no matches; every .env.example value is empty. No files were staged or committed. This is not a comprehensive historical secret audit.
- The final scaffold tree and full new/modified file list were displayed during validation. No dependencies were installed, database migrations generated, application logic implemented, or deployment performed.

No application test suite exists, so none was run. Documentation checks do not establish runtime correctness of the proposed system. All M1–M6 behavior and endpoints remain unimplemented.
