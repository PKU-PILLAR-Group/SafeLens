"""Run the built-in dummy pipeline from Python."""

from __future__ import annotations

from pathlib import Path

from SafeLens.pipelines import run_from_config


def main() -> None:
    config_path = Path(__file__).with_name("config.yaml")
    report = run_from_config(config_path)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
