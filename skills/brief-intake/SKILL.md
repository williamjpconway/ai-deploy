# Skill: Brief Intake

**When to use:** Starting a new product, or redoing `BRIEF.md` after the
direction changed. Triggered by asking to "build the brief" or "spec out
the product" before any ROADMAP.md rows exist.

This is a bootstrap exception to the normal skill rule (earn it after 2-3
repeats) — it's the entry point to every product this factory builds, not
a mistake-recovery procedure, so it's written up front instead of earned.

## Steps

1. Ask one `templates/BRIEF.md` section at a time, in order: one-liner,
   shape, infrastructure, problem, users, principles, non-goals, success.
   Never dump the whole template as a form to fill in.
2. For each section, propose a draft answer based on what's already been
   said, and let the user confirm or correct it before moving to the next
   section. Don't advance on a guess.
3. Write each confirmed answer into `BRIEF.md` live, `Status: Draft`, so
   the user sees it accumulate rather than getting one wall of text at
   the end.
3a. If Infrastructure names a real resource (not "none needed"), also
   fill in its block under `AGENTS.md`'s "Infrastructure access" section:
   the credential env var names, the access scope (e.g. a dedicated
   pool/namespace), and the confirm-before-destructive rule. Never ask
   for or write the actual secret value — only where it's stored.
4. Once every section is filled, propose exactly 3 candidate first
   features for `ROADMAP.md`. For each, state the reasoning in one line:
   thinnest end-to-end slice, hard dependency, or highest-risk unknown.
   Don't just list feature names with no justification.
5. Let the user pick, reorder, or edit the 3 candidates, then write the
   chosen order into `ROADMAP.md` as `Status: Planned` (no spec folder
   yet — that's created later, per the main loop).
6. Flip `BRIEF.md` to `Status: Agreed` only once the user confirms it
   matches their intent.

## Verify

- `BRIEF.md` fits in under one page and contains no requirements or
  acceptance criteria (those belong in a feature spec, never the brief).
- Shape names a concrete runtime target (CLI tool, container, VM image,
  web service, library, ...), not a vague restatement of the one-liner.
- Infrastructure names real, currently-accessible resources (a specific
  server, hypervisor, cloud account), not infra that would be nice to
  have. If Shape implies infra the user doesn't have, flag the mismatch
  before moving on.
- Every principle would actually change a feature decision if invoked —
  reject generic platitudes ("be user-friendly").
- Non-goals include at least one thing someone might reasonably assume
  is in scope.
- The #1 `ROADMAP.md` item is justified as the thinnest end-to-end
  slice, not just the most interesting feature to build.
