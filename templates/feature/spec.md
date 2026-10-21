# Spec NNN: <Feature name>

**Status:** Draft | Ready   <!-- spec readiness only - feature progress lives in status.md -->
**Date:** YYYY-MM-DD
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** NNN

<!--
LEVEL 2: one per roadmap item. Inherits the why, users and principles from BRIEF.md.
Don't repeat them here. Add only what's specific to this feature.

A spec says WHAT and WHY, never HOW. If you're naming files, libraries or
functions, that belongs in plan.md. Aim for 1 page. If it's longer, split the feature.
-->

## 1. Problem
<!-- 1-3 sentences. The gap THIS feature fills. The bigger why is already in the brief. -->

## 2. Goal
<!-- ONE sentence: what is true once this is done. -->

## 3. Non-goals
<!-- What this feature deliberately does NOT do (product-level non-goals are already in the brief). Agents expand scope,
     and this section is what stops them. Be specific. -->
-

## 4. User scenarios
<!-- Short stories from the user's point of view. Include at least one unhappy path. -->
- As a <user>, I want to <action> so that <outcome>.

## 5. Requirements
<!-- Numbered so tasks and tests can refer to them. MUST = required, SHOULD = nice to have.
     Each one is a single, testable statement. -->
- **R1** The system MUST ...
- **R2** The system MUST ...
- **R3** The system SHOULD ...

## 6. Acceptance criteria
<!-- The definition of done. Given/When/Then, each linked to a requirement.
     Each of these should turn directly into a test. -->
- **AC1** (R1) Given ..., when ..., then ...
- **AC2** (R2) Given ..., when ..., then ...

## 7. Constraints
<!-- Limits on the solution: performance, security, compatibility,
     things it must or mustn't depend on. Leave empty if there are none. -->
-

## 8. Open questions
<!-- Anything unresolved. The spec isn't Ready until this is empty
     or every item is explicitly deferred. -->
- [ ]

---
### Ready checklist
- [ ] Problem and goal make sense to someone without context
- [ ] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [ ] Every MUST has at least one acceptance criterion
- [ ] Non-goals list at least one thing someone might reasonably assume is in scope
- [ ] No implementation detail (that goes in plan.md)
- [ ] Doesn't contradict the brief's principles or non-goals
- [ ] Open questions resolved or deferred
