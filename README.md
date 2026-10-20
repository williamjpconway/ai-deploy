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

1. **Brief**: write once (`templates/BRIEF.md`). Revisit only if the direction changes.
2. **Roadmap**: list features in order. 001 = the thinnest end-to-end slice.
3. **Spec**: copy `templates/feature/` to `specs/NNN-name/` for the top roadmap item.
4. **Plan**: the agent proposes how. You approve before any code is written.
5. **Tasks → Implement**: one task at a time, with tests after each.
6. **Retro**: log mistakes in `retro.md` and route each fix (below). Then pick the next roadmap item.

## Where a fix goes

| Symptom | Fix goes in |
|---|---|
| Same mistake across different features | `AGENTS.md` (rule) |
| Agent built the wrong thing / misread intent | the spec (it was ambiguous) |
| Features pulling in different directions | the brief (principles or non-goals are missing) |
| Agent fumbled a multi-step procedure | `skills/` (after 2-3 repeats) |
| Mistake got through without anything catching it | a test / check |

Each fix goes in **one** place. When in doubt, choose the more automated one.

## Example
The current BRIEF, ROADMAP and `specs/001-add-item/` are a filled-in example
(a toy todo CLI) so you can see the structure working. Replace them with your real product.
