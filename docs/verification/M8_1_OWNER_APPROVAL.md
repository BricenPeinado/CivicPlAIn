# M8.1 project-owner pilot authorization

Recorded from the project owner's explicit user instruction in this chat on 2026-11-08. This is local project authorization for the CivicPlAIn hackathon pilot, **not NYC DOT approval, engineering certification or independent identity verification**. No additional association is approved. The user-authored attached approval text has SHA-256 `4c11646622647b05cc660ec6e0e3be13c17f0dd22cee6e0e3c2fd6ddafe78720`; no personal attachment path is required for runtime replay.

| Approved source observation | Approved LION SegmentID:OBJECTID |
| --- | --- |
| `condition-8d7e97c9b05832b7f976715f` | `0031869:93678` |
| `condition-b3fbf48779766247f0094f6d` | `0024365:106478` |
| `condition-af6497ae3976ac464387b86a` | `0023459:95443` |
| `condition-d94ea30139a3eee0b3882d0d` | `0032097:97186` |
| `condition-189d3413f583f508da25efe8` | `0032478:102671` |

The owner stated that these five associations were manually reviewed and authorized acceptance for the pilot. The fifth observation's raw zero rating must remain Unknown. Hash-bound executable annotations are in [m8.1-owner-approved-associations.json](m8.1-owner-approved-associations.json). They bind only the archived base snapshot and full candidate evidence, retain every competitor, and cannot be transferred to another release without revalidation.

The authorization approves the road references; it supplies no new whole-road, grade, roadbed, direction, multipass-selection or release-compatibility evidence. An annotation therefore uses the existing conservative `partial` scope: approved road reference, without a certified complete-road assessment scope. This is an implementation restriction, not a claim that the owner measured a partial extent. No independent whole-road scope review is fabricated. The existing eligibility rules remain in force.

## Approved application classification policy

The owner approved **CivicPlAIn Pilot Pavement Classification Policy v1.0**, an application planning assumption, not official NYC DOT grading:

- Zero, null, missing, nonnumeric, nonfinite and scores outside 0–10 are Unknown. Any populated NonRatingReason makes the observation Unknown regardless of score.
- For 0 < score ≤ 10, round using Decimal half-up to a whole number. Rounded 0 is Unknown, 1–3 Poor, 4–7 Fair and 8–10 Good.
- Preserve the exact raw score and non-rating reason. No local-street exception, PCI threshold, averaging or generated AI fact.
- An observation grade does not establish a road-level condition. Require an accepted association and preserve existing scope, date, direction/roadbed, multipass, conflict and recency checks.
- Policy ID `civicplain-pilot-pavement-v1.0`; explicit read projection version `road-condition-v2-pilot`. Policy hash and all raw evidence/association hashes bind replay. The default no-policy v1 projection is preserved.

The owner authorizes publication to a verified isolated pilot copy, explicit release selection and application of this policy there. The original M7 database, historical snapshots and synthetic fixtures must remain unchanged. No production deployment, commit/push, automatic future match approval or M8.2 start is authorized by this decision.

See [the pilot implementation and acceptance report](../M8_1_PILOT_IMPLEMENTATION.md) for actual publication identifiers, results, test evidence and remaining blockers. This approval supersedes the prior pending-review status **only for these five pilot associations and this project-defined policy**. External NYC DOT policy/release applicability remains unresolved.
