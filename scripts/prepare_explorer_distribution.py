from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_APP = ROOT / "apps" / "local_explorer"
WEB_DIST = WEB_APP / "dist"
PACKAGE_ROOT = ROOT / "src" / "SafeLens"
PACKAGE_WEB = PACKAGE_ROOT / "explorer_web"
PACKAGE_WORKERS = PACKAGE_ROOT / "explorer_workers"
BUILD_PACKAGE_ROOT = ROOT / "build" / "lib" / "SafeLens"
WORKERS = (
    "build_local_explorer_real_run.py",
    "run_local_explorer_attribution.py",
    "run_local_explorer_nla.py",
    "run_local_explorer_jlens.py",
    "run_local_explorer_patching.py",
    "run_local_explorer_intervention.py",
    "run_local_explorer_sae_discovery.py",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and stage SafeLens Explorer resources for Python packaging."
    )
    parser.add_argument(
        "--skip-web-build",
        action="store_true",
        help="Reuse apps/local_explorer/dist instead of invoking npm run build.",
    )
    args = parser.parse_args()

    if not args.skip_web_build:
        subprocess.run(["npm", "run", "build"], cwd=WEB_APP, check=True)
    _validate_web_dist()

    shutil.rmtree(PACKAGE_WEB, ignore_errors=True)
    shutil.copytree(WEB_DIST, PACKAGE_WEB)
    PACKAGE_WORKERS.mkdir(parents=True, exist_ok=True)
    for stale in PACKAGE_WORKERS.glob("*.py"):
        stale.unlink()
    for name in WORKERS:
        source = ROOT / "scripts" / name
        if not source.is_file():
            raise FileNotFoundError(f"Explorer worker is missing: {source}")
        shutil.copy2(source, PACKAGE_WORKERS / name)
    _clear_stale_build_cache()

    asset_count = sum(1 for path in (PACKAGE_WEB / "assets").rglob("*") if path.is_file())
    print(f"Staged Explorer web bundle ({asset_count} assets) in {PACKAGE_WEB}")
    print(f"Staged {len(WORKERS)} Explorer workers in {PACKAGE_WORKERS}")


def _validate_web_dist() -> None:
    if not (WEB_DIST / "index.html").is_file():
        raise FileNotFoundError(
            f"Explorer build is missing {WEB_DIST / 'index.html'}. Run without --skip-web-build."
        )
    assets = WEB_DIST / "assets"
    if not assets.is_dir() or not any(path.is_file() for path in assets.rglob("*")):
        raise FileNotFoundError(f"Explorer build has no static assets in {assets}")


def _clear_stale_build_cache() -> None:
    for relative in ("explorer_web", "explorer_workers"):
        shutil.rmtree(BUILD_PACKAGE_ROOT / relative, ignore_errors=True)


if __name__ == "__main__":
    main()
