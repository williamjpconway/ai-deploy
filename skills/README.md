# Skills

Each skill is a folder `skills/<name>/SKILL.md` containing: when to use
it, the steps, and how to verify the result.

Skills here are a project convention, not auto-loaded - `AGENTS.md`'s
Workflow section maps what the operator says to which skill to read.

## Standing skills (written up front, not earned)

| Skill | Operator says | Does |
|---|---|---|
| `brief-intake/` | "new project" | Builds `BRIEF.md`, proposes the first features |
| `new-feature/` | "new feature: ..." / scope converges | Creates the feature folder and roadmap row |
| `plan-feature/` | "let's plan NNN" | Interactive: spec to Ready, plan and tasks to approval (G1-G3) |
| `build-feature/` | "build NNN" | Autonomous: Develop and Test until clean |
| `accept-feature/` | "review NNN" | Presents the evidence, records the decision (G4) |

The last three are the feature lifecycle - see `LIFECYCLE.md` for the
stages and gates they move a feature through.

## Earned skills

Add a skill once you've done the same multi-step procedure by hand 2-3
times and the agent keeps tripping on it (see `retro.md`).
