# Spec 009: Test VM lab

**Status:** Draft
**Date:** 2026-10-21
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 009

## 1. Problem
The agent has no disposable targets to test against. Spec 001's
destructive test (SSH shell switched to `cmd.exe`) had to run on the
real domain controller, needed the operator to run it by hand, and
`masterchief`'s missing group membership on `dc` was only found when the
live tests hit it. Specs 007 (Ubuntu) and 003-006 need real, breakable
Windows and Ubuntu targets too.

## 2. Goal
The agent can, without the operator, bring up to ten Windows and ten
Ubuntu test VMs from the existing Proxmox templates into a known clean,
onboardable state, reset them to that state, and never touch any other
VM.

## 3. Non-goals
- The product itself still never calls a hypervisor API. This is test
  tooling only: onboarding, operations and the UI (specs 000-008) must
  not use it or depend on it, and no product test may require it -
  product tests take any target IP (decided 2026-10-21).
- No UI for the lab: the web UI (specs 000/002) doesn't show or manage
  test VMs. That would be a new roadmap item.
- No VMs beyond the 20 fixed slots, and no access to any other VM
  (including `dc` and `ai-deploy`).
- Does not build or re-seal the templates. Re-sealing
  `tmpl-windows2025` with an answer file is a one-off operator prep
  step that this feature documents and depends on, but doesn't automate.
- Does not create the AD account, OU or Group Policy it relies on -
  those are operator prep steps (AD writes), documented here, run by
  the operator.
- No production VM lifecycle management of any kind (the brief's
  non-goal stands for the product).

## 4. User scenarios
- As the agent, during a feature's Develop/Test stage, I want to reset
  a Windows test VM to clean, break it on purpose, and test against it,
  so destructive tests never need the real DC or the operator.
- As the agent, I want a fresh Windows clone to come up already renamed,
  joined to the domain and onboardable by spec 001's checks, with no
  console interaction.
- As the operator, I want a hard cap of 10 Windows + 10 Ubuntu test VMs
  that holds even if the agent's tooling has a bug.
- Unhappy path: if a clone doesn't get an IP, can't be joined, or a
  slot outside the 20 is requested, the agent gets a specific failure and
  nothing outside the slots is affected.

## 5. Requirements
- **R1** The system MUST only create, change, reset or remove VMs in
  20 fixed slots: ten for Windows (VMIDs 9101-9110) and ten for
  Ubuntu (9201-9210) (widened from 2 + 2 on 2026-10-21), cloned from `tmpl-windows2025` (9000) and
  `tmpl-ubuntu2604` (9001). The cap MUST be enforced by Proxmox
  permissions, not only by the tooling (already in place: see section 7).
- **R2** The system MUST bring a slot from empty to a clean state with
  no console interaction: cloned, started, its IP found, reachable over
  SSH with Key B.
