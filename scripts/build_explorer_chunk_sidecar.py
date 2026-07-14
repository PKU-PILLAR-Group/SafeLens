from __future__ import annotations

import argparse
from pathlib import Path

from SafeLens.explorer_chunks import build_explorer_sidecar


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build immutable physical chunks and an atomic Explorer sidecar manifest."
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--block-size", type=int, default=512)
    args = parser.parse_args()
    manifest = build_explorer_sidecar(args.artifact, block_size=args.block_size)
    print(manifest)


if __name__ == "__main__":
    main()
