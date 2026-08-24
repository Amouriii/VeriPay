# Branch Protection on `main`

## Why
`proto/` and `libs/` are the shared contract boundary for parallel work-trees.
Branch protection ensures no work-tree can land broken contracts directly on
`main` — changes must pass CI and be reviewed first.

## Rules enforced on `main` (verified via GitHub API)

| Rule | Value |
|---|---|
| Required status checks | `Buf lint & breaking`, `Lint (ruff + mypy + eslint)`, `Test (pytest)`, `Test (vitest)` |
| Strict status checks | `true` — branch must be up to date with `main` before merge |
| Require PR review | 1 approving review required before merge |
| Enforce for admins | `true` — rules apply to everyone, including repo admins |
| Linear history | `true` — no merge commits; rebase or squash only |
| Allow force pushes | `false` — no `git push --force` to `main` |
| Allow deletions | `false` — `main` cannot be deleted |

## Consequences for work-trees
1. **Direct pushes to `main` are blocked.** Every change lands via pull request.
2. **A PR cannot merge until all four CI jobs pass** and at least one approving review is recorded.
3. **The branch must be up to date** with `main` before merging (`strict: true`), so rebase onto the latest `main` before opening a PR.
4. **Contract changes** (`proto/` or `libs/`) are especially sensitive — request review from someone outside your own work-tree to catch contract drift.

## How to merge your work-tree branch
```bash
git checkout main
git pull --rebase            # stay current
git checkout feat/<service>-<topic>
git rebase main              # satisfy "strict" check
git push origin feat/<service>-<topic --force-with-lease  # rebased branch

# Open a PR on GitHub, wait for the four CI checks to pass,
# get one approving review, then squash-merge.
gh pr create --base main --head feat/<service>-<topic --fill
```

## Re-applying protection (if rules are ever removed)
```bash
gh api -X PUT repos/Amouriii/VeriPay/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --input docs/runbooks/branch-protection-payload.json
```
See the JSON payload in the commit that added this file.
