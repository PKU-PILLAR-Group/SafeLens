from __future__ import annotations

import json
from pathlib import Path

from SafeLens.config import run_report_json_schema


def test_run_report_schema_matches_golden_file() -> None:
    golden = json.loads(Path("schemas/run-report.schema.json").read_text(encoding="utf-8"))

    assert run_report_json_schema() == golden
