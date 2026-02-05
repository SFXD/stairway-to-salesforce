
# Making stairway-to-salesforce Open-Source Ready

Based on the repository review, here's a comprehensive set of boilerplate files and configurations to make your Salesforce ETL framework production-ready [^1].

---

## 1. Contributing Guidelines

Create `.github/CONTRIBUTING.md`:

```markdown
# Contributing to Stairway to Salesforce

Thank you for your interest in contributing! This document provides guidelines for contributing to this Salesforce ETL framework.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/stairway-to-salesforce.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up your development environment (see Installation in README)

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Run tests
pytest tests/
```

## How to Contribute

### Reporting Bugs
- Use the Bug Report issue template
- Include Python version, OS, and Salesforce API version
- Provide minimal reproducible example

### Suggesting Enhancements
- Use the Feature Request template
- Clearly describe the use case
- Explain why this would be useful

### Pull Requests
1. Ensure tests pass: `pytest tests/`
2. Add tests for new functionality
3. Update documentation as needed
4. Follow PEP 8 style guidelines
5. Write clear commit messages

**Commit Message Format:**
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Example:
```
feat: add support for Salesforce composite API

Implements composite API support for bulk operations
Reduces API call count by batching requests

Closes #123
```

## Code Style

- Follow PEP 8
- Use type hints where applicable
- Maximum line length: 100 characters
- Use meaningful variable names

## Testing

- Write unit tests for new features
- Maintain test coverage above 80%
- Test with multiple Salesforce API versions

## Questions?

Open a Discussion or reach out to maintainers.