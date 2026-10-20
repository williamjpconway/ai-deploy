# Instructions: Starting a New Project

To bootstrap a new product with this factory, open a fresh session in this
repo and say:

```
New project. Run skills/brief-intake/SKILL.md to build the brief, then suggest 3 starting features.
```

This runs the `brief-intake` skill: it asks through `BRIEF.md`'s sections
one at a time (one-liner, shape, infrastructure, problem, users,
principles, non-goals, success), writes each confirmed answer in as you
go, then proposes 3 candidate first `ROADMAP.md` items with reasoning
(thinnest slice / dependency / risk) for you to pick from.

Naming the skill path explicitly matters: `skills/` here is a project
convention, not a Claude Code auto-loaded skill, so without the path the
agent may freelance a brief from scratch instead of following the
intake procedure.
