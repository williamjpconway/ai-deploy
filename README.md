# Software Factory: Process

The point of this repo is the **process**. The product is just something to practise on.

## Structure: two levels

```
BRIEF.md                 LEVEL 1  the core idea. One per product, rarely changes
  │
ROADMAP.md               bridge   ordered list of features, one line each
  │
specs/NNN-name/          LEVEL 2  one folder per feature, created as soon as it's real scope
    status.md                     stage, gates, reconcile stamp, work log
    spec.md                       what and why (inherits the context from the brief)
    plan.md                       how: written with you, approved before code
    tasks.md                      small steps, each tied to an acceptance criterion
    review.md                     Test results and your accept/reject decision
```

Supporting files:

```
Instructions.md          the kickoff prompt for starting a new project
LIFECYCLE.md             how a feature moves Plan -> Develop -> Test -> Accept (source of truth)
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
3. **"Let's plan NNN"**: interactive - the spec is challenged until Ready, then plan and tasks are written with you, until you approve the plan.
4. **"Build NNN"**: autonomous - Develop and Test loop until every AC test passes, static checks run and an independent review is clean.
5. **"Review NNN"**: you see the evidence and accept or reject. Reject sends it back to Develop or Plan, logged in `retro.md`.
6. **Retro**: log mistakes in `retro.md` and route each fix (below). Then pick the next roadmap item.

Stages, gates and bookkeeping: `LIFECYCLE.md`. "Work on NNN" always picks up wherever the feature's `status.md` says it is.

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
