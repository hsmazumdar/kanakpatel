"""Post-process topology_quality_raw.csv: medians + captions (MDS-init runs)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_topology_quality import RESULTS, assessment, make_topology_figure  # noqa: E402


def summarize_robust(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for n, g in raw.groupby("n_nodes"):
        mae = g["angle_mae_deg"]
        dc = g["directional_correctness"]
        rows.append(
            {
                "n_nodes": int(n),
                "n_trials": len(g),
                "reference_columns": int(g["reference_columns"].iloc[0]),
                "tx_pct": float(g["tx_pct"].iloc[0]),
                "connected_rate": float(g["connected"].mean()),
                "mean_degree_avg": float(g["mean_degree"].mean()),
                "angle_mae_deg": float(mae.median()),
                "angle_mae_mean": float(mae.mean()),
                "angle_mae_std": float(mae.std(ddof=1)) if len(g) > 1 else 0.0,
                "angle_mae_min": float(mae.min()),
                "angle_sd_deg": float(g["angle_sd_deg"].median()),
                "angle_cv_pct": float(g["angle_cv_pct"].median()),
                "success_rate_mae_lt6": float((mae < 6.0).mean()),
                "directional_correctness": float(dc.median()),
                "directional_correctness_mean": float(dc.mean()),
                "procrustes_rmse_median": float(g["procrustes_rmse"].median()),
                "best_seed": int(g.loc[mae.idxmin(), "seed"]),
                "init_mode": str(g["init_mode"].iloc[0]) if "init_mode" in g else "mds",
                "assessment": assessment(float(mae.median())),
            }
        )
    return pd.DataFrame(rows).sort_values("n_nodes").round(4)


def write_table_markdown(summary: pd.DataFrame) -> None:
    lines = [
        "",
        "## Table (Ver03). Topological consistency — black guideline angle analysis (planned geometry)",
        "",
        "Planned-geometry expected distances; classical MDS initialization on expected-distance "
        "shortest paths, then asymmetric-attraction refine; uniform normalize. "
        "Reported MAE/SD/CV and directional correctness are **trial medians**. "
        "Success = fraction of trials with MAE < 6°. Seeds: 20 (N<1000) or 10 (N≥1000).",
        "",
        "| Nodes | Ref. columns | SD [°] | CV [%] | Angle MAE [°] | Dir. correct. | "
        "Success (MAE<6°) | Assessment |",
        "|------:|-------------:|-------:|-------:|--------------:|--------------:|"
        "----------------:|:-----------|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            "| {n} | {c} | {sd:.2f} | {cv:.2f} | {mae:.2f} | {dc:.1f}% | {suc:.0f}% | {a} |".format(
                n=int(r["n_nodes"]),
                c=int(r["reference_columns"]),
                sd=r["angle_sd_deg"],
                cv=r["angle_cv_pct"],
                mae=r["angle_mae_deg"],
                dc=100 * r["directional_correctness"],
                suc=100 * r["success_rate_mae_lt6"],
                a=r["assessment"],
            )
        )
    lines += [
        "",
        "*Artifacts:* `topology_quality_raw.csv`, `topology_quality_summary.csv`, "
        "`table_topology_angle_mae.csv`, `figures/fig_topology_preservation_N250.png`, "
        "`figures/fig_topology_guidelines_overlay_N250.png`.",
        "",
    ]
    path = RESULTS / "paper_tables.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## Table (Ver03). Topological consistency"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip()
    path.write_text(existing + "\n" + "\n".join(lines), encoding="utf-8")


def update_captions(best_seed: int) -> None:
    path = RESULTS / "captions.md"
    block = f"""
---

## Ver03 topology-quality figures (B1–B3)

**Fig. T1 (Ver03).** Topological preservation in a 250-node network (planned geometry supplies expected distances; classical MDS initialization on the distance graph; asymmetric-attraction refine; uniform scale normalization). Left: reference topology; right: localized map after similarity (Procrustes) alignment. Gray: communication edges; black: column guidelines. Shown trial seed={best_seed}.
*File:* `figures/fig_topology_preservation_N250.png`

**Fig. T2 (Ver03).** Correspondence guidelines after Procrustes alignment (N=250, same trial as Fig. T1): black segments join reference nodes to localized counterparts (subsampled).
*File:* `figures/fig_topology_guidelines_overlay_N250.png`

**Table T1 (Ver03).** Topological consistency vs network size (black-guideline edge-direction MAE/SD/CV and directional correctness ±30°). Values are trial **medians**; success rate = fraction with MAE < 6°. Auditable CSVs in `Results/`.
*Source:* `table_topology_angle_mae.csv` · also in `paper_tables.md`
"""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## Ver03 topology-quality figures"
    if marker in text:
        text = text.split(marker)[0].rstrip()
    path.write_text(text + "\n" + block, encoding="utf-8")


def main() -> None:
    raw = pd.read_csv(RESULTS / "topology_quality_raw.csv")
    summary = summarize_robust(raw)
    summary.to_csv(RESULTS / "topology_quality_summary.csv", index=False)
    summary[
        [
            "n_nodes",
            "reference_columns",
            "angle_sd_deg",
            "angle_cv_pct",
            "angle_mae_deg",
            "directional_correctness",
            "success_rate_mae_lt6",
            "assessment",
            "best_seed",
            "angle_mae_min",
        ]
    ].to_csv(RESULTS / "table_topology_angle_mae.csv", index=False)

    best = int(summary.loc[summary["n_nodes"] == 250, "best_seed"].iloc[0])
    print("N=250 best seed", best, "median MAE", summary.loc[summary.n_nodes == 250, "angle_mae_deg"].iloc[0])
    make_topology_figure(250, best)
    write_table_markdown(summary)
    update_captions(best)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
