# Skill: New Feature

**When to use:** Proactively, whenever a conversation converges on a
concrete, real piece of scope that isn't already covered by an
existing roadmap item - not only when explicitly asked. Confirm with
the operator that it should become a tracked feature before creating
anything (a quick check, not a full re-discussion) - don't spawn a
folder for every passing "it'd be nice if" comment.

This is a standing exception to the normal skill rule (earn it after
2-3 repeats), alongside `brief-intake/` - it's how every feature enters
the roadmap, not a mistake-recovery procedure.

This skill only creates the feature. Everything after that - stages,
gates, bookkeeping - is in `LIFECYCLE.md`, and the next step is
`skills/plan-feature/`.

## Steps

1. Pick the next unused roadmap number (NNN) and a short kebab-case name.
2. Create `specs/NNN-name/` from `templates/feature/`: `status.md`,
   `spec.md`, `plan.md`, `tasks.md` (`review.md` is created later, at Test).
3. Fill `spec.md` from what's actually been discussed - same discipline
   as `brief-intake`: draw only from real conversation content, and flag
   anything thin or undiscussed as an explicit open question rather than
   inventing detail to make the spec look more complete than the
   discussion actually was.
4. Fill `status.md`: Stage Plan, **Last reconciled** never, **Next**
   "let's plan NNN - waiting on operator", Work log
   `- YYYY-MM-DD - Feature created - <one line of what it is>`.
5. Add a row to `ROADMAP.md` where it belongs in build order:
   `| NNN | <name> | Plan | [specs/NNN-name](specs/NNN-name/spec.md) |`.
6. Commit `NNN: feature created`.
7. Tell the operator what was created and which open questions still
   need resolving - those are where `plan-feature` will start.

## Verify

- The folder has `status.md`, `spec.md`, `plan.md` and `tasks.md`.
- `status.md` and `ROADMAP.md` both say Plan.
- Every open question in `spec.md` is one the conversation genuinely
  left open, not filler.
