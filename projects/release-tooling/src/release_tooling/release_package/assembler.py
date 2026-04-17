"""Top-level release assembly orchestration."""

from __future__ import annotations

from release_tooling.release_package.biome_audit import build_biome_audit
from release_tooling.release_package.comparison_table import COMPARISON_FIELDS, build_comparison_rows
from release_tooling.release_package.control_checks import build_control_checks
from release_tooling.release_package.discovery import discover_runs
from release_tooling.release_package.file_writers import write_csv, write_json, write_text
from release_tooling.release_package.load_rows import load_episode_rows
from release_tooling.release_package.report_builder import build_report
from release_tooling.release_package.request import ReleaseRequest
from release_tooling.release_package.result import AssemblyResult
from release_tooling.release_package.summary_table import SUMMARY_FIELDS, build_summary_rows
from release_tooling.release_package.verdict_builder import build_official_verdict


def assemble_release(request: ReleaseRequest) -> AssemblyResult:
    runs = discover_runs(request.input_roots)
    rows = load_episode_rows(runs)
    summary_rows = build_summary_rows(rows)
    comparison_rows = build_comparison_rows(summary_rows)
    biome_audit = build_biome_audit(rows)
    control_checks = build_control_checks(summary_rows)
    output_paths = build_output_paths(request)
    write_outputs(request, output_paths, summary_rows, comparison_rows, biome_audit, control_checks)
    return AssemblyResult(
        release_table_path=output_paths["release_table"],
        release_comparisons_path=output_paths["release_comparisons"],
        biome_audit_path=output_paths["biome_audit"],
        official_verdict_path=output_paths["official_verdict"],
        report_path=output_paths["report"],
        run_count=len(summary_rows),
        episode_count=len(rows),
    )


def build_output_paths(request: ReleaseRequest) -> dict[str, object]:
    root = request.output_root / request.package_name
    return {
        "release_table": root / "release_table.csv",
        "release_comparisons": root / "release_comparisons.csv",
        "biome_audit": root / "biome_audit.json",
        "official_verdict": root / "official_verdict.md",
        "report": root / "report.md",
    }


def write_outputs(
    request: ReleaseRequest,
    output_paths: dict[str, object],
    summary_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
    biome_audit: dict[str, object],
    control_checks: dict[str, bool],
) -> None:
    write_csv(output_paths["release_table"], summary_rows, SUMMARY_FIELDS)
    write_csv(output_paths["release_comparisons"], comparison_rows, COMPARISON_FIELDS)
    write_json(output_paths["biome_audit"], biome_audit)
    write_text(
        output_paths["official_verdict"],
        build_official_verdict(request, summary_rows, comparison_rows, biome_audit, control_checks),
    )
    write_text(
        output_paths["report"],
        build_report(request, summary_rows, comparison_rows, biome_audit, control_checks),
    )
