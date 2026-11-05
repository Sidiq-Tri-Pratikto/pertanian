---
name: pr-generate-description
description: Generate a GitHub PR description from the current branch diff against main, filling .github/pull_request_template.md. Use when asked to write, draft, or update a PR description.
compatibility: Requires a git repository with an origin/main branch
---

# Generate PR Description

1. Refresh the base and read the change:

   ```bash
   git fetch origin main
   git diff --name-status origin/main...HEAD
   git diff origin/main...HEAD
   git log --oneline origin/main..HEAD
   ```

   Always compare against `origin/main`, not local `main`. If the fetch fails, stop and report it.

2. Read `.github/pull_request_template.md` and fill every section from the diff:
   - **Title:** Conventional Commits, `<type>(<scope>): <description>`, verb first.
   - **Summary:** what changed and why, in a few sentences. Name breaking changes and migrations.
   - **How to Test:** concrete steps with expected results, using Makefile targets where they exist.
   - **Related Issues:** only issues named in the branch, commits, or spec. Do not invent any.
   - **Author Checklist:** tick only what the diff or a command you ran proves. Leave the rest unticked.

3. Run `make check` from each changed application and report the result. Do not tick "tests pass" without it.

4. Output the description as markdown. Do not open or edit the PR unless asked.

Base claims on the diff only. Never guess intent that the code, commits, or spec do not show.
