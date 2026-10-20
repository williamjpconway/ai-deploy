# Spec 004: Create/Delete User

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 004

## 1. Problem
There's no repeatable, agent-driven way to create or delete an AD user
account on the onboarded DC, using a least-privilege credential scoped
to a specific OU rather than Domain Admin.

## 2. Goal
Running the playbook against the onboarded DC creates or deletes a
specified AD user in the designated OU.

## 3. Non-goals
- Does not manage group membership beyond what's needed to create the
  user (that's roadmap item 005).
- Does not manage users outside the delegated OU scope (`AGENTS.md`'s
  least-privilege table) - creating a user elsewhere is out of scope,
  not silently redirected.
- Does not set or manage passwords beyond initial creation specifics
  deferred to plan.md.

## 4. User scenarios
- As the operator, I want to create an AD user for a new service
  account without manually opening Active Directory Users and
  Computers.
- As the operator, I want to delete a user account I no longer need.
- As the operator, if the user already exists (create) or doesn't
  exist (delete), I want that handled cleanly, not an error.

## 5. Requirements
- **R1** The system MUST create an AD user with at least a username
  and display name, in the delegated OU.
- **R2** The system MUST delete a specified AD user.
- **R3** Creating a user that already exists MUST be a no-op, not an
  error (idempotency).
- **R4** Deleting a user that doesn't exist MUST be a no-op, not an
  error.
- **R5** Any AD write MUST require explicit confirmation, per
  `AGENTS.md`'s standing rule for this credential.

## 6. Acceptance criteria
- **AC1** (R1) Given no user "svc-test" exists, when the create
  playbook runs with that username, then the user exists in the
  delegated OU.
- **AC2** (R3) Given that user already exists, when the create
  playbook runs again, then nothing changes and no error occurs.
- **AC3** (R2) Given the user from AC1 exists, when the delete
  playbook runs, then the user no longer exists.
- **AC4** (R4) Given the user doesn't exist, when the delete playbook
  runs, then nothing changes and no error occurs.

## 7. Constraints
- Requires the OU-scoped delegation (Create/Delete User objects +
  Reset Password + Write all properties) from `AGENTS.md`'s
  permissions table to actually be in place - not yet implemented as
  of this spec being written.

## 8. Open questions
- [ ] Initial password handling - generated and returned, prompted
      interactively (matching the pattern in
      `dc/New-AiDeployPrereqs.ps1`), or deferred entirely to a
      separate reset step? Not yet decided; deferred to plan.md.
- [ ] Which user attributes beyond username/display name are required
      at creation - deferred to plan.md.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
