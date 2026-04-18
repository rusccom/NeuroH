"""report.md builder."""

from __future__ import annotations

from collections import Counter

from release_tooling.release_package.pathology_flags import full_observation_pathology
from release_tooling.release_package.request import ReleaseRequest

KEY_METRICS = {
    "survival_steps_mean",
    "steps_to_first_needed_resource_mean",
    "return_steps_to_seen_resource_mean",
    "post_relocation_life_mean",
    "relocation_recovery_success_rate",
    "relocation_recovery_steps_mean",
    "mean_energy_deficit",
    "mean_water_deficit",
}


def build_report(
    request: ReleaseRequest,
    summary_rows: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    biome_audit: dict[str, object],
    control_checks: dict[str, bool],
) -> str:
    lines = [
        "# report",
        "",
        "## Architecture Overview",
        "- Release assembly runs outside frozen rc3 and reads artifact roots in read-only mode.",
        "- Truth source is `episode_summaries.jsonl`; summary tables are derived from per-episode rows, not from prior aggregates.",
        "",
        "## Experimental Protocol",
        *protocol_lines(request, summary_rows),
        "",
        "## Results",
        *result_lines(summary_rows),
        "",
        "## Comparisons",
        *comparison_lines(comparisons),
        "",
        "## Discussion",
        *discussion_lines(summary_rows, biome_audit, control_checks),
        "",
        "## What Transfers To v2",
        "- Release assembly remains external to experiment code.",
        "- Split-phase lineage and control checks remain reusable as release discipline.",
        "- `_pick_biome` stays documented as the first baseline investigation item for v2.",
    ]
    return "\n".join(lines)


def protocol_lines(
    request: ReleaseRequest,
    summary_rows: list[dict[str, object]],
) -> list[str]:
    counts = Counter(str(row["phase"]) for row in summary_rows)
    bundles = Counter(str(row["input_name"]) for row in summary_rows)
    return [
        f"- package: `{request.package_name}`",
        f"- baseline: `{request.baseline_tag}` @ `{request.baseline_commit}`",
        f"- input roots: {', '.join(f'`{path}`' for path in request.input_roots)}",
        f"- assembled runs: `{len(summary_rows)}`",
        f"- bundle coverage: {', '.join(f'`{name}:{bundles[name]}`' for name in sorted(bundles))}",
        f"- phase coverage: {', '.join(f'`{phase}:{counts[phase]}`' for phase in sorted(counts))}",
    ]


def result_lines(summary_rows: list[dict[str, object]]) -> list[str]:
    lines = [summary_table_header(), summary_table_rule()]
    lines.extend(summary_table_row(row) for row in summary_rows)
    return lines


def summary_table_header() -> str:
    return "| input | run_id | mode | phase | seed | episodes | biome | survival | recovery | slow | fast |"


def summary_table_rule() -> str:
    return "| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |"


def summary_table_row(row: dict[str, object]) -> str:
    return (
        f"| {row['input_name']} | {row['run_id']} | {row['mode']} | {row['phase']} | {row['seed']} | {row['episode_count']} | "
        f"{row['biome_distribution']} | {format_value(row['survival_steps_mean'])} | "
        f"{format_value(row['relocation_recovery_success_rate'])} | {format_value(row['source_slow_share'])} | "
        f"{format_value(row['source_fast_share'])} |"
    )


def comparison_lines(comparisons: list[dict[str, object]]) -> list[str]:
    if not comparisons:
        return ["- No `full` vs ablation comparisons were available."]
    lines = [comparison_table_header(), comparison_table_rule()]
    decisive = filtered_comparisons(comparisons)
    lines.extend(comparison_table_row(row) for row in decisive)
    return lines if len(lines) > 2 else ["- No decisive comparisons were available."]


def filtered_comparisons(comparisons: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [row for row in comparisons if row["preferred_mode"] is not None]
    return [row for row in rows if str(row["metric"]) in KEY_METRICS]


def comparison_table_header() -> str:
    return "| input | phase | compared | metric | preferred | delta | significance |"


def comparison_table_rule() -> str:
    return "| --- | --- | --- | --- | --- | ---: | --- |"


def comparison_table_row(row: dict[str, object]) -> str:
    return (
        f"| {row['input_name']} | {row['phase']} | {row['compared_mode']} | {row['metric']} | {row['preferred_mode']} | "
        f"{format_value(row['delta'])} | {row['significance']} |"
    )


def discussion_lines(
    summary_rows: list[dict[str, object]],
    biome_audit: dict[str, object],
    control_checks: dict[str, bool],
) -> list[str]:
    biome_summary = ", ".join(
        f"`{key}:{value}`" for key, value in biome_audit["total_counts"].items()
    )
    lines = [
        f"- biome audit total: {biome_summary}",
        f"- single biome only: `{biome_audit['single_biome_only']}`",
        f"- control checks: {', '.join(f'`{key}={value}`' for key, value in control_checks.items())}",
    ]
    pathology = full_observation_pathology(summary_rows)
    if pathology is not None:
        lines.append(
            "- `full_observation` remained pathological in the assembled package: "
            "missing `steps_to_first_needed_resource_mean`, zero relocation recovery, and lower relocation survival."
        )
    return lines


def format_value(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
