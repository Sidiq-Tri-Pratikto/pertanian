---
description: Branch naming, commit format, PR, and merge rules. Use for any git or PR work.
globs: ".github/**"
alwaysApply: false
trigger: model_decision
paths:
  - ".github/**"
---
# Git Workflow

## Branches

| Prefix | Type | Example |
|---|---|---|
| `f/` | Feature | `f/add-order-history` |
| `e/` | Enhancement | `e/improve-search-latency` |
| `b/` | Bugfix | `b/fix-token-expiry` |
| `chore/` | Maintenance | `chore/update-dependencies` |
| `NNN-name` | Spec Kit feature | `003-order-history` |

Spec Kit creates `NNN-name` branches and its scripts depend on that shape. Do not rename them.

## Commits and PR titles

Conventional Commits: `<type>(<scope>): <description>`.

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`. Start the description with a verb.

```
feat(orders): add order history endpoint
fix(auth): resolve token expiry check
```

## Pull requests

- Every branch targets `main`. Sync with `origin/main` before opening.
- Fill in `.github/pull_request_template.md`.
- All checks pass and the checklist is complete before review.
- Keep PRs small; one logical change.

## Merging

Squash merge to `main`. The squash commit message follows the same Conventional Commits format.

## Before opening a PR

- [ ] `make check` passes
- [ ] Tests cover the change, including failure paths
- [ ] Docstrings and READMEs updated
- [ ] No secrets or sensitive data
- [ ] Migrations added, none edited
