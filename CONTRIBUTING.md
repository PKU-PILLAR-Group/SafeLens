# Contributing to SafeLens

SafeLens is a research-oriented infrastructure project for LLM safety probing,
monitoring, attribution, model adaptation, and downstream report conversion.
Contributions should keep the public interfaces stable, dependency boundaries
clear, and tests lightweight enough for CI.

## Development Setup

Use Python 3.10 or newer.

```bash
conda create -p ./.conda python=3.10 -y
conda run -p ./.conda python -m pip install -r requirements-dev.txt
conda run -p ./.conda python -m pip install -e . --no-build-isolation
```

Run the standard checks before opening a pull request:

```bash
conda run -p ./.conda pre-commit run --all-files
conda run -p ./.conda pytest
conda run -p ./.conda mkdocs build --strict
```

## Contribution Workflow

1. Create a focused branch from `main`.
2. Keep changes scoped to one feature, bug fix, or documentation update.
3. Add or update tests when changing behavior.
4. Update documentation when changing public APIs, config fields, model
   support, or CLI behavior.
5. Open a pull request using the repository PR template.

## Adding Methods

New probes, monitors, and attributors should follow the abstract interfaces in
`src/SafeLens/core/base.py` and register themselves through
`src/SafeLens/core/registry.py`.

For a new method, include:

- A small implementation module under `src/SafeLens/probes`,
  `src/SafeLens/monitors`, or `src/SafeLens/attribution`.
- A registration name that is stable and documented.
- Unit tests that avoid network access and large model downloads.
- A short example or documentation snippet when the method is user-facing.

## Adding Model Adapters

Model adapters should implement the `ModelWrapper` contract and clearly declare
which activation names and patching operations are supported. Unit tests should
use mocks, dummy modules, or tiny local objects unless an integration test is
explicitly marked as slow.

Do not commit model weights, tokenizer artifacts, private datasets, API tokens,
or generated experiment outputs.

## Code Style

SafeLens uses Ruff for linting and formatting, mypy for type checking, pytest
for tests, and MkDocs for documentation. Prefer small modules, explicit data
models, and clear error messages over implicit behavior.

## Documentation Style

Documentation should explain the public contract first, then give a minimal
example. Keep implementation notes separate from user-facing API guidance.
