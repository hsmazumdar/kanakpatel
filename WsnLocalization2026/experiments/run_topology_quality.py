"""
B1–B3: Localization quality / topological consistency (Mode A, planned geometry).

Produces:
  Results/topology_quality_raw.csv
  Results/topology_quality_summary.csv
  Results/table_topology_angle_mae.csv
  Results/figures/fig_topology_preservation_N250.png
  Updates Results/captions.md and Results/paper_tables.md appendices
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from wsn_sim import SimConfig, _procrustes_align, run_trial_detailed  # noqa: E402

RESULTS = ROOT / "Results"
FIGS = RESULTS / "figures"

# V01-style sizes; Mode A (reference layout supplies expected distances)
# MDS init + attraction refine yields stable angular metrics for the quality table.
NODE_SIZES = [25, 64, 100, 250, 500, 750, 1000, 1500, 2000]
N_SEEDS_DEFAULT = 20
N_SEEDS_LARGE = 10  # for N >= 1000
K_NEIGHBORS = 10
# R ≈ RANGE_FACTOR * mean spacing → connected k-NN graphs on fixed canvas
RANGE_FACTOR = 2.8
ATTRACTION = 0.3
MOVES_PER_TICK = 200
FIG_N = 250
FIG_SEED = 0
DIR_CORRECT_DEG = 30.0
DIR_SAMPLES = 200
INIT_MODE = "mds"


def max_ticks_for_n(n: int) -> int:
    # MDS already places nodes; short attraction refine is enough.
    return 150


def tx_pct_for_n(n: int, canvas: int = 800) -> float:
    diag = math.sqrt(2 * canvas * canvas)
    spacing = math.sqrt((canvas * canvas) / n)
    r = RANGE_FACTOR * spacing
    return float(np.clip(100.0 * r / diag, 5.0, 45.0))


def reference_columns(n: int) -> int:
    return int(math.ceil(math.sqrt(n)))


def _angle_deg(v: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(v[1], v[0])))


def _wrap_abs_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def guideline_angle_errors(
    ref_c: np.ndarray, aligned: np.ndarray, dst_id: list
) -> np.ndarray:
    """
    Black-guideline angle analysis: for each undirected stored neighbor edge, compare
    direction angle in the reference map vs the similarity-aligned localized map.
    Mode A: planned geometry is the independent reference; expected distances come
    from that same layout (standard for planned deployments).
    """
    errs = []
    for i, nbrs in enumerate(dst_id):
        for nbr in nbrs:
            nbr = int(nbr)
            if nbr <= i:
                continue
            v_ref = ref_c[nbr] - ref_c[i]
            v_loc = aligned[nbr] - aligned[i]
            if np.linalg.norm(v_ref) < 1e-9 or np.linalg.norm(v_loc) < 1e-9:
                continue
            errs.append(_wrap_abs_diff(_angle_deg(v_ref), _angle_deg(v_loc)))
    return np.asarray(errs, dtype=np.float64)


def directional_correctness(
    ref_c: np.ndarray,
    aligned: np.ndarray,
    dst_id: list,
    rng: np.random.Generator,
    n_samples: int = DIR_SAMPLES,
    tol_deg: float = DIR_CORRECT_DEG,
) -> float:
    """
    Greedy directional forwarding on the localized map: choose the neighbor whose
    localized bearing best matches the localized destination bearing; score whether
    that neighbor lies within ±tol of the true destination bearing in the reference.
    """
    n = len(ref_c)
    if n < 3:
        return float("nan")
    ok = 0
    trials = 0
    for _ in range(n_samples):
        src, dst = (int(x) for x in rng.choice(n, size=2, replace=False))
        nbrs = dst_id[src]
        if len(nbrs) == 0:
            continue
        loc_dest = aligned[dst] - aligned[src]
        ref_dest = ref_c[dst] - ref_c[src]
        if np.linalg.norm(loc_dest) < 1e-9 or np.linalg.norm(ref_dest) < 1e-9:
            continue
        loc_ang = _angle_deg(loc_dest)
        true_ang = _angle_deg(ref_dest)

        best = None
        best_err = 1e9
        for nbr in nbrs:
            nbr = int(nbr)
            v = aligned[nbr] - aligned[src]
            if np.linalg.norm(v) < 1e-9:
                continue
            err = _wrap_abs_diff(_angle_deg(v), loc_ang)
            if err < best_err:
                best_err = err
                best = nbr
        if best is None:
            continue
        trials += 1
        v_ref = ref_c[best] - ref_c[src]
        if np.linalg.norm(v_ref) < 1e-9:
            continue
        if _wrap_abs_diff(_angle_deg(v_ref), true_ang) <= tol_deg:
            ok += 1
    return ok / trials if trials else float("nan")


def assessment(mae: float) -> str:
    if mae < 6.0:
        return "Excellent"
    if mae < 12.0:
        return "Well Achieved"
    if mae < 20.0:
        return "Acceptable"
    return "Needs Attention"


def run_one(n: int, seed: int) -> dict:
    cfg = SimConfig(
        n_nodes=n,
        tx_pct=tx_pct_for_n(n),
        k_neighbors=K_NEIGHBORS,
        attraction=ATTRACTION,
        moves_per_tick=MOVES_PER_TICK,
        max_ticks=max_ticks_for_n(n),
        seed=seed,
        uniform_normalize=True,
        init_mode=INIT_MODE,
        early_stop=False,
    )
    detailed = run_trial_detailed(cfg)
    s = detailed.summary
    ref_c, aligned, _ = _procrustes_align(
        detailed.reference, detailed.localized, detailed.ref_map
    )
    errs = guideline_angle_errors(ref_c, aligned, detailed.dst_id)
    rng = np.random.default_rng(seed + 10_000)
    dcorr = directional_correctness(ref_c, aligned, detailed.dst_id, rng)
    mae = float(np.mean(errs)) if len(errs) else float("nan")
    sd = float(np.std(errs)) if len(errs) else float("nan")
    mean_abs = mae
    cv = float(100.0 * sd / mean_abs) if mean_abs and mean_abs > 1e-12 else float("nan")
    return {
        "n_nodes": n,
        "seed": seed,
        "tx_pct": s.tx_pct,
        "k_neighbors": s.k_neighbors,
        "reference_columns": reference_columns(n),
        "connected": int(s.connected),
        "mean_degree": s.mean_degree,
        "ticks": s.ticks,
        "converged_hard": int(s.converged),
        "mean_constraint_violation": s.mean_constraint_violation,
        "procrustes_rmse": s.procrustes_rmse,
        "angle_mae_deg": mae,
        "angle_sd_deg": sd,
        "angle_cv_pct": cv,
        "n_edge_angles": int(len(errs)),
        "directional_correctness": dcorr,
        "mode": "A_planned_geometry",
        "init_mode": INIT_MODE,
        "uniform_normalize": 1,
        "early_stop": 0,
        "max_ticks": cfg.max_ticks,
    }


def make_topology_figure(n: int = FIG_N, seed: int = FIG_SEED) -> Path:
    FIGS.mkdir(parents=True, exist_ok=True)
    cfg = SimConfig(
        n_nodes=n,
        tx_pct=tx_pct_for_n(n),
        k_neighbors=K_NEIGHBORS,
        attraction=ATTRACTION,
        moves_per_tick=MOVES_PER_TICK,
        max_ticks=max_ticks_for_n(n),
        seed=seed,
        uniform_normalize=True,
        init_mode=INIT_MODE,
        early_stop=False,
    )
    detailed = run_trial_detailed(cfg)
    ref_c, aligned, rmse = _procrustes_align(
        detailed.reference, detailed.localized, detailed.ref_map
    )
    # Shift both to positive display coords
    def _to_plot(pts: np.ndarray) -> np.ndarray:
        p = pts.copy()
        p -= p.min(axis=0)
        return p

    ref_p = _to_plot(ref_c)
    loc_p = _to_plot(aligned)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.0))
    for ax, pts, title in (
        (axes[0], ref_p, "Reference topology (planned)"),
        (axes[1], loc_p, "Localized topology (aligned)"),
    ):
        # Edges
        for ref_i, nbrs in enumerate(detailed.dst_id):
            for nbr in nbrs:
                nbr = int(nbr)
                if nbr <= ref_i:
                    continue
                ax.plot(
                    [pts[ref_i, 0], pts[nbr, 0]],
                    [pts[ref_i, 1], pts[nbr, 1]],
                    color="#b0b0b0",
                    lw=0.4,
                    zorder=1,
                )
        ax.scatter(pts[:, 0], pts[:, 1], s=8, c="#1f4e79", zorder=2)
        # Black guidelines: a subset of correspondence / column polylines
        cols = reference_columns(n)
        order = np.arange(n)
        # Draw vertical-ish guidelines along reference column groups
        for c in range(min(cols, 12)):
            idxs = order[c::cols]
            if len(idxs) < 2:
                continue
            ax.plot(
                pts[idxs, 0],
                pts[idxs, 1],
                color="black",
                lw=0.9,
                alpha=0.85,
                zorder=3,
            )
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle(
        f"Topological preservation (N={n}, Mode A, seed={seed}, "
        f"Procrustes RMSE={rmse:.1f} px)",
        fontsize=11,
    )
    fig.tight_layout()
    out = FIGS / "fig_topology_preservation_N250.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Overlay correspondence guidelines (ref vs aligned) as extra visual
    fig2, ax = plt.subplots(figsize=(6.2, 6.0))
    # Align display frames to same origin
    both_min = np.minimum(ref_c.min(axis=0), aligned.min(axis=0))
    ref_o = ref_c - both_min
    loc_o = aligned - both_min
    ax.scatter(ref_o[:, 0], ref_o[:, 1], s=10, c="#1f4e79", label="Reference", zorder=2)
    ax.scatter(loc_o[:, 0], loc_o[:, 1], s=10, c="#8b3a2a", label="Localized (aligned)", zorder=2)
    step = max(1, n // 80)
    for i in range(0, n, step):
        ax.plot(
            [ref_o[i, 0], loc_o[i, 0]],
            [ref_o[i, 1], loc_o[i, 1]],
            color="black",
            lw=0.5,
            alpha=0.7,
            zorder=1,
        )
    ax.set_aspect("equal")
    ax.legend(fontsize=8, loc="best")
    ax.set_title(f"Correspondence guidelines after similarity alignment (N={n})")
    ax.set_xticks([])
    ax.set_yticks([])
    fig2.tight_layout()
    out2 = FIGS / "fig_topology_guidelines_overlay_N250.png"
    fig2.savefig(out2, dpi=180, bbox_inches="tight")
    plt.close(fig2)
    return out


def summarize(raw: pd.DataFrame) -> pd.DataFrame:
    g = (
        raw.groupby("n_nodes", as_index=False)
        .agg(
            n_trials=("seed", "count"),
            reference_columns=("reference_columns", "first"),
            tx_pct=("tx_pct", "first"),
            connected_rate=("connected", "mean"),
            mean_degree_avg=("mean_degree", "mean"),
            angle_mae_deg=("angle_mae_deg", "mean"),
            angle_mae_std=("angle_mae_deg", "std"),
            angle_sd_deg=("angle_sd_deg", "mean"),
            angle_cv_pct=("angle_cv_pct", "mean"),
            directional_correctness=("directional_correctness", "mean"),
            directional_correctness_std=("directional_correctness", "std"),
            procrustes_rmse=("procrustes_rmse", "mean"),
            violation_avg=("mean_constraint_violation", "mean"),
        )
        .sort_values("n_nodes")
    )
    g["assessment"] = g["angle_mae_deg"].map(assessment)
    return g.round(
        {
            "connected_rate": 3,
            "mean_degree_avg": 2,
            "angle_mae_deg": 2,
            "angle_mae_std": 2,
            "angle_sd_deg": 2,
            "angle_cv_pct": 2,
            "directional_correctness": 4,
            "directional_correctness_std": 4,
            "procrustes_rmse": 2,
            "violation_avg": 3,
            "tx_pct": 2,
        }
    )


def write_table_markdown(summary: pd.DataFrame) -> None:
    lines = [
        "",
        "## Table (Ver03). Topological consistency — black guideline angle analysis (Mode A)",
        "",
        "Mode A planned geometry; classical MDS init on expected-distance shortest paths, "
        "then asymmetric-attraction refine; uniform (similarity) normalization. "
        "Seeds: 20 for N<1000, 10 for N≥1000. "
        f"Canvas 800×800, k=10, Tx% = clip(100·{RANGE_FACTOR}·spacing/diag, 5, 45).",
        "",
        "| Nodes | Ref. columns | SD [°] | CV [%] | Relative angle MAE [°] | Dir. correct. | Assessment |",
        "|------:|-------------:|-------:|-------:|-----------------------:|--------------:|:-----------|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {int(r['n_nodes'])} | {int(r['reference_columns'])} | "
            f"{r['angle_sd_deg']:.2f} | {r['angle_cv_pct']:.2f} | "
            f"{r['angle_mae_deg']:.2f} | {100*r['directional_correctness']:.1f}% | "
            f"{r['assessment']} |"
        )
    lines += [
        "",
        "*Artifacts:* `topology_quality_raw.csv`, `topology_quality_summary.csv`, "
        "`table_topology_angle_mae.csv`, "
        "`figures/fig_topology_preservation_N250.png`, "
        "`figures/fig_topology_guidelines_overlay_N250.png`.",
        "",
    ]
    path = RESULTS / "paper_tables.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## Table (Ver03). Topological consistency"
    if marker in existing:
        head = existing.split(marker)[0].rstrip()
        path.write_text(head + "\n" + "\n".join(lines), encoding="utf-8")
    else:
        path.write_text(existing.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")


def update_captions() -> None:
    path = RESULTS / "captions.md"
    block = """
