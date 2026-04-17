from __future__ import annotations

import csv
import json
from pathlib import Path

from official_packet_core import coverage_rows, group_summary, load_rows, seed_mean_summary
from official_release_writer import build_release_reports
from official_packet_review import replay_rows, review_payload


def build_packet(protocol_dir: Path, output_dir: Path, aggregate_dir: Path) -> dict[str, str]:
    rows = load_rows(output_dir)
    paths = output_paths(aggregate_dir)
    phase_rows = group_summary(rows, ("mode", "phase"))
    _write_csv(paths["summary"], seed_mean_summary(rows))
    _write_csv(paths["mode"], group_summary(rows, ("mode",)))
    _write_csv(paths["seed"], group_summary(rows, ("mode", "launch_seed")))
    _write_csv(paths["phase"], phase_rows)
    _write_csv(paths["coverage"], coverage_rows(rows))
    replay = replay_rows(rows)
    _write_csv(paths["replay"], replay)
    _write_json(paths["review"], review_payload(rows, phase_rows, paths["replay"]))
    report_paths = build_release_reports(
        protocol_dir=protocol_dir,
        aggregate_dir=aggregate_dir,
        reports_dir=output_report_dir(output_dir),
    )
    result = {name: str(path) for name, path in paths.items()}
    result.update(report_paths)
    return result


def output_paths(aggregate_dir: Path) -> dict[str, Path]:
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    return {
        "summary": aggregate_dir / "official_summary.csv",
        "mode": aggregate_dir / "official_mode_summary.csv",
        "seed": aggregate_dir / "official_seed_summary.csv",
        "phase": aggregate_dir / "official_phase_summary.csv",
        "coverage": aggregate_dir / "official_metric_coverage.csv",
        "replay": aggregate_dir / "official_replay_cases.csv",
        "review": aggregate_dir / "official_review.json",
    }


def output_report_dir(output_dir: Path) -> Path:
    return output_dir.parent / "reports" / "official_wave1"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    paths = build_packet(
        protocol_dir=root / "artifacts" / "protocols" / "official-wave1",
        output_dir=root / "artifacts" / "official_wave1",
        aggregate_dir=root / "artifacts" / "aggregate",
    )
    print(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
