#!/usr/bin/env python3
"""Run one local GemmaScope steering comparison from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.gemma_sae_steering import SAEFeature, steer_gemma_prompt  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument(
        "--feature",
        action="append",
        default=[],
        metavar="INDEX:STRENGTH",
        help="SAE feature and decoder coefficient; repeat for multiple features",
    )
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    features: list[SAEFeature] = []
    for value in args.feature:
        try:
            index, strength = value.split(":", maxsplit=1)
            features.append(SAEFeature(int(index), float(strength)))
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"Invalid --feature {value!r}; expected INDEX:STRENGTH") from exc
    result = steer_gemma_prompt(
        args.prompt,
        features,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        seed=args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
