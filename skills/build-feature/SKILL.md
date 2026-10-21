# Skill: Build Feature

**When to use:** Straight after G3 (plan-feature hands over), or the
operator says "build NNN" (or "work on NNN" while NNN is in Develop, or
in Test and not yet clean).

**Mode:** Autonomous. Runs Develop and Test, looping between them,
without asking - except at the stop conditions below. Read
`LIFECYCLE.md` first.

## Preconditions

- `status.md` has a G3 row with Approved. If not, stop: this feature
  belongs in `skills/plan-feature/`.
- Reconcile passes. If `spec.md`, `plan.md` or `tasks.md` changed since
  G3, stop and ask - a changed plan needs G3 again.

## Develop

1. On the first run, record the base commit in the Work log
   (`- YYYY-MM-DD - Develop started at <sha>`). The independent review
   diffs against it.
2. Work `tasks.md` in order, one task at a time (`AGENTS.md` Workflow).
3. **T1:** write a test for every AC, from `spec.md` - never from an
   implementation. Run them and confirm each fails for the expected
   reason, not because of a broken test. Tick T1.
4. **Each later task:** implement, run the tests for its ACs plus the
   whole suite, and tick it only when they pass.
5. All tasks ticked and every AC test passing -> Stage Test.

## Test

6. Append a new "Test run N" section to `review.md` (create it from
   `templates/feature/review.md` on the first run) and fill it:
   a. **Tests:** the full suite, every AC listed with its result.
   b. **Static checks:** every check listed under "Checks" in `AGENTS.md`.
   c. **Independent review:** start a fresh subagent and give it ONLY
      `spec.md`, the diff from the base commit to now, and the static
      check output - never `plan.md`, `tasks.md`, `status.md` or this
      conversation. Ask it to check the diff against every R and AC,
      and for problems scanners miss: authz gaps, injection, secrets
      handling, unsafe defaults, destructive or AD-write actions
      without confirmation. Record each finding as blocking or advisory.
7. **Not clean** (any failing test or open blocking finding): Stage ->
   Develop, add fix tasks to `tasks.md` (tagged `fix, run N`, naming
   the AC or finding), and continue at step 2. No operator call needed.
8. **Clean:** stay in Test, set **Next** to "waiting on G4 - review
   NNN", and tell the operator it's ready, pointing at `review.md`.

## Stop conditions (ask the operator, then carry on)

- The spec is ambiguous or turns out to be wrong. If the answer
  changes the spec or the plan, that's a move back to Plan - it needs
  G3 again.
- An action needs confirmation under `AGENTS.md`.
- The same test fails for the same reason after 3 fix attempts - report
  what was tried.
- Test run 3 is still not clean - stop and summarise. Something
  upstream is probably wrong.

## Bookkeeping

`LIFECYCLE.md` bookkeeping at every stage change and at the end of the
session. One Work log line per session, e.g.
`- 2026-10-23 - T1-T3 done - AC1-AC3 passing, AC4-AC5 still failing`.

## Verify

- T1's tests existed and failed before any implementation task was ticked.
- The reviewer was given only spec, diff and static check output.
- `review.md` has a section for every Test run, and nothing reached
  "waiting on G4" with a failing test or an open blocking finding.
- Built-without-error was never treated as passing (`AGENTS.md`).
