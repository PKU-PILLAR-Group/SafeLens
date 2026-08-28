from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

WORKERS = (
    "build_local_explorer_real_run.py",
    "run_local_explorer_attribution.py",
    "run_local_explorer_nla.py",
    "run_local_explorer_jlens.py",
    "run_local_explorer_patching.py",
    "run_local_explorer_intervention.py",
    "run_local_explorer_sae_discovery.py",
)


def test_explorer_wheel_verifier_accepts_reachable_assets(tmp_path: Path) -> None:
    wheel = _write_wheel(tmp_path, include_stale=False)

    result = _verify(wheel)

    assert result.returncode == 0, result.stderr
    assert "2 CSS/JS assets" in result.stdout


def test_explorer_wheel_verifier_rejects_unreferenced_assets(tmp_path: Path) -> None:
    wheel = _write_wheel(tmp_path, include_stale=True)

    result = _verify(wheel)

    assert result.returncode == 1
    assert "unreferenced Explorer assets: stale-old-hash.js" in result.stderr


def _write_wheel(tmp_path: Path, *, include_stale: bool) -> Path:
    wheel = tmp_path / "safelens-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "SafeLens/explorer_web/index.html",
            '<link href="./assets/app.css"><script src="./assets/app.js"></script>',
        )
        archive.writestr("SafeLens/explorer_web/assets/app.css", "body { color: black; }")
        archive.writestr("SafeLens/explorer_web/assets/app.js", "console.log('ready')")
        if include_stale:
            archive.writestr("SafeLens/explorer_web/assets/stale-old-hash.js", "")
        for worker in WORKERS:
            archive.writestr(f"SafeLens/explorer_workers/{worker}", "")
        archive.writestr(
            "safelens-0.1.0.dist-info/entry_points.txt",
            "[console_scripts]\nsafelens = SafeLens.cli:main\n"
            "safelens-explorer = SafeLens.explorer_api:main\n",
        )
    return wheel


def _verify(wheel: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/verify_explorer_wheel.py", str(wheel)],
        check=False,
        capture_output=True,
        text=True,
    )
