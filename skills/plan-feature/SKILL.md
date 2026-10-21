# Skill: Plan Feature

**When to use:** The operator says "let's plan NNN" (or "work on NNN"
while NNN is in Plan). Also after a G4 reject sends NNN back to Plan.

**Mode:** Interactive. Ask one question at a time and keep going until
G3 is approved or the operator stops. Read `LIFECYCLE.md` first - it
defines the gates, reconciliation and bookkeeping this skill uses.

This skill never writes code, tests or scripts. It produces a Ready
`spec.md`, an approved `plan.md` and `tasks.md`, and nothing else.

## Steps

1. **Load.** Read `specs/NNN-*/status.md`, `spec.md`, `plan.md`,
   `tasks.md`, `BRIEF.md`, `AGENTS.md`, and the spec of anything this
   feature depends on. If G1 is empty, fill it. Tell the operator in
   2-3 lines where the feature stands (from **Next** and the last log
   line) and what this session will cover.
2. **Reconcile** what exists (`LIFECYCLE.md`). Anything that fails
   becomes a question in step 3.
3. **Challenge the spec**, one question at a time, in this order:
   a. Open questions in section 8.
   b. Ready checklist items not ticked.
   c. Weaknesses you find yourself:
      - an AC that can't be turned into a test as written;
      - a MUST with no unhappy-path AC;
      - a requirement that conflicts with `BRIEF.md` or `AGENTS.md`,
        including open risks or gaps recorded there that block it;
      - a dependency on something not yet built or decided.
   For each one: state the problem in 1-2 sentences, propose an answer,
   and wait. Write the confirmed answer into `spec.md` straight away.
   Never advance on a guess, and never invent detail the operator
   didn't give. A deferral is fine when the operator says so - record
   it as "deferred to plan.md" with what will decide it.
4. **G2 - Spec Ready.** When nothing is open and the Ready checklist
   passes, summarise what changed in the spec this session and ask the
   operator to confirm it's Ready. On yes: spec **Status** Ready, fill
   G2, commit `NNN: spec ready`.
5. **Write the plan with the operator**, one section at a time:
   Approach, Changes, Test setup, AC coverage, Risks. Draft each from
   the spec and the repo, show it, and ask only about real decisions -
   things the repo and spec can't answer (a library with real
   trade-offs, where a test target comes from). Write each agreed
   section into `plan.md` as you go.
   Test setup must say how every AC's target state is produced -
   including broken states (e.g. a target whose SSH shell is cmd.exe) -
   and how it's reset afterwards. It must respect `AGENTS.md`'s
   confirmation rules: if a test needs a confirmed write, say how.
6. **Write `tasks.md`.** T1 is always "write a test for every AC and
   confirm each fails". Then small implementation tasks, each naming the
   ACs it covers, ordered so each one can be verified on its own. Show
   it and adjust.
7. **Reconcile** spec, plan and tasks fully. Fix anything that fails,
   or ask if the fix is a decision.
8. **G3 - Plan approved.** Present the plan in 5-10 lines, the AC
   coverage table, and the open risks. Ask: "Approve the plan and move
   NNN to Develop?"
   - Yes: fill G3, Stage -> Develop, commit `NNN: plan approved`, then
     continue straight into `skills/build-feature/` unless the operator
     says to stop there.
   - No: go back to whichever step the objection points to.
9. **Bookkeeping** (`LIFECYCLE.md`) at the end of the session, whether
   or not G3 was reached. If stopping early, the log line and **Next**
   must say exactly where to resume (e.g. "Plan: spec Ready, Approach
   and Changes agreed, Test setup not started").

## Verify

- No code, tests or scripts were written.
- Everything written into `spec.md` and `plan.md` came from the
  operator, or was proposed and explicitly confirmed - nothing invented.
- G2 was recorded before the plan was approved; G3 only on an explicit yes.
- Every AC in `spec.md` has a row in `plan.md`'s AC coverage table with
  a test, a target and a task.
- `status.md` (Stage, gates, **Last reconciled**, **Next**, a Work log
  line) and `ROADMAP.md` are updated and agree.
