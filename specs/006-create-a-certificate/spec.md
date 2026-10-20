# Spec 006: Create a Certificate

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 006

## 1. Problem
There's no repeatable, agent-driven way to issue a TLS certificate
from the lab CA for services that need one (GitLab, ArgoCD, etc.),
using a least-privilege credential that can only enroll against a
specific template, not manage the CA.

## 2. Goal
Running the playbook requests and issues a certificate from the
`lab-WebServer` template (the lab-validity copy of the built-in
`WebServer` template - see
`utils/prereqs/dc/duplicate-certificate-template.md`), chosen first
among the four playbooks' subjects because web/TLS certs are the
confirmed real use case (GitLab, ArgoCD), not `Administrator` or other
built-in templates used only for earlier debugging.

## 3. Non-goals
- Does not duplicate or manage certificate templates - that's the
  manual, one-time process in `duplicate-certificate-template.md`.
  This playbook only enrolls against an existing template.
- Does not manage the CA itself (OCSP, NDES, CEP/CES, CDP/AIA
  extensions, IIS config) - those remain explicitly out of scope per
  `AGENTS.md`'s CA install notes.
- Does not require manual CA approval of the request - this spec
  assumes the template is set to auto-issue (confirmed decision); if
  that changes, CA-level "Issue and Manage Certificates" rights would
  be needed and this spec would need revisiting.
- Does not export the issued certificate to non-Windows trust stores -
  that's separate, deferred infrastructure work noted in `AGENTS.md`.

## 4. User scenarios
- As the operator, I want to request a certificate for a new web
  service without manually using the Certificate Authority console or
  `certsrv` web enrollment.
- As the operator, if a certificate for the same subject already
  exists and is still valid, I want that handled cleanly, not a
  duplicate issuance.

## 5. Requirements
- **R1** The system MUST request and receive an issued certificate
  from the `lab-WebServer` template for a specified subject name.
- **R2** The system MUST use a credential whose AD CS rights are
  limited to Enroll on `lab-WebServer` (per `AGENTS.md`'s permissions
  table) - not a Domain Admin or CA-admin credential, once the
  least-privilege delegation is actually in place.
- **R3** Requesting a certificate for a subject that already has a
  valid, unexpired certificate from this template MUST be a no-op,
  not a duplicate issuance (idempotency).
- **R4** Issuance MUST require explicit confirmation, per `AGENTS.md`'s
  standing AD-write confirmation rule.

## 6. Acceptance criteria
- **AC1** (R1) Given no certificate exists for "test.domain.internal",
  when the playbook runs, then a certificate for that subject is
  issued from `lab-WebServer` and retrievable.
- **AC2** (R3) Given that certificate already exists and is valid,
  when the playbook runs again, then no new certificate is issued.

## 7. Constraints
- Requires `lab-WebServer` to actually exist (manual step, not yet
  done as of this spec being written) and the Enroll-only delegation
  from `AGENTS.md`'s permissions table to be in place.

## 8. Open questions
- [ ] Exact enrollment mechanism (`certreq` locally on the DC via SSH,
      or a WinRM-free equivalent) - deferred to plan.md.
- [x] Where the issued certificate/private key end up: a local Vault
      install (2026-10-20 decision - see `AGENTS.md`'s Infrastructure
      access note). Vault itself isn't set up yet - exact integration
      (API call from the playbook? manual push?) deferred to plan.md.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [ ] Open questions resolved or deferred - certificate/key destination is a real gap, not just an implementation detail; worth resolving before plan.md.
