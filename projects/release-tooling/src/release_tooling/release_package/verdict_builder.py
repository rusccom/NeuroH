"""official_verdict.md builder."""

from __future__ import annotations

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


def build_official_verdict(
    request: ReleaseRequest,
    summary_rows: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    biome_audit: dict[str, object],
    control_checks: dict[str, bool],
) -> str:
    lines = [
        "# official_verdict",
        "",
        "## Baseline Statement",
        baseline_statement(request, summary_rows),
        "",
        "## Key Findings",
        *key_findings(comparisons),
        "",
        "## Control Checks",
        *control_lines(control_checks),
        "",
        "## Known Limitations",
        *limitation_lines(summary_rows, biome_audit),
        "",
        "## Verdict",
        verdict_line(control_checks),
    ]
    return "\n".join(lines)


def baseline_statement(request: ReleaseRequest, summary_rows: list[dict[str, object]]) -> str:
    configs = sorted({str(row["config_hash"]) for row in summary_rows})
    return (
        f"- tag `{request.baseline_tag}`, commit `{request.baseline_commit}`, "
        f"config hashes: {', '.join(f'`{item}`' for item in configs)}"
    )


def key_findings(comparisons: list[dict[str, object]]) -> list[str]:
    selected = filtered_findings(comparisons)
    if not selected:
        return ["- No `full` vs ablation comparisons were available."]
    if not comparisons:
        return ["- No `full` vs ablation comparisons were available."]
    lines = [markdown_table_header(), markdown_table_rule()]
    lines.extend(markdown_table_row(row) for row in selected)
    return lines if len(lines) > 2 else ["- No decisive `full` vs ablation deltas were available."]


def filtered_findings(comparisons: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [row for row in comparisons if row["preferred_mode"] is not None]
    return [row for row in rows if str(row["metric"]) in KEY_METRICS]


def markdown_table_header() -> str:
    return "| input | phase | compared | metric | preferred | full | compared | delta |"


def markdown_table_rule() -> str:
    return "| --- | --- | --- | --- | --- | ---: | ---: | ---: |"


def markdown_table_row(row: dict[str, object]) -> str:
    return (
        f"| {row['input_name']} | {row['phase']} | {row['compared_mode']} | {row['metric']} | {row['preferred_mode']} | "
        f"{format_value(row['baseline_value'])} | {format_value(row['compared_value'])} | {format_value(row['delta'])} |"
    )


def control_lines(control_checks: dict[str, bool]) -> list[str]:
    return [f"- `{key}`: `{value}`" for key, value in control_checks.items()]


def limitation_lines(
    summary_rows: list[dict[str, object]],
    biome_audit: dict[str, object],
) -> list[str]:
    lines = biome_limitation_lines(biome_audit)
    lines.extend(full_observation_lines(summary_rows))
    return lines


def biome_limitation_lines(biome_audit: dict[str, object]) -> list[str]:
    if not biome_audit["single_biome_only"]:
        return ["- Biome audit found more than one biome in the assembled package."]
    biome_id = biome_audit["single_biome_id"]
    return [
        (
            "- Wave 1 and assembled follow-up runs operated exclusively on "
            f"`BiomeId.{biome_id}` due to a defect in `_pick_biome` "
            "(numpy random choice interaction with str-Enum types)."
        ),
        (
            "- Current effects remain valid as within-biome comparisons. "
            "Biome generalization is not demonstrated here and is scheduled for v2-rc4."
        ),
    ]


def full_observation_lines(summary_rows: list[dict[str, object]]) -> list[str]:
    pathology = full_observation_pathology(summary_rows)
    if pathology is None:
        return []
    return [
        (
            "- `full_observation` in "
            f"`{pathology['input_name']}` showed a pathological pattern: "
            "`steps_to_first_needed_resource_mean` stayed missing across phases, "
            "`relocation_recovery_success_rate` stayed `0.0`, and relocation survival was worse than `full`."
        ),
        (
            "- Root cause was not investigated inside frozen rc3. Candidate causes include "
            "metric events not firing when resources are visible from t=0, exploration/visibility interactions, "
            "or stale belief-map state after relocation. This is scheduled for v2-rc4 alongside `_pick_biome`."
        ),
    ]


def verdict_line(control_checks: dict[str, bool]) -> str:
    if all(control_checks.values()):
        return "- GO for v2 baseline freeze with documented limitations."
    return "- NO-GO until control checks are restored."


def format_value(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
