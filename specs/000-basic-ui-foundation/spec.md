# Spec 000: Basic UI Foundation

**Status:** Draft
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 000

## 1. Problem
This is the first UI requirement anywhere in the product (needed by
spec 001's new Validate/Onboard buttons, and later specs 002 and 008).
There's no web UI, no authentication, and no app-data storage yet -
building that scaffolding as a side effect of 001 would conflate a
foundational decision with a single feature's needs.

## 2. Goal
An operator can log into a web UI on `ai-deploy` using their existing
Ubuntu local account credentials, and the backend is wired to Postgres
(app state) and Vault (secrets) - ready for 001, 002, and 008 to add
their own pages/actions on top.

## 3. Non-goals
- Does not implement any feature-specific page or action itself
  (onboarding triggers, the connected-VMs list, the terminal) - those
  are specs 001/002/008.
- Does not implement multi-user roles or permissions - the brief
  assumes a single operator; PAM login just confirms identity, it's
  not a multi-tenant permission system.
- Does not implement password reset, MFA, or other auth flows beyond
  basic login/logout - this is a lab tool for one operator, not a
  product with those requirements.
- Does not install Postgres or Vault themselves - that's prerequisite
  infrastructure setup on `ai-deploy` (not yet done), same category as
  `utils/prereqs/ai-deploy/install-ansible.sh`. This spec assumes they
  exist and are reachable.

## 4. User scenarios
- As the operator, I want to log into the UI with the same credentials
  I already use on `ai-deploy`, without a separate account to manage.
- As the operator, if I enter the wrong password, I want a clear
  rejection, not a crash or a silent retry loop.
- As the operator, if I'm not logged in, I want protected pages to
  redirect me to login rather than showing broken/partial content.

## 5. Requirements
- **R1** The system MUST authenticate against the operator's real
  Ubuntu local account via PAM - not a separate credential store.
- **R2** A successful login MUST establish a session; subsequent
  requests to protected pages MUST NOT re-prompt for credentials
  within that session.
- **R3** An unauthenticated request to a protected page MUST redirect
  to login, not render partial content or error.
- **R4** A failed login MUST be rejected with a clear message, and
  MUST NOT crash the request or leak whether the username itself is
  valid (same error for bad username vs. bad password).
- **R5** The backend MUST be able to connect to Postgres and to Vault,
  and MUST fail its own startup/health check clearly if either is
  unreachable - not silently run in a half-working state.

## 6. Acceptance criteria
- **AC1** (R1) Given valid Ubuntu local credentials, when the operator
  logs in, then they reach the authenticated area.
- **AC2** (R4) Given an invalid password for a valid username, when
  the operator attempts login, then they see a generic auth-failure
  message (not "wrong password" specifically).
- **AC3** (R4) Given a username that doesn't exist, when login is
  attempted, then the same generic message as AC2 is shown.
- **AC4** (R2) Given a successful login, when the operator navigates
  to a protected page within the same session, then no re-login is
  required.
- **AC5** (R3) Given no active session, when a protected page is
  requested directly, then the response redirects to login.
- **AC6** (R5) Given Postgres or Vault is unreachable, when the
  backend starts, then its health check reports failure clearly.

## 7. Constraints
- Requires Postgres and Vault actually installed and reachable from
  `ai-deploy` - not yet done as of this spec being written.
- PAM authentication from an unprivileged process is expected to work
  via `pam_unix`'s setuid `unix_chkpwd` helper (no root required for
  the backend) - to be confirmed during implementation, not assumed.

## 8. Open questions
- [x] Stack: FastAPI backend, Postgres, Vault, PAM auth (e.g.
      `python-pam`), htmx/Alpine.js frontend - decided 2026-10-20.
      `xterm.js` is NOT part of this foundation; it belongs to spec
      008 (Terminal), the only place it's actually used.
- [ ] Exact Postgres schema for "UI-based info" - deferred to plan.md,
      and will likely grow as 001/002/008 are built rather than being
      fully designed up front.

---
### Ready checklist
- [x] Problem and goal make sense to someone without context
- [x] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [x] Every MUST has at least one acceptance criterion
- [x] Non-goals list at least one thing someone might reasonably assume is in scope
- [x] No implementation detail beyond the stack decision itself (that goes in plan.md)
- [x] Doesn't contradict the brief's principles or non-goals
- [x] Open questions resolved or deferred
