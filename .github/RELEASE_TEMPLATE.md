# SafeLens vX.Y.Z

## Highlights

-

## What's Changed

-

## Compatibility

- Python: 3.10, 3.11, 3.12
- Package extras: `models`, `modelscope`, `dev`

## Installation

```bash
python -m pip install safelens
```

## Verification

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m mkdocs build --strict
```

## Notes

- Do not attach model weights, private datasets, API tokens, or generated safety reports to public releases.
