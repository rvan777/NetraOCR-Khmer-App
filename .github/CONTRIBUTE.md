# Contributing to Netra Khmer OCR Desktop

We follow the **GitFlow** workflow to ensure stable, predictable releases.

## 🌿 Branching Strategy

- **`main`**: Production-ready code only. Never commit directly here.
- **`develop`**: Integration branch for features. All PRs target this branch.
- **`feature/*`**: New features (e.g., `feature/add-batch-processing`). Branch off `develop`.
- **`release/*`**: Preparation for a new production release (e.g., `release/v1.1.0`). Branch off `develop`, merge into
  both `main` and `develop`.
- **`hotfix/*`**: Urgent fixes to production (e.g., `hotfix/crash-on-pdf`). Branch off `main`, merge into both `main`
  and `develop`.

## 🛠️ Development Setup

1. Fork the repository and clone your fork.
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## ✅ Pull Request Guidelines

- Ensure code passes `pytest` (if applicable) and is formatted with `black`.
- Update `README.md` if you add new features or change setup steps.
- Request review from at least one maintainer.

## 🏷️ Commit Message Convention

Use conventional commits:

- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `chore:` Changes to the build process or auxiliary tools