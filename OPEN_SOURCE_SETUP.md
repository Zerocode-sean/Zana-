# Open Source Setup Guide

This guide walks you through setting up your Zana repository for open-source contributions.

## ✅ What's Already Created

### 1. CI/CD Pipeline
- **File**: `.github/workflows/ci.yml`
- **Features**:
  - Automated testing on Python 3.9, 3.10, 3.11
  - Code linting (flake8, black)
  - Type checking (mypy)
  - Security scanning (bandit, safety)
  - Code quality analysis (pylint)
  - Coverage reporting (Codecov integration)
  - Automatic PR comments on test results

### 2. Contributing Guidelines
- **File**: `CONTRIBUTING.md`
- **Includes**:
  - Development setup instructions
  - Branch naming conventions
  - Commit message guidelines
  - PR process workflow
  - Testing requirements
  - Code style standards
  - Issue reporting templates

### 3. Git Protection Rules Documentation
- **File**: `.github/BRANCH_PROTECTION_RULES.md`
- **Covers**:
  - Rules for `main` and `develop` branches
  - Step-by-step setup instructions
  - Merge strategy recommendations
  - Code ownership configuration
  - Admin enforcement guidelines

### 4. Configuration Files
- `.gitignore` - Protects sensitive files and Python artifacts
- `.env.example` - Template for environment variables
- `.flake8` - Linting configuration
- `pytest.ini` - Testing configuration
- `pyproject.toml` - Project metadata and tool configurations
- `.github/CODEOWNERS` - Code ownership definitions
- `.github/pull_request_template.md` - PR submission template

---

## 🚀 Next Steps: Enable on GitHub

### Step 1: Push These Changes
```bash
git add .
git commit -m "feat: add open source infrastructure (CI/CD, contributing guides, branch protection)"
git push origin main
```

### Step 2: Create Main and Develop Branches (if not exists)
```bash
# If you only have master, rename it
git branch -m master main
git push -u origin main

# Create develop branch
git checkout -b develop
git push -u origin develop
```

### Step 3: Enable Branch Protection for `main`

1. Go to: **Settings** → **Branches**
2. Click **Add rule**
3. Configure as follows:

**Branch name pattern**: `main`

**Protect matching branches**:
- ✅ Require a pull request before merging
  - ✅ Require approvals: **1 or 2** (adjust as needed)
  - ✅ Dismiss stale pull request approvals
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date
  - Select these checks:
    - `lint-and-test (3.9)`
    - `lint-and-test (3.10)`
    - `lint-and-test (3.11)`
    - `security-check`
    - `code-quality`
    - `build-check`
- ✅ Require conversation resolution before merging
- ✅ Allow force pushes: **Disabled**
- ✅ Allow deletions: **Disabled**

### Step 4: Enable Branch Protection for `develop`

Repeat Step 3, but with these differences:

**Branch name pattern**: `develop`

**Reduce requirements slightly**:
- ✅ Require approvals: **1**
- Select checks:
  - `lint-and-test`
  - `security-check`

### Step 5: Update Code Owners

Edit `.github/CODEOWNERS` and replace `@YOUR_USERNAME` with actual GitHub usernames:

```bash
# Example:
* @alice @bob
/webhook/ @charlie
```

### Step 6: Configure GitHub Actions (if needed)

1. Go to: **Settings** → **Actions** → **General**
2. Allow actions and workflows to run
3. Set appropriate permissions for workflows

### Step 7: Enable PR Templates

The `.github/pull_request_template.md` will automatically appear when users open PRs.

To test: Create a test PR and verify the template appears.

### Step 8: Codecov Integration (Optional)

