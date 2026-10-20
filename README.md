# Software Factory: Process

The point of this repo is the **process**. The product is just something to practise on.

## Structure: two levels

```
BRIEF.md                 LEVEL 1  the core idea. One per product, rarely changes
  │
ROADMAP.md               bridge   ordered list of features, one line each
  │
specs/NNN-name/          LEVEL 2  one folder per feature, created when you're ready to build it
    spec.md                       what and why (inherits the context from the brief)
    plan.md                       how: agent-written, reviewed by you before code
    tasks.md                      small steps, each tied to an acceptance criterion
```

Supporting files:

```
Instructions.md          the kickoff prompt for starting a new project
AGENTS.md                always-on technical rules for the agent (source of truth)
CLAUDE.md                thin pointer (`@AGENTS.md`) so Claude Code auto-loads it
retro.md                 log of mistakes and where each fix went
skills/                  repeatable procedures, added once earned
templates/               blank BRIEF, ROADMAP and feature/ templates
```

**Which level?** If it applies to every feature, it goes in the brief
(or in AGENTS.md if it's a technical rule). If it can be tested on its own,
it's a requirement in a feature spec.

## The loop

1. **Brief**: write once (`templates/BRIEF.md`, or run `skills/brief-intake/`). Revisit only if the direction changes.
2. **Roadmap**: list features in order. 001 = the thinnest end-to-end slice. New features get added here — and get their spec folder — via `skills/new-feature/`, proactively, as they come up in conversation.
3. **Plan stage**: `spec.md` (what/why) then `plan.md` (how — the agent proposes, you approve before any code is written).
4. **Develop stage**: work `tasks.md` one task at a time, per `AGENTS.md`'s Workflow rule.
5. **Test stage**: every acceptance criterion in `spec.md` runs as an actual automated test — built-without-error is never treated as working.
6. **Accept stage**: you review the test results and make an explicit accept/reject call. Reject sends it back to Develop or Plan, logged in `retro.md`.
7. **Retro**: log mistakes in `retro.md` and route each fix (below). Then pick the next roadmap item.

Every roadmap item's Status is always exactly one of **Plan / Develop / Test / Accept** — see `skills/new-feature/SKILL.md` for the full lifecycle rules.

## Where a fix goes

| Symptom | Fix goes in |
|---|---|
| Same mistake across different features | `AGENTS.md` (rule) |
| Agent built the wrong thing / misread intent | the spec (it was ambiguous) |
| Features pulling in different directions | the brief (principles or non-goals are missing) |
| Agent fumbled a multi-step procedure | `skills/` (after 2-3 repeats) |
| Mistake got through without anything catching it | a test / check |

Each fix goes in **one** place. When in doubt, choose the more automated one.

## Current product
`BRIEF.md`, `ROADMAP.md` and `specs/` are no longer the toy example —
they were replaced with the real product (`ai-deploy`) once the
process itself was validated. If you're forking this repo as a
template for a different product, that's what to replace next.
