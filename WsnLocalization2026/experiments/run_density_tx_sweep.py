"""
Density vs Tx-range experimental sweep for WSN localization.

Input parameter matrix (primary study):
  N_NODES      x  TX_PCT  x  K_NEIGHBORS  x  SEEDS

Fixed controls:
  canvas, attraction, moves/tick, max_ticks, path-loss eta

Outputs (Results/):
  param_matrix.csv          - full input grid
  results_raw.csv           - one row per trial
  results_summary.csv       - mean/std grouped by (N, tx_pct, k)
  table_min_tx_for_degree.csv
  table_convergence_rate.csv
  table_energy_vs_density.csv
"""
from __future__ import annotations

import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

# Allow running from repo root or experiments/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from wsn_sim import SimConfig, run_trial

RESULTS_DIR = ROOT / "Results"

# ---------------------------------------------------------------------------
# INPUT PARAMETER MATRIX
# ---------------------------------------------------------------------------
# Primary factors for "node density vs RSS/Tx range" deployment assist.
# Lower tx_pct => lower Tx energy (range ~ % of diagonal).

PARAM_MATRIX = {
    # Node count -> density on fixed canvas
    "n_nodes": [50, 100, 150, 200, 300],
    # Radio range as % of canvas diagonal (UI: numudTxRange)
    "tx_pct": [5, 8, 10, 12, 15, 20, 25, 30],
    # Max neighbors stored (UI/code: txRange). Keep 10 as paper default;
    # include 6 and 12 to show sensitivity.
    "k_neighbors": [6, 10, 12],
    # Independent Monte-Carlo seeds
    "seeds": [0, 1, 2, 3, 4],
}

# Fixed algorithm / geometry controls (not swept)
FIXED = {
    "canvas_w": 800,
    "canvas_h": 800,
    "attraction": 0.3,
    "moves_per_tick": 100,
    "max_ticks": 250,
    "nod_size": 20,
    "normalize_span": 0.9,
    "path_loss_eta": 2.5,
}


