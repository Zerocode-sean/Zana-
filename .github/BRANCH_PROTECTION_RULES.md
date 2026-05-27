# Git Branch Protection Rules

This document outlines the branch protection rules that should be configured on GitHub to ensure code quality and maintain project integrity.

## Overview

Branch protection rules enforce code quality standards and prevent accidental or unauthorized changes to critical branches (`main` and `develop`).

## Main Branch Protection Rules

### Branch: `main`

This is the production-ready branch. These rules should be strictly enforced:

#### 1. Require Pull Request Reviews
- **Minimum required reviewers**: 1-2 (recommended 2 for critical projects)
- **Dismiss stale pull request approvals when new commits are pushed**: ✅ Enabled
- **Require review from Code Owners**: ✅ Enabled (if CODEOWNERS file exists)
- **Restrict who can dismiss pull request reviews**: ✅ Enable (only admins)

#### 2. Require Status Checks to Pass
- **Require branches to be up to date before merging**: ✅ Enabled
- **Require passing status checks before merging**:
  - ✅ `CI/CD Pipeline` (lint-and-test)
  - ✅ `code-quality`
  - ✅ `security-check`
  - ✅ `build-check`

#### 3. Require Code Scanning Results
- ✅ Code scanning tools must pass (CodeQL, Snyk, etc.)

#### 4. Additional Protections
- **Number of approving reviews required**: 1-2
- **Dismiss stale pull request approvals**: Yes
- **Require conversation resolution**: ✅ Enabled
- **Require signed commits**: ✅ Recommended (optional)
- **Require linear history**: ✅ Recommended
- **Restrict who can push to matching branches**: ✅ Admins only
- **Block force pushes**: ✅ Enabled
- **Block deletions**: ✅ Enabled

#### 5. Requirement Status Checks
All GitHub Actions workflows must pass:
- `CI/CD Pipeline`
- `code-quality`
- `security-check`
- `build-check`

---

## Develop Branch Protection Rules

### Branch: `develop`

This is the development/staging branch. Rules are slightly relaxed but still maintained:

#### 1. Require Pull Request Reviews
- **Minimum required reviewers**: 1
- **Dismiss stale pull request approvals when new commits are pushed**: ✅ Enabled
- **Require conversation resolution**: ✅ Enabled

#### 2. Require Status Checks to Pass
- **Require branches to be up to date before merging**: ✅ Enabled
- **Require passing status checks before merging**:
  - ✅ `CI/CD Pipeline` (lint-and-test)
  - ✅ `security-check`

#### 3. Additional Protections
- **Block force pushes**: ✅ Enabled
- **Block deletions**: ✅ Enabled
- **Restrict who can push to matching branches**: Optional (maintainers)

---

## How to Enable These Rules on GitHub

1. Go to repository **Settings** → **Branches**
2. Click **Add rule** under "Branch protection rules"
3. Enter the branch name pattern:
   - For `main`: `main`
   - For `develop`: `develop`
4. Configure the following sections:

### Protect matching branches
- ✅ Require a pull request before merging
  - ✅ Require approvals (1-2)
  - ✅ Dismiss stale pull request approvals
  - ✅ Require review from code owners
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date
  - Select all workflow checks
- ✅ Require conversation resolution before merging
- ✅ Require signed commits
- ✅ Require linear history
- ✅ Require up-to-date branches before merging

### Rules to bypass
- Only allow admins

---

## Naming Convention for Branches

All contributors should follow this naming convention:

```
<type>/<description>

type: feature, fix, docs, refactor, test, chore
description: lowercase, hyphens instead of spaces
```

### Examples
- `feature/add-appointment-rescheduling`
- `fix/timezone-bug-in-reminders`
- `docs/update-webhook-setup`
- `refactor/simplify-orchestrator-logic`
- `test/add-language-detection-tests`

---

## PR Merge Strategy

### Recommended: Squash and Merge

```bash
# Squash commits when merging to main/develop
# This keeps history clean and linear
```

**Settings → General → Pull Requests → Allow squash merging**

### Optional: Allow Rebase and Merge
- Useful for feature branches to keep a linear history
- Configure: **Settings → General → Pull Requests → Allow rebase merging**

### Avoid: Regular Merge Commits
- Creates complex merge commits
- Disable or limit to specific cases

---

## Code Owners Configuration

Create `.github/CODEOWNERS` file to define ownership:

```
# Global owners - review all changes
* @maintainer1 @maintainer2

# Specific file owners
/webhook/ @webhook-expert
/agents/ @ai-expert
/database/ @database-expert
/tools/ @tools-expert
```

Then enable **Require review from Code Owners** in branch protection rules.

---

## Enforcement Guidelines

### When PR Checks Fail

1. **CI Pipeline Failure**: Run tests locally and fix issues before pushing
2. **Review Required**: Wait for at least 1-2 approvals
3. **Merge Conflicts**: Resolve conflicts by rebasing on latest `main`/`develop`
4. **Status Checks**: All must pass (no bypassing except admins)

### What NOT to Do

❌ Force push to `main` or `develop`
❌ Bypass branch protection rules
❌ Merge without reviews
❌ Merge failing CI/CD checks
❌ Delete main/develop branches

### Admin Override

Only in emergencies, admins can:
- Bypass branch protection (not recommended)
- Force push (document reason)
- Merge without reviews (document reason)

**Always communicate if you use admin override!**

---

## Monitoring & Maintenance

### Regular Checks

- **Weekly**: Review merged PRs for quality
- **Monthly**: Check security vulnerabilities
- **Quarterly**: Update branch protection rules if needed

### Activity Logs

View enforcement of branch protection rules in:
- **Settings → Branches** - See recent protections applied
- **Audit Log** - See all branch permission changes (enterprise only)

---

## Questions or Issues?

If a branch protection rule is causing problems:
1. Document the issue in a new issue/discussion
2. Contact maintainers
3. We may adjust rules based on feedback

---

**Last Updated:** May 2026

**Maintained By:** Project Maintainers

**Review Schedule:** Quarterly
