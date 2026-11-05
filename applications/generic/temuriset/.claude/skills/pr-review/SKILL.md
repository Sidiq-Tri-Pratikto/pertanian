---
name: pr-review
description: Review the current branch against main for correctness, constitution compliance, compatibility, and test gaps, and summarize the PR. Use when asked to review a branch, diff, or PR.
compatibility: Requires a git repository with an origin/main branch
---

# PR Review

1. Refresh the base and read the change:

   ```bash
   git fetch origin main
   git diff origin/main...HEAD
   ```

   Always compare against `origin/main`. If the fetch fails, stop and report it.

2. Read `.specify/memory/constitution.md`, then the rules that apply to the changed files. `.claude/rules/004-code-review.md` is the checklist.

3. Review in this order. Skip a section with nothing to report.

   **A. Correctness and compliance (critical)**
   - Logic errors, unhandled edge cases, spec or issue mismatches.
   - Constitution and rule violations, citing the rule.
   - Module shape per `005-module-structure`.
   - Error handling per `008-error-handling`.

   **B. Compatibility (critical)**
   - Breaking API changes, repurposed error codes, removed fields without deprecation.
   - Migrations: new ones added, none edited, safe for the running version.
   - Settings: new ones have safe defaults and appear in `.env.example`.
   - Dependencies: justified and minimal.

   **C. Design (high)**
   - Layer boundaries, abstractions with one implementation, code that can be deleted.
   - Blocking calls in async code, missing timeouts, unbounded work.
   - N+1 queries, missing indexes, unpaginated lists.

   **D. Tests (high)**
   - New and changed behavior covered, including failure paths.
   - Would these tests fail if the logic broke?
   - `Condition`/`Expected` docstrings per `003-testing`.

4. Report:
   - **Summary:** what the PR does, in a few sentences.
   - **Findings:** ranked, each with `path:line`, severity (blocker, major, minor), the problem, and the fix.
   - **Verdict:** ready to merge, or what must change first.

Report only real findings. Do not pad with praise or style notes that ruff handles.