1. Visit [codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Select your repository
4. Get the access token
5. Add to **Settings** → **Secrets and variables** → **Actions**:
   - Key: `CODECOV_TOKEN`
   - Value: Your token

---

## 📋 Checklist for Open Source

- [ ] Created `.gitignore` with sensitive files protected
- [ ] Created `CONTRIBUTING.md` with clear guidelines
- [ ] Created CI/CD pipeline in `.github/workflows/ci.yml`
- [ ] Created branch protection rules documentation
- [ ] Set up `.github/CODEOWNERS` with maintainer names
- [ ] Updated `.github/pull_request_template.md`
- [ ] Pushed all changes to GitHub
- [ ] Enabled branch protection on **main** branch
- [ ] Enabled branch protection on **develop** branch
- [ ] Updated README with contribution section (optional but recommended):

```markdown
## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Start
1. Fork the repository
2. Create a feature branch (`feature/your-feature`)
3. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions.
```

---

## 🔐 Before Making It Public

### Security Checklist

- [ ] All API keys and secrets removed from Git history
- [ ] `.env.example` doesn't contain real credentials
- [ ] Firebase keys excluded in `.gitignore`
- [ ] No secrets in commit logs
- [ ] CI/CD pipeline set to fail on security issues

### Check for Exposed Secrets

```bash
# Install git-secrets or similar tool
brew install git-secrets  # macOS

# Run check
git secrets --scan
```

---

## 📖 Documentation to Add to README

Add this section to your `README.md`:

```markdown
## Development & Contributing

### Setup for Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup and contribution guidelines.

```bash
# Quick setup
git clone https://github.com/YOUR_USERNAME/zana.git
cd zana
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest  # Run tests
```

### Code Quality

- Tests must pass
- Code automatically formatted with black
- Type checking with mypy
- Linting with flake8

### CI/CD

All pull requests automatically run:
- Unit tests on Python 3.9, 3.10, 3.11
- Linting and code style checks
- Security scanning
- Code coverage analysis

See `.github/workflows/ci.yml` for details.

### Branch Protection

- `main` and `develop` branches are protected
- All PRs require review and passing tests
- See [BRANCH_PROTECTION_RULES.md](.github/BRANCH_PROTECTION_RULES.md)
```

---

## 🎯 Recommended Additional Steps

### 1. Create Issue Templates (Optional)

Create `.github/ISSUE_TEMPLATE/` with:
- `bug_report.md`
- `feature_request.md`
- `documentation.md`

### 2. Create GitHub Labels

Suggested labels for issues:
- `good first issue` - Easy tasks for first-time contributors
- `help wanted` - Need community help
- `bug` - Something is broken
- `enhancement` - New feature request
- `documentation` - Documentation improvement
- `security` - Security issues
- `blocked` - Blocked/waiting
- `priority: high/medium/low`

### 3. Create Release Process

Create a `RELEASE.md` or add to CONTRIBUTING.md with:
- Versioning strategy (semver recommended)
- Release checklist
- Changelog maintenance process

### 4. Set Up Wiki or Documentation Site

Consider:
- GitHub Wiki for user docs
- ReadTheDocs for API docs
- GitHub Pages for landing page

---

## 🆘 Troubleshooting

### CI/CD Failing

1. **Python version mismatch**: Ensure code supports Python 3.9+
2. **Import errors**: Install all dependencies in requirements.txt
3. **Test failures**: Run `pytest` locally first
4. **Type errors**: Run `mypy .` to check types

### Branch Protection Issues

- If you're an admin and need to bypass: Use with caution and document why
- Use "Dismiss stale approvals" if updating PR after reviews

### Secret Exposure

If you accidentally pushed secrets:
1. Revoke the exposed credentials immediately
2. Use `git filter-branch` or `git filter-repo` to remove from history
3. Force push (only you/admins should do this)

---

## 📞 Getting Help

For issues with:
- **GitHub setup**: GitHub Docs (https://docs.github.com)
- **Python testing**: pytest docs (https://docs.pytest.org)
- **GitHub Actions**: Actions documentation (https://docs.github.com/en/actions)

---

**Last Updated**: May 2026

**Status**: Ready for open-source contributions! 🎉
