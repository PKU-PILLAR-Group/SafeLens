from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

WORKERS = (
    "build_local_explorer_real_run.py",
    "run_local_explorer_attribution.py",
    "run_local_explorer_nla.py",
    "run_local_explorer_patching.py",
    "run_local_explorer_intervention.py",
)
ASSET_ROOT = "SafeLens/explorer_web/assets/"
ASSET_REFERENCE = re.compile(r"[A-Za-z0-9_.-]+\.(?:css|js)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify that a SafeLens wheel contains a runnable Explorer."
    )
    parser.add_argument("wheel", nargs="?", type=Path)
    args = parser.parse_args()
    wheel = args.wheel or _single_wheel(Path("dist"))

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {
            "SafeLens/explorer_web/index.html",
            *(f"SafeLens/explorer_workers/{name}" for name in WORKERS),
        }
        missing = sorted(required - names)
        if missing:
            raise SystemExit(f"Wheel is missing Explorer resources: {', '.join(missing)}")
        assets = [
            name for name in names if name.startswith(ASSET_ROOT) and name.endswith((".css", ".js"))
        ]
        if not any(name.endswith(".css") for name in assets):
            raise SystemExit("Wheel is missing the Explorer CSS bundle")
        if not any(name.endswith(".js") for name in assets):
            raise SystemExit("Wheel is missing the Explorer JavaScript bundle")
        unreachable = sorted(set(assets) - _reachable_assets(archive, assets))
        if unreachable:
            stale = ", ".join(Path(name).name for name in unreachable)
            raise SystemExit(f"Wheel contains unreferenced Explorer assets: {stale}")
        entry_points = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(entry_points) != 1:
            raise SystemExit("Wheel must contain exactly one entry_points.txt")
        entry_point_text = archive.read(entry_points[0]).decode("utf-8")
        for command in ("safelens =", "safelens-explorer ="):
            if command not in entry_point_text:
                raise SystemExit(f"Wheel entry points are missing {command.rstrip(' =')}")

    print(f"Verified packaged Explorer in {wheel} ({len(assets)} CSS/JS assets)")


def _reachable_assets(archive: zipfile.ZipFile, assets: list[str]) -> set[str]:
    by_basename = {Path(name).name: name for name in assets}
    pending = ["SafeLens/explorer_web/index.html"]
    visited: set[str] = set()
    reachable: set[str] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        content = archive.read(current).decode("utf-8")
        for basename in ASSET_REFERENCE.findall(content):
            asset = by_basename.get(basename)
            if asset is None or asset in reachable:
                continue
            reachable.add(asset)
            pending.append(asset)
    return reachable


def _single_wheel(dist: Path) -> Path:
    wheels = sorted(dist.glob("safelens-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected exactly one SafeLens wheel in {dist}, found {len(wheels)}")
    return wheels[0]


if __name__ == "__main__":
    main()
