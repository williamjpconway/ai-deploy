# Spec 003: Create/Delete a DNS Record

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 003

## 1. Problem
Once the Windows DC is onboarded (001), there's no repeatable,
agent-driven way to create or delete a DNS record on it - this is the
first of the AD/DNS/CA playbooks, chosen to go first because it's the
simplest of the four (no AD object permissions, no certificate
template complexity).

## 2. Goal
Running the playbook against the onboarded DC creates or deletes a
specified DNS record, using a least-privilege credential scoped to
exactly that.

## 3. Non-goals
- Does not manage DNS zones themselves (forwarders, reverse zones -
  that's `utils/prereqs/dc/Install-AiDeployDNS.ps1`, a one-time setup
  script, not a repeatable playbook).
- Does not manage the `DnsAdmins` group or grant broader DNS rights -
  the least-privilege delegation (ACL on the specific zone) is a
  prerequisite this spec assumes exists, not something it sets up.
- Does not modify or create other AD objects (users, groups,
  certificates - separate specs).

## 4. User scenarios
- As the operator, I want to create a DNS A record for a new service
  without manually opening DNS Manager.
- As the operator, I want to delete a DNS record I no longer need.
- As the operator, if the record already exists (create) or doesn't
  exist (delete), I want that handled cleanly, not an error.

## 5. Requirements
- **R1** The system MUST create a DNS record of a specified type (at
  minimum A records) given a zone, name, and value.
- **R2** The system MUST delete a specified DNS record.
- **R3** Creating a record that already exists with the same value
  MUST be a no-op, not an error (idempotency, per the brief).
- **R4** Deleting a record that doesn't exist MUST be a no-op, not an
  error.
- **R5** Any AD write (create or delete) MUST require explicit
  confirmation, per `AGENTS.md`'s standing rule for this credential.

## 6. Acceptance criteria
- **AC1** (R1) Given a zone with no record "test.domain.internal",
  when the create playbook runs with that name and an IP, then the
  record exists with that value.
- **AC2** (R3) Given that same record already exists with the same
  value, when the create playbook runs again, then nothing changes
  and no error occurs.
- **AC3** (R2) Given the record from AC1 exists, when the delete
  playbook runs, then the record no longer exists.
- **AC4** (R4) Given the record doesn't exist, when the delete
  playbook runs, then nothing changes and no error occurs.

## 7. Constraints
- Requires the DNS zone ACL delegation from the permissions table
  (`AGENTS.md`) to actually be in place - not yet implemented as of
  this spec being written.

## 8. Open questions
- [ ] Record types beyond A (CNAME, PTR, etc.) - deferred to plan.md;
      R1 only requires A records to start.
- [ ] Exact Ansible module (`win_dns_record`? raw PowerShell via the
      `DnsServer` module per `AGENTS.md`'s Tools rule?) - deferred to
      plan.md as an implementation detail.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
