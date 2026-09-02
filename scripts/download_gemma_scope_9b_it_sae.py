#!/usr/bin/env python3
"""Download the canonical GemmaScope Gemma-2-9B-it layer-9 SAE checkpoint."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.gemma_sae_steering import (
    DEFAULT_GEMMA_9B_SAE_PATH,
    GEMMA_SCOPE_9B_IT_SAE_URL,
)


def download(
    url: str,
    output: Path,
    *,
    force: bool = False,
    fallback_url: str | None = None,
) -> None:
    if output.exists() and output.stat().st_size > 0 and not force:
        print(f"Already present: {output}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "SafeLens GemmaScope downloader"})
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{output.name}.", suffix=".part", dir=output.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            try:
                with urlopen(request, timeout=60) as response:
                    while True:
                        chunk = response.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            except (OSError, TimeoutError):
                if not fallback_url:
                    raise
                print(f"Primary download failed; retrying mirror: {fallback_url}")
                handle.seek(0)
                handle.truncate()
                mirror_request = Request(
                    fallback_url,
                    headers={"User-Agent": "SafeLens GemmaScope downloader"},
                )
                with urlopen(mirror_request, timeout=60) as response:
                    while True:
                        chunk = response.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
            if temporary.stat().st_size == 0:
                raise RuntimeError("downloaded checkpoint is empty")
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Downloaded {output} ({output.stat().st_size / 1024**3:.2f} GiB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_GEMMA_9B_SAE_PATH))
    parser.add_argument("--url", default=GEMMA_SCOPE_9B_IT_SAE_URL)
    parser.add_argument(
        "--mirror-url",
        default=os.environ.get(
            "SAFELENS_HF_MIRROR_URL",
            GEMMA_SCOPE_9B_IT_SAE_URL.replace("https://huggingface.co", "https://hf-mirror.com"),
        ),
        help="Optional fallback URL used when the primary Hugging Face download is unavailable.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    download(
        args.url,
        args.output.expanduser(),
        force=args.force,
        fallback_url=args.mirror_url if args.mirror_url != args.url else None,
    )


if __name__ == "__main__":
    main()
