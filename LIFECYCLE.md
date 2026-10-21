# Feature Lifecycle

The single source of truth for how a roadmap item moves from idea to
done. `README.md`, `AGENTS.md` and the skills point here - none of them
restate it.

## Stages

Every feature is in exactly one stage. It's recorded as **Stage** in
the feature's `status.md` (the source of truth) and mirrored in
`ROADMAP.md`'s Status column.

| Stage | What's happening | Leaves when |
|---|---|---|
| Plan | Spec challenged until Ready; `plan.md` and `tasks.md` written with the operator | G3: operator approves the plan -> Develop |
| Develop | `tasks.md` worked one task at a time; T1 writes the AC tests and confirms they fail | All tasks done, all AC tests pass -> Test (automatic) |
| Test | Full suite, static checks, independent review. When clean, waits here for G4 | Failing test or blocking finding -> Develop (automatic). G4 accept -> Accept. G4 reject -> Develop or Plan |
| Accept | Accepted by the operator. Done. | - |

Going back is a move to an earlier stage, never an extra stage.

## Gates (the operator's touchpoints)

Every gate is the operator's decision. The agent records it in
`status.md` - it never makes it.

| Gate | Touchpoint | Passed when |
|---|---|---|
| G1 | Start | The operator first says "let's plan NNN" |
| G2 | Spec Ready | The operator confirms nothing is open and the spec's Ready checklist passes |
| G3 | Plan approved | The operator explicitly approves `plan.md` + `tasks.md`. Stage -> Develop |
| G4 | Accept / reject | The operator explicitly accepts or rejects after reviewing the Test evidence |

Gate rows are never edited or deleted. When a gate is passed again
(G3 after a reject to Plan, G4 after any reject), a new row is appended.

The agent also stops and asks outside the gates when:
- the spec is ambiguous or turns out to be wrong (ask, don't guess), or
- an action needs confirmation under `AGENTS.md` (AD writes, anything
  destructive).

## Who triggers what

| Operator says | Skill | Mode | Runs until |
|---|---|---|---|
| "new feature: ..." (or scope converges in conversation) | `skills/new-feature/` | Creates the folder | Feature exists in Plan |
| "let's plan NNN" | `skills/plan-feature/` | Interactive Q&A | G3 approved (or the operator stops) |
| "build NNN" (or straight after G3) | `skills/build-feature/` | Autonomous | Test clean, or a stop condition |
| "review NNN" | `skills/accept-feature/` | Presents evidence | G4 recorded |

"Work on NNN" means: read `specs/NNN-*/status.md` and run the skill for
its current stage.

## Feature files

```
specs/NNN-name/
  status.md   stage, gates, reconcile stamp, next step, work log - progress lives here only
  spec.md     what and why
  plan.md     how, including how every AC gets tested and against what
  tasks.md    ordered steps, T1 = the AC tests
  review.md   created at Test: results of every Test run + the G4 decision
```

## Reconciliation

"Reconciled" means every one of these was checked and holds:
1. Every MUST requirement in `spec.md` has at least one AC.
2. Every AC is in `plan.md`'s AC coverage table, with a test and a target.
3. Every AC is covered by at least one task in `tasks.md`.
4. Nothing in `plan.md` or `tasks.md` contradicts `spec.md`, and nothing
   in any of the three contradicts `BRIEF.md` or `AGENTS.md`.
5. Every R/AC id mentioned in `plan.md` or `tasks.md` exists in `spec.md`.

Before `plan.md`/`tasks.md` have real content, only checks 1 and 4 (for
`spec.md`) apply.

When they all hold, set **Last reconciled** to today. When they don't,
fix the drift - or ask, if the fix is a decision - before stamping. A
stamp older than the last change to `spec.md`, `plan.md` or `tasks.md`
is stale.

Reconcile at the start of every skill run, after any edit to those three
files, and before every gate.

## Bookkeeping

At every gate and at the end of every skill run, in this order:
1. **Stage** in `status.md`, if it changed - and mirror it in `ROADMAP.md`.
2. The gate row, if a gate was passed (date, result).
3. Reconcile and restamp **Last reconciled**.
4. **Next**: one line - what happens next, and who it's waiting on.
5. Append one **Work log** line:
   `- YYYY-MM-DD - <what was done> - <what was decided, if anything>`
   One line per session, not per action. Newest last. Never edit old lines.
6. Commit: `NNN: <the log line text>`. At gates: `NNN: spec ready`,
   `NNN: plan approved`, `NNN: accepted`, `NNN: rejected -> Develop|Plan`.

Dates are ISO (`YYYY-MM-DD`) everywhere.

## Done

A feature is done when all three agree:
- `status.md`: Stage Accept, latest G4 row Accepted.
- `review.md`: Decision Accepted.
- `ROADMAP.md`: Accept.
