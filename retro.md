# Retro Log

One entry per agent mistake. The routing column is the important one.

| # | Date | Feature | What went wrong | Root cause | Fix went into |
|---|------|---------|-----------------|------------|---------------|
| 1 | | | | | rule / spec / skill / test |
| 2 | 2026-10-20 | dc prereqs | `New-AiDeployLabCertTemplates.ps1` failed to parse on the DC with "string is missing the terminator" | An em dash (`—`) inside a `Write-Host` string literal; Windows PowerShell 5.1 misread the file's encoding on transfer, corrupting the character and breaking the string | rule (AGENTS.md: no non-ASCII characters in scripts) |
| 3 | 2026-10-20 | dc prereqs | `New-AiDeployLabCertTemplates.ps1`'s raw-ADSI template duplication kept failing with a generic `E_FAIL` on `pKIExpirationPeriod`, through several real fixes (stale COM reference, double-write of the period attributes, two-phase vs single-phase commit) - but the exact same logic always succeeded when run in isolation and always failed as part of the full script, with no structural difference ever found despite extensive live debugging | Unknown - never root-caused. Raw ADSI object creation for AD CS templates proved too fragile to debug further within reasonable effort | rule (AGENTS.md: cert template duplication is manual, not scripted - see `utils/prereqs/dc/duplicate-certificate-template.md`); script deleted |
| 4 | 2026-10-21 | 001 | Operator rejected at G4 to fix advisory findings: local-side failures (missing/loose Key B, bad inventory YAML, missing binary, bad --port, paths with spaces) gave misleading or traceback errors | The plan's failure design listed only target-side failures (R1-R3, R8, R9); preconditions on ai-deploy itself were never enumerated, so no AC or task covered them | test + code (T12-T15); consider adding "local preconditions" to the plan template's failure-path prompts |
