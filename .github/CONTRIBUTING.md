# Contributing to Stairway to Salesforce
Thank you for your interest in contributing! We welcome all types of contributions: bug reports, feature requests, documentation improvements, or code changes.

---

## 1. Environment Setup

1. Fork and Clone the repository.
2. Run `make setup-dev`. This will setup the environment and install git hooks.
3. Verify your setup by running `make check-all`.


## 2. Development Workflow

### Code Quality & Style
We use **Ruff** via a standardized Makefile to maintain high code quality.

* **Format and Auto-fix**:
    ```bash
    make fix-style
    ```

* **Verify Everything (Style, Types and Tests)**:
    ```bash
    make check-all
    ```

* **Verify specific aspects**:
    ```bash
    make check-style
    make check-type
    make check-test
    ```

### Testing Requirements
No pull request will be merged without passing tests and maintaining coverage.

* **Run all tests**: `uv run pytest`
* **Check coverage** (Target: > 80%):
    ```bash
    make check-test
    ```

## 3. Pull Request Process

### Before Submitting
- [ ] Ensure all tests pass.
- [ ] Code is formatted and linted with `make fix-style`.
- [ ] Documentation is updated (if applicable).
- [ ] Type hints are used for all new functions.
- [ ] **Pathlib** is used for all file path manipulations instead of `os.path`.

### Commit Message Format
We follow a structured commit format: `<type>: <subject>`.
* `feat`: A new feature.
* `fix`: A bug fix.
* `docs`: Documentation changes.
* `test`: Adding or correcting tests.
* `refactor`: Code change that neither fixes a bug nor adds a feature.

### Submission Template
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

## 4. Documentation
If you add a new component or connector, you must document it.

1.  **Preview documentation** locally: `uv run mkdocs serve`.
2.  **Update API Reference**: Add your new class/function to `docs/api-reference.md`.


## 5. Reporting Issues & Feature Requests

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

## 6. Release & Docker Workflow

We use an automated pipeline to handle versioning and Docker image distribution. **Do not create manual git tags.**

### Versioning Policy

The version of the project is defined in 'pyproject.toml'. We follow Semantic Versioning.

### Automated Releases

The CI/CD pipeline (GitHub Actions) triggers a new build and release whenever a **GitHub Release** is published:

1. **Update version**: The maintainer updates the version in 'pyproject.toml' and merges to main.
2. **Create Release**: A new release is created via the GitHub UI with a tag (e.g., v0.1.2).
3. **Automated Build**: GitHub Actions automatically:

* Builds the Docker image using the multi-stage Dockerfile.
* Pushes the image to GitHub Container Registry (GHCR).
* Tags the image with both the version number and latest.

### Local Docker Testing

If you need to test the Docker build locally before submitting a PR:

```bash
# Build the image
make docker-build

# Run a quick check
make docker-run
```

## 7. Code of Conduct
We are committed to providing a welcoming and inclusive environment. Please be respectful and considerate in all interactions.

## 8. License
By contributing, you agree that your contributions will be licensed under the same MIT License as the project.
