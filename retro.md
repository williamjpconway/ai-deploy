# Retro Log

One entry per agent mistake. The routing column is the important one.

| # | Date | Feature | What went wrong | Root cause | Fix went into |
|---|------|---------|-----------------|------------|---------------|
| 1 | | | | | rule / spec / skill / test |
| 2 | 2026-10-20 | dc prereqs | `New-AiDeployLabCertTemplates.ps1` failed to parse on the DC with "string is missing the terminator" | An em dash (`—`) inside a `Write-Host` string literal; Windows PowerShell 5.1 misread the file's encoding on transfer, corrupting the character and breaking the string | rule (AGENTS.md: no non-ASCII characters in scripts) |
| 3 | 2026-10-20 | dc prereqs | `New-AiDeployLabCertTemplates.ps1`'s raw-ADSI template duplication kept failing with a generic `E_FAIL` on `pKIExpirationPeriod`, through several real fixes (stale COM reference, double-write of the period attributes, two-phase vs single-phase commit) - but the exact same logic always succeeded when run in isolation and always failed as part of the full script, with no structural difference ever found despite extensive live debugging | Unknown - never root-caused. Raw ADSI object creation for AD CS templates proved too fragile to debug further within reasonable effort | rule (AGENTS.md: cert template duplication is manual, not scripted - see `utils/prereqs/dc/duplicate-certificate-template.md`); script deleted |