- **R3** A clean Windows slot MUST have a unique hostname, be joined to
  the domain in `OU=ai-deploy-test`, have `masterchief` in its local
  Administrators group, and have its own SSH host keys (not the
  template's) - so spec 001's onboarding passes against it.
- **R4** A clean Ubuntu slot MUST have a unique hostname and network
  config (via Proxmox cloud-init) and pass Ubuntu onboarding's checks
  (spec 007). Ubuntu slots are not joined to AD.
- **R5** The system MUST save a clean state per slot and reset a slot to
  it on request, without re-cloning. It MUST NOT destroy a slot;
  rebuilding a slot from scratch is an operator step.
- **R6** The system MUST report a specific failure (which slot, which
  step) when a slot can't reach clean, and leave other slots and all
  non-slot VMs untouched.
- **R7** The system MUST keep the Proxmox token and the AD join
  credential on `ai-deploy` only, never in the repo, logs or output.
- **R8** The system SHOULD show which slots exist and their state
  (empty / clean / in use).

## 6. Acceptance criteria
- **AC1** (R1) Given the tooling asks Proxmox to create a VM outside
  9101-9110 / 9201-9210, when it runs, then Proxmox refuses
  it and the tooling reports which slot limit was hit.
- **AC2** (R2, R3) Given an empty Windows slot, when it's brought up,
  then within 20 minutes it's renamed, domain-joined in
  `OU=ai-deploy-test`, has its own SSH host keys, and spec 001's
  `onboard-windows` passes against it.
- **AC3** (R2, R4) Given an empty Ubuntu slot, when it's brought up,
  then it has its own hostname and IP and is reachable over SSH with
  Key B.
- **AC4** (R5) Given a slot changed after reaching clean (e.g. SSH shell
  set to `cmd.exe`), when it's reset, then it's back to clean and
  onboarding passes again.
- **AC5** (R6) Given a clone that never reports an IP, when it's brought
  up, then the failure names the slot and the IP step, and no other VM
  changed.
- **AC6** (R7) Given any run, then neither secret appears in output,
  logs or the repo.

## 7. Constraints
- Proxmox (decided and set up 2026-10-21, verified read-only): VE 9.2.3,
  node `pve` at 192.168.0.199. API user `ai-deploy-test@pve` (no
  password), token `lab` (`--privsep 0`), stored in
  `~/.config/ai-deploy/proxmox.env` on `ai-deploy` (mode 0600).
  Permissions only on: templates 9000/9001 (`VM.Audit`, `VM.Clone`);
  slots 9101-9110 and 9201-9210 (allocate, CD-ROM for cloud-init, config, power, snapshot,
  rollback, guest-agent audit); storage `local` and `local-lvm`; bridge
  `vmbr0`. The token gets 403 on any other VM.
- Templates: QEMU guest agent installed; DHCP available on `vmbr0`.
- Templates (re-sealed 2026-10-21, see the spike results below):
  `tmpl-windows2025` (9000) is full retail Windows Server 2025 Standard
  with the operator's key in its answer file - like-for-like with real
  servers (decided 2026-10-21, replacing the earlier evaluation-edition
  plan). `SetupComplete.cmd` deletes the answer file from every clone.
  Known limit: one retail key on many clones may stop activating after
  the first few - Windows runs unactivated, so tests aren't affected.
  `tmpl-ubuntu2604` (9001) sealed with `seal-template.sh`.
- No limit on how many slots run at once (decided 2026-10-21).
- Confirmation (decided 2026-10-21, `AGENTS.md`): actions confined to
  the 20 slots and their computer objects in `OU=ai-deploy-test` need
  no operator confirmation; anything outside - `dc`, Domain Admin,
  templates, other OUs - keeps the confirmation rules.
- The brief's principles apply to the tooling: idempotent, verify
  don't assume.
- Spike results (2026-10-21, outside the lifecycle - no feature code):
  - Token can clone 9000/9001 into the slots, set the MAC, start, stop
    and delete. **Deleting a VM removes its `/vms/<id>` permission**
    (confirmed on 9201; re-baking 9000 removed `/vms/9000` too) - the
    operator re-adds it after any rebuild. Adding a cloud-init drive
    needs `VM.Config.CDROM` (now granted).
  - Windows template 9000 re-sealed 2026-10-21 from a clone: answer file
    (retail key, random name, `SkipRearm`) plus `SetupComplete.cmd`
    that deletes both answer-file copies (the answer file's own
    `FirstLogonCommands` cleanup never runs - clones are only reached
    over SSH) and creates SSH host keys if missing; host keys removed
    before sysprep. A fresh clone: IP via guest agent in 42 s, SSH with
    Key B in 59 s, unique host key, random name, no answer file left,
    licensed, PowerShell shell.
  - `dc` and the pre-2026-10-21 template shared one SSH host key
    (`SHA256:AQk3...`) - `dc` should get its own (operator decision,
    change on `dc`).
  - Ubuntu template 9001: Key B and passwordless sudo work on a clone,
    but qemu-guest-agent is missing and clones share hostname,
    machine-id and SSH host keys. `utils/onboarding/ubuntu2604/seal-template.sh`
    drafted to fix it (dry-run only so far).

## 8. Open questions
- [x] Scope change: carve-out agreed 2026-10-21 and written into
      `BRIEF.md` (sections 2, 3, 6, 7) and `AGENTS.md` (Infrastructure
      access, Tools).
- [x] Confirmation rules inside the sandbox: agreed 2026-10-21 and
      written into `AGENTS.md` - no confirmation for actions confined to
      the slots and their computer objects in `OU=ai-deploy-test`
      (join-only account); everything else keeps the confirmation rules.
      A Claude Code permission rule for the lab tooling's commands may
      also be needed (auto mode blocked 001's approved AC3 run) -
      deferred to plan.md, once the commands exist.
- [x] Windows product key for test clones: full retail Windows with
      the operator's key in the answer file, like-for-like (decided
      2026-10-21, replacing the earlier evaluation-edition choice). The
      answer file is removed from every clone by `SetupComplete.cmd`.
- [x] Template: retail Windows re-sealed as VMID 9000 (done 2026-10-21);
      the token's ACL on `/vms/9000` re-added after the swap (removing a
      VM removes its ACL - confirmed).
- [x] AD prep (decided 2026-10-21): OU
      `OU=ai-deploy-test,OU=ai-deploy,DC=domain,DC=internal`; join-only
      account `svc-ai-deploy-join` (join/remove computers in that OU
      only); Group Policy on that OU (`masterchief` in local
      Administrators; machine account password changes disabled so
      rollbacks don't break the domain trust). Credential in
      `~/.config/ai-deploy/ad-join.env` (0600) on `ai-deploy` - created
      with a dummy password, the operator sets the real one. Creating
      the OU, account and GPOs is an operator prep step (AD write).
- [x] Reset model: rollback only (decided 2026-10-21). Each slot is
      cloned once and snapshotted `clean`; every reset is a rollback.
      Rebuilding a slot from scratch (destroy + re-clone) is an operator
      step, since destroying a VM very likely removes its slot
      permission - the operator re-adds it.
- [x] IPs: plain DHCP (decided 2026-10-21, replacing the earlier
      reservations plan when slots went to 10 + 10) - the IP is read
      from the guest agent each time. Each slot keeps a fixed MAC,
      `BC:24:11:00:91:NN` for Windows slot 91NN and `BC:24:11:00:92:NN`
      for Ubuntu slot 92NN, so the router's lease table shows which slot
      is which. Network 192.168.0.0/22, DHCP from 192.168.0.254.
- [x] Ubuntu slots: no AD join for now (decided 2026-10-21) - spec 007
      uses the local `masterchief` user with Key B.
- [x] Storage: keep `local` (decided 2026-10-21) - room for custom
      cloud-init snippets later.
- [x] AC2 time limit: 20 minutes (decided 2026-10-21).

---
### Ready checklist
- [ ] Problem and goal make sense to someone without context
- [ ] Every requirement is testable (no "fast", "easy", "robust" without a number)
- [ ] Every MUST has at least one acceptance criterion
- [ ] Non-goals list at least one thing someone might reasonably assume is in scope
- [ ] No implementation detail (that goes in plan.md)
- [ ] Doesn't contradict the brief's principles or non-goals
- [ ] Open questions resolved or deferred
