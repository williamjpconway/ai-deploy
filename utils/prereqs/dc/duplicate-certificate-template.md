# Duplicate a certificate template (manual)

Why manual: a scripted approach (raw ADSI object creation) hit a
reproducible but unexplained `E_FAIL` on `pKIExpirationPeriod`, which
survived extensive isolated debugging - the exact same logic succeeded
every time in isolation, but failed every time as part of the full
script, with no structural difference ever found (see `retro.md`). The
Certificate Templates console's "Duplicate Template" is Microsoft's own
tested code path and avoids all of this. This is a one-time lab setup
task per template needed, not worth scripting fragility for.

## Steps

1. On a machine with the Certificate Templates console available (the
   CA itself, or anywhere with RSAT AD CS tools), open `certtmpl.msc`.
2. Find the source template to base the lab copy on - whichever one
   the "Create a Certificate" playbook will actually target.
3. Right-click it -> **Duplicate Template**.
4. In the new template's properties:
   - **General** tab: set *Template display name* to `lab-<original
     name>` (matches this project's naming convention). Set *Validity
     period* to 2 years (down from the source's typical 5-year
     default). Leave *Renewal period* at its default unless you have a
     reason to change it.
   - **Security** tab: grant the `ai-deploy-operators` group **Enroll**
     only - not Autoenroll, not Full Control. This matches the
     least-privilege delegation already decided for this project (see
     `AGENTS.md`'s Windows AD domain account section).
5. Click OK to save.
6. Publish it on the CA: open the Certification Authority console
   (`certsrv.msc`) -> **Certificate Templates** -> right-click -> **New**
   -> **Certificate Template to Issue** -> select `lab-<original name>`
   -> OK.
7. Verify: `certutil -CATemplates` should list it, or confirm it's
   selectable when requesting a certificate via `certreq` or the Web
   Enrollment page.
