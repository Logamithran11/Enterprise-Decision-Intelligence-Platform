# Developer Guide

Welcome to the Developer Guide for the Enterprise Decision Intelligence Platform.

## Coding Style & Standards
- Python files must adhere to PEP-8 and utilize type hints. We enforce formatting via `Ruff` and type checking via `MyPy`.
- Frontend code must use React, TypeScript, and Tailwind CSS. Avoid unused variables or type casting to satisfy `verbatimModuleSyntax`.

## Local Setup
1. Setup Python Virtual Environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e "./backend[ml,dev]"
   ```
2. Generate synthetic enterprise datasets:
   ```bash
   python run_pipeline.py
   ```
3. Run model training:
   ```bash
   python run_training.py
   ```
4. Start backend API dev server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
5. Install and run frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Test Suite Execution
Run tests from the root directory:
```bash
$env:PYTHONPATH="backend"
.venv\Scripts\python -m pytest
```
All pull requests must pass local regression tests and GitHub Actions CI.
