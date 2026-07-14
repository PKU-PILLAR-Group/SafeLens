from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

WORKERS = (
    "build_local_explorer_real_run.py",
    "run_local_explorer_attribution.py",
    "run_local_explorer_nla.py",
    "run_local_explorer_patching.py",
    "run_local_explorer_intervention.py",
)


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
            name
            for name in names
            if name.startswith("SafeLens/explorer_web/assets/") and name.endswith((".css", ".js"))
        ]
        if not any(name.endswith(".css") for name in assets):
            raise SystemExit("Wheel is missing the Explorer CSS bundle")
        if not any(name.endswith(".js") for name in assets):
            raise SystemExit("Wheel is missing the Explorer JavaScript bundle")
        entry_points = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(entry_points) != 1:
            raise SystemExit("Wheel must contain exactly one entry_points.txt")
        entry_point_text = archive.read(entry_points[0]).decode("utf-8")
        for command in ("safelens =", "safelens-explorer ="):
            if command not in entry_point_text:
                raise SystemExit(f"Wheel entry points are missing {command.rstrip(' =')}")

    print(f"Verified packaged Explorer in {wheel} ({len(assets)} CSS/JS assets)")


def _single_wheel(dist: Path) -> Path:
    wheels = sorted(dist.glob("safelens-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected exactly one SafeLens wheel in {dist}, found {len(wheels)}")
    return wheels[0]


if __name__ == "__main__":
    main()