---

## Ver03 topology-quality figures (B1–B3)

**Fig. T1 (Ver03).** Topological preservation in a 250-node network (Mode A: planned geometry → expected distances; classical MDS initialization on the distance graph; asymmetric-attraction refine; uniform scale normalization). Left: reference topology; right: localized topology after similarity (Procrustes) alignment. Gray lines are communication edges; black polylines are column guidelines used for angular-structure comparison.
*File:* `figures/fig_topology_preservation_N250.png`

**Fig. T2 (Ver03).** Correspondence guidelines after Procrustes (similarity) alignment for N=250: black segments join each reference node to its localized counterpart (subsampled for clarity). Short segments indicate isometric consistency up to residual noise.
*File:* `figures/fig_topology_guidelines_overlay_N250.png`

**Table T1 (Ver03).** Summary of topological consistency across network sizes using black guideline angle analysis (relative edge-direction MAE, SD, CV) and directional correctness (±30°). Mode A with MDS init + attraction refine; 20 seeds (10 for N≥1000). Auditable CSVs under `Results/`.
*Source:* `table_topology_angle_mae.csv` · also in `paper_tables.md`
"""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## Ver03 topology-quality figures"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n" + block
    else:
        text = text.rstrip() + "\n" + block
    path.write_text(text, encoding="utf-8")


def n_seeds_for(n: int) -> int:
    return N_SEEDS_LARGE if n >= 1000 else N_SEEDS_DEFAULT


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    total = sum(n_seeds_for(n) for n in NODE_SIZES)
    done = 0
    print(f"Running topology quality: sizes={NODE_SIZES}, total trials={total}")
    for n in NODE_SIZES:
        for seed in range(n_seeds_for(n)):
            row = run_one(n, seed)
            rows.append(row)
            done += 1
            if done % 5 == 0 or done == total:
                print(
                    f"  [{done}/{total}] N={n} seed={seed} "
                    f"MAE={row['angle_mae_deg']:.2f} deg "
                    f"dir={100 * row['directional_correctness']:.1f}% "
                    f"conn={row['connected']}"
                )

    raw = pd.DataFrame(rows)
    raw.to_csv(RESULTS / "topology_quality_raw.csv", index=False)
    summary = summarize(raw)
    summary.to_csv(RESULTS / "topology_quality_summary.csv", index=False)

    table = summary[
        [
            "n_nodes",
            "reference_columns",
            "angle_sd_deg",
            "angle_cv_pct",
            "angle_mae_deg",
            "directional_correctness",
            "assessment",
        ]
    ].copy()
    table.to_csv(RESULTS / "table_topology_angle_mae.csv", index=False)

    fig_path = make_topology_figure(FIG_N, FIG_SEED)
    write_table_markdown(summary)
    update_captions()

    print("\nSummary:")
    print(summary.to_string(index=False))
    print("\nWrote:")
    print(" ", RESULTS / "topology_quality_raw.csv")
    print(" ", RESULTS / "topology_quality_summary.csv")
    print(" ", RESULTS / "table_topology_angle_mae.csv")
    print(" ", fig_path)
    print(" ", FIGS / "fig_topology_guidelines_overlay_N250.png")


if __name__ == "__main__":
    main()
