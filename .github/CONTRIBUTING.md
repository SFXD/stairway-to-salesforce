# Contributing to Stairway to Salesforce

Thank you for your interest in contributing! We welcome all types of contributions: bug reports, feature requests, documentation improvements, or code changes.

---

## 🚀 Getting Started

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/stairway-to-salesforce.git
    cd stairway-to-salesforce
    ```
3.  **Set up the development environment** using **uv**:
    ```bash
    pip install uv
    uv sync --all-groups
    ```
4.  **Create a feature branch**: `git checkout -b feat/your-feature-name`.

---

## 🛠 Development Workflow

### Code Quality & Style
We use **Ruff** to maintain high code quality. It replaces Black, Isort, Flake8, and Bandit.

* **Format and Lint**:
    ```bash
    uv run ruff format .
    uv run ruff check --fix .
    ```
* **Type Checking**:
    ```bash
    uv run mypy .
    ```

### Testing Requirements
No pull request will be merged without passing tests and maintaining coverage.

* **Run all tests**: `uv run pytest`
* **Check coverage** (Target: > 80%):
    ```bash
    uv run pytest --cov=stairway_to_salesforce --cov-report=term
    ```

---

## 📝 Pull Request Process

### 1. Before Submitting
- [ ] Ensure all tests pass.
- [ ] Code is formatted and linted with `ruff`.
- [ ] Documentation is updated (if applicable).
- [ ] Type hints are used for all new functions.
- [ ] **Pathlib** is used for all file path manipulations instead of `os.path`.

### 2. Commit Message Format
We follow a structured commit format: `<type>: <subject>`.
* `feat`: A new feature.
* `fix`: A bug fix.
* `docs`: Documentation changes.
* `test`: Adding or correcting tests.
* `refactor`: Code change that neither fixes a bug nor adds a feature.

### 3. Submission Template
When opening a PR, please use the following structure:

```markdown
## Description
*Explain the changes and the problem they solve.*

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation only

## Quality Check
- [ ] Unit tests passed
- [ ] Pipeline integration tests passed
- [ ] Ruff linting OK
```

---

## 📖 Documentation
If you add a new component or connector, you must document it.

1.  **Preview documentation** locally: `uv run mkdocs serve`.
2.  **Update API Reference**: Add your new class/function to `docs/api-reference.md`.

---

## 🐛 Reporting Issues & Feature Requests

We use GitHub Issue Forms to ensure we have all the necessary information to help you.

### Report a Bug
If you find a bug, please open a **[Bug Report](https://github.com/SFXD/stairway-to-salesforce/issues/new?template=bug_report.yml)**.
* Provide clear reproduction steps.
* Include environment details (Python version, OS, dlt version).
* Attach relevant logs or screenshots.

### Request a Feature
Have a great idea? Submit a **[Feature Request](https://github.com/SFXD/stairway-to-salesforce/issues/new?template=feature_request.yml)**.
* Describe the problem this feature solves.
* Explain your proposed solution and specific use cases.

---

## Code of Conduct
We are committed to providing a welcoming and inclusive environment. Please be respectful and considerate in all interactions.

## License
By contributing, you agree that your contributions will be licensed under the same MIT License as the project.