# Spec 001: Add a todo item from the CLI

**Status:** Ready
**Date:** 2026-10-20
**Brief:** [../../BRIEF.md](../../BRIEF.md) · **Roadmap item:** 001

<!-- EXAMPLE: shows a finished, Ready feature spec. -->

## 1. Problem
There's no way to put a task into the system yet. This is the first slice:
without it, no other feature has any data to work with.

## 2. Goal
A user can add a todo item with a single command and see it saved straight away.

## 3. Non-goals
- No due dates, priorities or tags (a later spec).
- No editing or deleting items.

## 4. User scenarios
- As a user, I want to run `todo add "Buy milk"` so that the task is saved without opening any file.
- As a user, if I run `todo add` with no text, I want a clear error rather than an empty item being saved.

## 5. Requirements
- **R1** The CLI MUST accept `todo add "<text>"` and save a new item containing that text.
- **R2** Each item MUST get a unique, increasing integer ID.
- **R3** The CLI MUST reject empty or whitespace-only text with a non-zero exit code.
- **R4** The CLI MUST create the data file if it doesn't exist.
- **R5** The CLI SHOULD print the new item's ID on success.

## 6. Acceptance criteria
- **AC1** (R1, R5) Given an empty todo list, when I run `todo add "Buy milk"`, then the list contains one item "Buy milk" and the output is `Added #1`.
- **AC2** (R2) Given items #1 and #2 exist, when I add another, then it gets ID #3.
- **AC3** (R3) When I run `todo add "   "`, then the exit code is 1, stderr says `error: text is required`, and nothing is saved.
- **AC4** (R4) Given no data file, when I add an item, then the file is created and contains that item.

## 7. Constraints
- None beyond the brief's principles.

## 8. Open questions
- [x] Max text length? Deferred: no limit for now.
