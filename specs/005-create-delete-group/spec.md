# Spec 005: Create/Delete Group

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 005

## 1. Problem
There's no repeatable, agent-driven way to create or delete an AD
security group, or manage its membership, using a least-privilege
credential scoped to a specific OU rather than Domain Admin.

## 2. Goal
Running the playbook against the onboarded DC creates or deletes a
specified AD group, and can add/remove members, in the designated OU.

## 3. Non-goals
- Does not create the users being added as members (roadmap item 004,
  separate playbook) - this playbook only manages the group and its
  membership list, not the members' own existence.
- Does not manage groups outside the delegated OU scope (`AGENTS.md`'s
  least-privilege table).

## 4. User scenarios
- As the operator, I want to create an AD security group for a new
  purpose without manually opening Active Directory Users and
  Computers.
- As the operator, I want to add or remove a member from an existing
  group.
- As the operator, I want to delete a group I no longer need.
- As the operator, if the group already exists (create) or doesn't
  exist (delete), or a member is already present/absent, I want that
  handled cleanly, not an error.

## 5. Requirements
- **R1** The system MUST create an AD security group with at least a
  name, in the delegated OU.
- **R2** The system MUST delete a specified AD group.
- **R3** The system MUST add a specified user to a specified group's
  membership.
- **R4** The system MUST remove a specified user from a specified
  group's membership.
- **R5** Creating a group that already exists, or adding/removing a
  member already in the target state, MUST be a no-op, not an error.
- **R6** Any AD write MUST require explicit confirmation, per
  `AGENTS.md`'s standing rule for this credential.

## 6. Acceptance criteria
- **AC1** (R1) Given no group "test-group" exists, when the create
  playbook runs, then the group exists in the delegated OU.
- **AC2** (R3) Given the group from AC1 and an existing user, when the
  add-member playbook runs, then that user is a member.
- **AC3** (R5) Given that membership already exists, when the
  add-member playbook runs again, then nothing changes and no error
  occurs.
- **AC4** (R4) Given the membership from AC2, when the remove-member
  playbook runs, then the user is no longer a member.
- **AC5** (R2) Given the group from AC1 exists, when the delete
  playbook runs, then the group no longer exists.

## 7. Constraints
- Requires the OU-scoped delegation (Create/Delete Group objects +
  Modify group membership) from `AGENTS.md`'s permissions table to
  actually be in place - not yet implemented as of this spec being
  written.

## 8. Open questions
- [ ] None beyond what's already deferred to plan.md (exact Ansible
      module/approach).

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
