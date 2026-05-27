# Maintainer's Guide

Quick reference guide for project maintainers handling PRs, issues, and releases.

## Daily Workflow

### Reviewing Pull Requests

#### Before Review
- [ ] All CI/CD checks pass ✅
- [ ] Branch is up to date with main/develop
- [ ] No merge conflicts

#### During Review
1. **Code Quality**
   - [ ] Code follows PEP 8 and project style
   - [ ] Type hints present where required
   - [ ] No code duplication
   - [ ] Proper error handling
   - [ ] Docstrings for public functions

2. **Testing**
   - [ ] Tests added for new features
   - [ ] Bug fixes include regression tests
   - [ ] Coverage doesn't decrease
   - [ ] Tests are meaningful (not just counting coverage)

3. **Security**
   - [ ] No hardcoded secrets
   - [ ] No SQL injection/XSS vulnerabilities
   - [ ] External dependencies are vetted
   - [ ] No privilege escalation issues

4. **Documentation**
   - [ ] README updated if needed
   - [ ] Docstrings present
   - [ ] Comments explain complex logic
   - [ ] CHANGELOG/release notes if needed

#### After Review
- **Approve**: Test locally if major changes
- **Request Changes**: Be specific with feedback
- **Comment**: Ask for clarification if needed

### Handling Issues

#### Triage
1. Check for duplicates
2. Label appropriately
3. Add to milestone if applicable
4. Assign to owner (or leave unassigned)

#### Responding
- Acknowledge receipts on same day
- Ask for more info if unclear
- Link to related issues/PRs

#### Closing
- Only close if resolved
- Thank contributors
- Document solutions for visibility

---

## Branch Management

### Creating Protected Branches

Protected branches are configured via GitHub Settings (see BRANCH_PROTECTION_RULES.md).

### Merging Strategy

```bash
# For feature branches: Squash and merge
# - Keeps history clean
# - Each feature is one commit

# For hotfixes to main: Merge or rebase
# - Maintains history clarity
# - Document the merge

# Avoid: Multiple merge commits (use squash)
```

### Force Push Policy

**When allowed:**
- Fixing commit history before PR goes to main (discuss first)
- Removing accidentally exposed secrets (revoke immediately)
- Resolving conflicts in rebase (with team agreement)

**When NOT allowed:**
- After PR is approved
- To public branches (main/develop)
- Without documenting in PR

---

## Release Management

### Before Release

1. **Update Documentation**
   ```
   - CHANGELOG.md (summarize changes)
   - README.md (if dependencies changed)
   - Requirements.txt (if updated)
   ```

2. **Version Bump**
   - Follow semver: MAJOR.MINOR.PATCH
   - Update in: `pyproject.toml`, `__version__.py` (if exists)

3. **Final Testing**
   ```bash
   # Full test suite
   pytest --cov=.
   
   # Type checking
   mypy .
   
   # Security check
   bandit -r .
   ```

4. **Code Review**
   - Release PR reviewed by another maintainer
   - All CI checks pass

### Release Steps

1. Create release branch: `release/v0.1.0`
2. Bump version numbers
3. Create PR to main
4. Merge via GitHub (squash merge)
5. Create GitHub Release:
   - Tag version (e.g., `v0.1.0`)
   - Write release notes
   - Add binary if applicable
6. PyPI publish (if applicable):
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

### Post-Release

- [ ] Tag pushed to GitHub
- [ ] Release notes posted
- [ ] Package published (if applicable)
- [ ] Update docs website
- [ ] Announce in relevant channels
- [ ] Backport critical fixes to release branch

---

## Managing Dependencies

### Adding New Dependencies

```bash
# 1. Add to requirements.txt with version constraints
# 2. Update pyproject.toml
# 3. Run tests with new dependency
# 4. Document why it's needed in PR description
# 5. Check for security issues: safety check
```

### Updating Dependencies

