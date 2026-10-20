# Skill: New Feature

**When to use:** Proactively, whenever a conversation converges on a
concrete, real piece of scope that isn't already covered by an
existing roadmap item — not only when explicitly asked. Confirm with
the user that it should become a tracked feature before creating
anything (a quick check, not a full re-discussion) - don't spawn a
folder for every passing "it'd be nice if" comment.

This is a second standing exception to the normal skill rule (earn it
after 2-3 repeats) alongside `brief-intake/` — it's how every feature
enters the roadmap, not a mistake-recovery procedure.

## Steps

1. Pick the next roadmap number (NNN) and a short kebab-case name.
2. Create `specs/NNN-name/` from `templates/feature/`
   (`spec.md`, `plan.md`, `tasks.md`).
3. Fill `spec.md` from what's actually been discussed - same
   discipline as `brief-intake`: draw only from real conversation
   content, and flag anything thin or undiscussed as an explicit open
   question rather than inventing detail to make the spec look more
   complete than the discussion actually was.
4. Add a row to `ROADMAP.md`: `| NNN | <name> | Plan | [specs/NNN-name](specs/NNN-name/spec.md) |`.
5. Tell the user what was created and which open questions (if any)
   still need resolving before this can leave the Plan stage.

## Feature lifecycle

Every roadmap item is in exactly one of 4 stages - `ROADMAP.md`'s
Status column. A reject decision at Test sends the feature back to an
earlier stage; it is never a 5th stage of its own.

- **Plan** — `spec.md` written and Ready, `plan.md` written and
  approved by the user. Nothing is implemented yet.
- **Develop** — `tasks.md` being executed, one task at a time, per
  `AGENTS.md`'s existing Workflow rule.
- **Test** — implementation complete. Every acceptance criterion in
  `spec.md` runs as an actual automated test, per the template's own
  instruction that each AC "should turn directly into a test." Per
  `AGENTS.md`'s write/test/approve rule, built-without-error is never
  treated as working.
- **Accept** — the user reviews the Test results and makes an explicit
  accept or reject call; this is a human decision, not an automatic
  pass/fail. Accept means the feature is done and stays at this
  status. Reject sends it back to **Develop** (the implementation was
  wrong) or **Plan** (the spec itself was wrong) - whichever the test
  failure actually points to - with the reason logged in `retro.md`.

## Verify

- Every row in `ROADMAP.md` has a Status that's one of
  Plan/Develop/Test/Accept - no other value.
- A feature never sits in Test without every AC having a corresponding
  automated test that was actually run, not just written.
- A reject is always logged in `retro.md` with which stage it bounced
  back to and why - a silent reject (no record of what failed) is a
  bug in the process, not just the feature.