def expand_param_matrix(pm: dict) -> list[dict]:
    keys = ["n_nodes", "tx_pct", "k_neighbors", "seeds"]
    rows = []
    for n, tx, k, seed in itertools.product(
        pm["n_nodes"], pm["tx_pct"], pm["k_neighbors"], pm["seeds"]
    ):
        rows.append(
            {
                "n_nodes": n,
                "tx_pct": tx,
                "k_neighbors": k,
                "seed": seed,
                **FIXED,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def result_to_row(r) -> dict:
    return {
        "n_nodes": r.n_nodes,
        "tx_pct": r.tx_pct,
        "k_neighbors": r.k_neighbors,
        "seed": r.seed,
        "tx_distance_px": round(r.tx_distance, 3),
        "density": f"{r.density:.6e}",
        "spacing_approx": round(r.spacing_approx, 3),
        "r_over_s": round(r.r_over_s, 4),
        "mean_degree": round(r.mean_degree, 3),
        "min_degree": r.min_degree,
        "max_degree": r.max_degree,
        "isolated_nodes": r.isolated_nodes,
        "n_components": r.n_components,
        "connected": int(r.connected),
        "converged": int(r.converged),
        "ticks": r.ticks,
        "mean_constraint_violation": round(r.mean_constraint_violation, 4),
        "procrustes_rmse": round(r.procrustes_rmse, 4),
        "tx_energy_proxy": round(r.tx_energy_proxy, 6),
    }


def summarize(raw: list[dict]) -> list[dict]:
    """Group by (n_nodes, tx_pct, k_neighbors)."""
    groups: dict[tuple, list[dict]] = {}
    for row in raw:
        key = (row["n_nodes"], row["tx_pct"], row["k_neighbors"])
        groups.setdefault(key, []).append(row)

    out = []
    for (n, tx, k), rows in sorted(groups.items()):
        def col(name):
            return np.array([float(r[name]) for r in rows], dtype=np.float64)

        out.append(
            {
                "n_nodes": n,
                "tx_pct": tx,
                "k_neighbors": k,
                "n_trials": len(rows),
                "mean_degree_avg": round(col("mean_degree").mean(), 3),
                "mean_degree_std": round(col("mean_degree").std(), 3),
                "connected_rate": round(col("connected").mean(), 3),
                "converge_rate": round(col("converged").mean(), 3),
                "ticks_avg": round(col("ticks").mean(), 1),
                "ticks_std": round(col("ticks").std(), 1),
                "rmse_avg": round(col("procrustes_rmse").mean(), 3),
                "rmse_std": round(col("procrustes_rmse").std(), 3),
                "violation_avg": round(col("mean_constraint_violation").mean(), 4),
                "r_over_s_avg": round(col("r_over_s").mean(), 4),
                "tx_energy_proxy": round(col("tx_energy_proxy").mean(), 6),
                "isolated_avg": round(col("isolated_nodes").mean(), 2),
            }
        )
    return out


def table_min_tx_for_target_degree(summary: list[dict], target_degree: float = 8.0) -> list[dict]:
    """For each (N, k), smallest tx_pct with mean_degree >= target and connected_rate==1."""
    keys = sorted({(r["n_nodes"], r["k_neighbors"]) for r in summary})
    rows = []
    for n, k in keys:
        cand = [
            r
            for r in summary
            if r["n_nodes"] == n
            and r["k_neighbors"] == k
            and r["mean_degree_avg"] >= target_degree
            and r["connected_rate"] >= 1.0
        ]
        if not cand:
            rows.append(
                {
                    "n_nodes": n,
                    "k_neighbors": k,
                    "target_degree": target_degree,
                    "min_tx_pct": "",
                    "tx_energy_proxy": "",
                    "converge_rate": "",
                    "rmse_avg": "",
                    "note": "no feasible tx in matrix",
                }
            )
            continue
        best = min(cand, key=lambda r: r["tx_pct"])
        rows.append(
            {
                "n_nodes": n,
                "k_neighbors": k,
                "target_degree": target_degree,
                "min_tx_pct": best["tx_pct"],
                "tx_energy_proxy": best["tx_energy_proxy"],
                "converge_rate": best["converge_rate"],
                "rmse_avg": best["rmse_avg"],
                "mean_degree_avg": best["mean_degree_avg"],
                "note": "energy-optimal Tx for density",
            }
        )
    return rows


def table_convergence(summary: list[dict]) -> list[dict]:
    """Pivot-like: N rows, tx_pct columns for converge_rate at k=10."""
    k = 10
    ns = sorted({r["n_nodes"] for r in summary if r["k_neighbors"] == k})
    txs = sorted({r["tx_pct"] for r in summary if r["k_neighbors"] == k})
    lookup = {
        (r["n_nodes"], r["tx_pct"]): r
        for r in summary
        if r["k_neighbors"] == k
    }
    rows = []
    for n in ns:
        row = {"n_nodes": n, "k_neighbors": k}
        for tx in txs:
            r = lookup.get((n, tx))
            row[f"tx{tx}_converge"] = r["converge_rate"] if r else ""
            row[f"tx{tx}_degree"] = r["mean_degree_avg"] if r else ""
        rows.append(row)
    return rows


def table_energy_vs_density(min_tx_table: list[dict]) -> list[dict]:
    """Deployment assist: density vs min Tx energy at k=10."""
    rows = []
    area = FIXED["canvas_w"] * FIXED["canvas_h"]
    for r in min_tx_table:
        if r["k_neighbors"] != 10:
            continue
        n = r["n_nodes"]
        rows.append(
            {
                "n_nodes": n,
                "density": f"{n / area:.6e}",
                "min_tx_pct": r["min_tx_pct"],
                "tx_energy_proxy": r["tx_energy_proxy"],
                "converge_rate": r["converge_rate"],
                "rmse_avg": r["rmse_avg"],
                "note": r["note"],
            }
        )
    return rows


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save input matrix definition
    meta = {"param_matrix": PARAM_MATRIX, "fixed": FIXED}
    (RESULTS_DIR / "param_matrix_definition.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    combos = expand_param_matrix(PARAM_MATRIX)
    write_csv(RESULTS_DIR / "param_matrix.csv", combos)
    print(f"Input combos: {len(combos)}")
    print(f"Factors: N={PARAM_MATRIX['n_nodes']}")
    print(f"         tx_pct={PARAM_MATRIX['tx_pct']}")
    print(f"         k={PARAM_MATRIX['k_neighbors']}")
    print(f"         seeds={PARAM_MATRIX['seeds']}")

    raw_rows = []
    for i, p in enumerate(combos, 1):
        cfg = SimConfig(
            n_nodes=p["n_nodes"],
            tx_pct=float(p["tx_pct"]),
            k_neighbors=p["k_neighbors"],
            attraction=p["attraction"],
            canvas_w=p["canvas_w"],
            canvas_h=p["canvas_h"],
            nod_size=p["nod_size"],
            moves_per_tick=p["moves_per_tick"],
            max_ticks=p["max_ticks"],
            normalize_span=p["normalize_span"],
            path_loss_eta=p["path_loss_eta"],
            seed=p["seed"],
        )
        res = run_trial(cfg)
        raw_rows.append(result_to_row(res))
        if i % 10 == 0 or i == len(combos):
            print(
                f"  [{i}/{len(combos)}] N={p['n_nodes']} tx={p['tx_pct']}% "
                f"k={p['k_neighbors']} seed={p['seed']} "
                f"deg={raw_rows[-1]['mean_degree']} conv={raw_rows[-1]['converged']} "
                f"ticks={raw_rows[-1]['ticks']}",
                flush=True,
            )

    write_csv(RESULTS_DIR / "results_raw.csv", raw_rows)
    summary = summarize(raw_rows)
    write_csv(RESULTS_DIR / "results_summary.csv", summary)

    min_tx = table_min_tx_for_target_degree(summary, target_degree=8.0)
    write_csv(RESULTS_DIR / "table_min_tx_for_degree8.csv", min_tx)

    min_tx6 = table_min_tx_for_target_degree(summary, target_degree=6.0)
    write_csv(RESULTS_DIR / "table_min_tx_for_degree6.csv", min_tx6)

    write_csv(RESULTS_DIR / "table_convergence_rate_k10.csv", table_convergence(summary))
    write_csv(RESULTS_DIR / "table_energy_vs_density_k10.csv", table_energy_vs_density(min_tx))

    print(f"\nWrote results to {RESULTS_DIR}")
    for name in sorted(RESULTS_DIR.glob("*.csv")):
        print(f"  - {name.name}")


if __name__ == "__main__":
    main()
