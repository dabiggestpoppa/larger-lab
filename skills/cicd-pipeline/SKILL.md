# CI/CD Pipeline Skill

## Purpose
Automate testing, building, and deployment of OCE and SRRA-OPH components using GitHub Actions and local tooling.

## When to Use
- Before merging any code changes
- Setting up automated testing for new components
- Deploying OCE to production/staging
- Running the full test suite locally

## GitHub Actions Workflows

### Main CI Workflow (`.github/workflows/ci.yml`)
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run SRRA-OPH tests
        run: |
          cd srrs_opc
          python -m pytest tests/ -v --cov=. --cov-report=xml

      - name: Run OCE tests
        run: |
          cd oce
          python -m pytest tests/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

### Deploy Workflow (`.github/workflows/deploy.yml`)
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker images
        run: docker compose build

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker compose push

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/oce
            docker compose pull
            docker compose up -d
```

## Local CI Commands

```bash
# Run all tests
python -m pytest srrs_opc/tests/ oce/tests/ -v

# Run with coverage
python -m pytest srrs_opc/tests/ --cov=srrs_opc --cov-report=html

# Run specific test file
python -m pytest srrs_opc/tests/test_phase9_e2e.py -v

# Lint code
python -m flake8 srrs_opc/ --max-line-length=120
python -m black srrs_opc/ --check

# Type checking
python -m mypy srrs_opc/ --ignore-missing-imports

# Full CI pipeline locally
python tools/ci-local.py
```

## Pre-Commit Hooks (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

## Setup
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```
