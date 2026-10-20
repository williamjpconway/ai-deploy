# Retro Log

One entry per agent mistake. The routing column is the important one.

| # | Date | Feature | What went wrong | Root cause | Fix went into |
|---|------|---------|-----------------|------------|---------------|
| 1 | | | | | rule / spec / skill / test |
| 2 | 2026-10-20 | dc prereqs | `New-AiDeployLabCertTemplates.ps1` failed to parse on the DC with "string is missing the terminator" | An em dash (`—`) inside a `Write-Host` string literal; Windows PowerShell 5.1 misread the file's encoding on transfer, corrupting the character and breaking the string | rule (AGENTS.md: no non-ASCII characters in scripts) |
