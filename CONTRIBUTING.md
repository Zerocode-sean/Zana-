# Contributing to Zana

Thank you for your interest in contributing to Zana! We welcome contributions from the community, whether it's bug fixes, new features, documentation improvements, or general feedback.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

- Be respectful and inclusive
- Welcome diverse perspectives and experiences
- Focus on constructive feedback
- Report inappropriate behavior to the maintainers

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Push to your fork
6. Open a pull request

## Development Setup

### Prerequisites
- Python 3.9 or higher
- pip or poetry
- Git

### Installation

1. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/zana.git
cd zana
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your local configuration
```

5. Run tests to verify setup:
```bash
pytest
```

## Making Changes

### Branch Naming
Use clear, descriptive branch names following this pattern:

- `feature/description` - for new features
- `fix/description` - for bug fixes
- `docs/description` - for documentation updates
- `refactor/description` - for code refactoring
- `test/description` - for test additions/improvements

Example: `feature/add-appointment-rescheduling`

### Code Changes

1. Keep changes focused and atomic
2. Write clear commit messages (see [Commit Guidelines](#commit-guidelines))
3. Add or update tests for your changes
4. Update documentation if needed
5. Run tests locally before pushing
6. Ensure your code follows our style guidelines

## Commit Guidelines

### Commit Message Format

Use clear, descriptive commit messages:

```
Short summary (50 characters or less)

More detailed explanation if needed, wrapped at 72 characters.
Explain what the change does and why it's needed.

Fixes #123 (if applicable)
```

### Examples
- ✅ `Add appointment rescheduling via WhatsApp`
- ✅ `Fix timezone handling in reminder scheduling`
- ✅ `Update documentation for webhook setup`
- ❌ `fix stuff`
- ❌ `update`

### Conventional Commits (Optional but Appreciated)

Consider using conventional commit format:
```
type(scope): subject

body
footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(tools): add appointment validation

Add comprehensive validation for appointment data before
booking to prevent invalid states in the database.

Fixes #456
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass locally:
```bash
pytest
```

2. Check code style:
```bash
# If using linting tools
black --check .
flake8 .
```

3. Update relevant documentation
4. Add tests for new functionality
5. Rebase on latest `main` branch

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Breaking change

## Related Issues
Closes #123

## Testing
- [ ] Added tests
- [ ] All tests pass locally
- [ ] Tested locally with provided steps

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added/updated
- [ ] Ready for review
```

### Review Process

1. At least one maintainer review required
2. CI/CD pipeline must pass
3. All conversations resolved
4. No merge conflicts
5. Commits kept clean (squash if needed)

## Testing Requirements

### Test Expectations

- New features must include tests
- Bug fixes should include a test that reproduces the issue
- Minimum test coverage: 70%
- All tests must pass before merging

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py

# Run specific test
pytest tests/test_orchestrator.py::test_function_name
```

## Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these considerations:

- Line length: 100 characters (soft limit, 120 hard limit)
- Use type hints for function signatures
- Docstrings for all public functions/classes
- Snake_case for variables and functions
- PascalCase for classes

### Example

```python
def process_appointment(
    appointment_id: str,
    clinic_id: str,
) -> dict[str, Any]:
    """
    Process appointment state machine.
    
    Args:
        appointment_id: Unique appointment identifier
        clinic_id: Associated clinic identifier
    
    Returns:
        Updated appointment state
    
    Raises:
        ValueError: If appointment not found
    """
    # Implementation
    return {}
```

### Recommended Tools

- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `isort` - Import sorting

## Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Example usage (if applicable)
- Related issues or discussions

### Security Issues

**Do not** open a public issue for security vulnerabilities. Please email security concerns to the maintainers privately.

## Questions?

- Check existing issues and discussions
- Open a new discussion for questions
- Join our community chat [if available]

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to Zana! 🙏

---

**Last Updated:** May 2026