```bash
# Monthly or as needed
pip install --upgrade pip
pip list --outdated

# Test after updates
pytest --cov=.

# Commit security updates immediately
# Batch feature updates with releases
```

---

## Security Management

### Vulnerability Response

1. **Identify**: Security scanning tools or reports
2. **Assess**: Severity and impact
3. **Fix**: ASAP for critical issues
4. **Patch**: Release patch version (PATCH bump)
5. **Announce**: Notify users/contributors
6. **Document**: In release notes

### Secret Management

```bash
# Scan for exposed secrets
git secrets --scan

# Remove if found
git filter-repo --invert-paths --path <secret-file>

# Force push and revoke credentials
# (Only if no alternative - document!)
```

---

## Communication

### Announcing Changes

- **Breaking Changes**: Major version bump + clear migration guide
- **New Features**: Feature version bump + documentation
- **Bug Fixes**: Patch version bump (mention in release notes)
- **Security**: Patch immediately, announce in security section

### High-Priority Communications

- Security vulnerabilities: Email maintainers
- Project deprecation: Public issue + discussions
- Major changes: Discussions section + issue
- Contribution policy changes: CONTRIBUTING.md + announcement

### Response Times

- **Critical bugs**: 24 hours
- **Security issues**: Private + quick triage
- **Feature requests**: 1 week
- **Questions**: Best effort (community help appreciated)

---

## Tools & Automation

### GitHub Actions

The CI/CD pipeline automatically:
- ✅ Tests all PRs
- ✅ Runs security scans
- ✅ Checks code quality
- ✅ Reports coverage

### Useful Commands

```bash
# Run full test suite locally before pushing
pytest --cov=. --cov-report=html

# Format code
black .

# Check imports
isort . --check-only

# Type check
mypy .

# Security scan
bandit -r .
```

### GitHub Labels

Organize issues and PRs:
- `good first issue` - Perfect for new contributors
- `help wanted` - Need community assistance
- `in progress` - Someone is working on it
- `blocked` - Waiting on something
- `priority: critical|high|medium|low`
- `type: bug|feature|docs|refactor`
- `status: review|testing|ready`

---

## Problem Resolution

### Common Issues

**PR stuck in review:**
1. Ping reviewer comment (max 1 week)
2. Offer to update if needed
3. Escalate to another reviewer if stuck >2 weeks

**Conflicting opinions:**
1. Document different views in PR
2. Make decision and document reasoning
3. Document in contributing guide to prevent future conflicts

**Contributor unresponsive:**
1. Give 2 weeks for response
2. Close with comment about reopening
3. Keep tags for future work

### Burnout Prevention

- Don't feel obligated to review everything
- Distribute review load
- Set boundaries on response times
- Thank active contributors publicly
- Take breaks as needed

---

## Metrics to Track

Monthly/Quarterly:

- Number of issues opened vs closed
- Average PR review time
- Test coverage percentage
- Number of active contributors
- Dependency vulnerability count
- Release frequency

---

## Troubleshooting

### CI Failures

```bash
# Run locally first
pytest
black .
flake8 .
mypy .

# Check Python version compatibility
python --version  # Should be 3.9+
```

### Merge Conflicts

```bash
# Resolve locally
git checkout feature-branch
git rebase develop
# Fix conflicts
git add .
git rebase --continue
git push -f origin feature-branch
```

### Accidental Push

```bash
# If you pushed something wrong
git revert HEAD  # Creates new commit undoing changes

# Or rebase (only if no one pulled yet)
git reset --soft HEAD~1
git push -f origin branch-name
```

---

## Resources

- [GitHub Docs](https://docs.github.com)
- [Python Best Practices](https://pep8.org)
- [Semantic Versioning](https://semver.org)
- [Keep a Changelog](https://keepachangelog.com)
- [Open Source Guides](https://opensource.guide)

---

**Last Updated**: May 2026

**Maintainers**: See CODEOWNERS file

**Questions?** Open a discussion or email the maintainer team.
