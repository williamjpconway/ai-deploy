# Skill: Accept Feature

**When to use:** The operator says "review NNN" (or "work on NNN" while
NNN is in Test and waiting on G4).

**Mode:** Presents the evidence and records the operator's decision.
Never makes the decision. Read `LIFECYCLE.md` first.

## Preconditions

- The latest Test run in `review.md` is clean: every test passing,
  static checks run, no open blocking findings. If not, stop - this
  feature belongs in `skills/build-feature/`.

## Steps

1. **Reconcile** (`LIFECYCLE.md`).
2. **Present**, short and in this order:
   - what was built: the spec's Goal plus 3-5 lines;
   - every AC with its test result;
   - the static check summary;
   - the review findings, advisory ones included;
   - anything deferred or known to be limited.
   Then give the operator a way to see it working for themselves - a
   command to run, a page to open. Acceptance is the operator checking
   it works, not re-reading the agent's claims.
3. **Ask:** "Accept NNN, or reject? If reject: is the implementation
   wrong (-> Develop) or the spec (-> Plan)?"
4. **Accept:** append a G4 row "Accepted"; write
   `Accepted YYYY-MM-DD (masterchief)` under `review.md`'s Decision;
   Stage -> Accept; **Next** "done". Commit `NNN: accepted`.
5. **Reject:** append a G4 row "Rejected -> Develop|Plan: <reason in
   the operator's words>"; write the same under `review.md`'s Decision;
   add a row to `retro.md`; Stage -> Develop or Plan; **Next** names the
   skill to run. Commit `NNN: rejected -> Develop|Plan`.
6. **Bookkeeping** (`LIFECYCLE.md`).

## Verify

- The decision was the operator's explicit words - the agent never wrote
  Accepted without an explicit accept.
- `status.md`, `review.md` and `ROADMAP.md` agree; a reject also has a
  `retro.md` row.
