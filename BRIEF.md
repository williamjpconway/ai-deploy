# Product Brief: todo

**Status:** Agreed
**Last revised:** 2026-10-20

<!-- EXAMPLE: a filled-in brief for a toy product. Replace it with your real one
     (blank template: templates/BRIEF.md). -->

## 1. One-liner
A personal, offline command-line tool for tracking todos.

## 2. Shape
A single CLI executable, installed and run locally on the user's machine.
No server, no container, no VM image, no deployment target of any kind.

## 3. Infrastructure
- None needed. Installed and run directly on the user's own machine.

## 4. Problem
Quick tasks come up while working in the terminal. Switching to a GUI app or
hand-editing a file to note them is slow and error-prone, so tasks get lost.

## 5. Users
One developer, working in a terminal, on their own machine.

## 6. Principles
- Terminal-first: every action is a single command.
- Data is a plain, human-readable file the user owns.
- Works fully offline.
- Clear errors and non-zero exit codes, so it can be scripted.

## 7. Non-goals (product level)
- No multi-user, accounts or sharing.
- No sync, cloud or network features.
- No GUI or TUI.

## 8. Success looks like
- Adding, listing and completing a task each take one command.
- The data file survives every command with no corruption (verified by tests).
