"""
Compare greedy directional forwarding on:
  A — reference / planned coordinates (best-case geometric baseline)
  B — MDS-only relative coordinates
  C — MDS + asymmetric-attraction relative coordinates

GPS/reference coordinates are used as simulation ground truth and as Case A.
Cases B and C route without absolute geographic coordinates.

Example:
  python experiments/routing_reference_vs_relative.py --seeds 20 --pairs 500
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _routing_common import (  # noqa: E402
    FIGS,
    RESULTS,
    build_and_route,
    ensure_dirs,
)
from src.metrics import routing_metrics  # noqa: E402
from src.greedy_directional_routing import greedy_route  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Paired greedy-routing comparison: reference vs MDS vs relative map."
    )
    p.add_argument("--seeds", type=int, default=20)
    p.add_argument("--pairs", type=int, default=500)
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--example-seed", type=int, default=13)
    return p.parse_args()


def bar_plot(summary: pd.DataFrame, column: str, ylabel: str, outfile: Path, ylim=None) -> None:
    labels = ["Reference", "MDS-only", "MDS + attraction"]
    keys = ["A_reference", "B_mds_only", "C_mds_attraction"]
    vals = [float(summary.loc[summary["case"] == k, column].mean()) for k in keys]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    colors = ["#1f4e79", "#6b7c85", "#8b3a2a"]
    ax.bar(labels, vals, color=colors, width=0.62, edgecolor="black", linewidth=0.6)
    ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", alpha=0.6)
    if ylim is not None:
        ax.set_ylim(*ylim)
    for i, v in enumerate(vals):
        if np.isfinite(v):
            ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(outfile, dpi=180, bbox_inches="tight")
    plt.close(fig)


def example_route_figure(n: int, seed: int, k: int, outfile: Path) -> None:
    from _routing_common import prepared_layout
    from src.greedy_directional_routing import hop_distance_matrix

    layout = prepared_layout(n, seed, k)
    hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
    # Choose a moderately long connected pair
    cand = np.argwhere(hop_dist >= 6)
    if len(cand) == 0:
        cand = np.argwhere(hop_dist > 0)
    rng = np.random.default_rng(seed + 77)
    src, dest = (int(x) for x in cand[int(rng.integers(0, len(cand)))])

    ref_route = greedy_route(src, dest, layout.reference, layout.radio_ids, hop_dist=hop_dist)
    rel_route = greedy_route(
        src,
        dest,
        layout.relative,
        layout.radio_ids,
        hop_dist=hop_dist,
        reference_coords=layout.reference,
    )

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 5.1))
    titles = (
        f"Reference-coordinate routing\n{ref_route.status}, hops={ref_route.hop_count}",
        f"Relative-coordinate routing (GPS-denied)\n{rel_route.status}, hops={rel_route.hop_count}",
    )
    paths = (ref_route.path, rel_route.path)
    coords_list = (layout.reference, layout.relative)
    for ax, pts, path, title in zip(axes, coords_list, paths, titles):
        for i, nbrs in enumerate(layout.radio_ids):
            for j in nbrs:
                j = int(j)
                if j <= i:
                    continue
                ax.plot(
                    [pts[i, 0], pts[j, 0]],
                    [pts[i, 1], pts[j, 1]],
                    color="#d0d0d0",
                    lw=0.35,
                    zorder=1,
                )
        ax.scatter(pts[:, 0], pts[:, 1], s=10, c="#7a8b99", zorder=2)
        if len(path) >= 2:
            xy = pts[np.array(path)]
            ax.plot(xy[:, 0], xy[:, 1], color="#c0392b", lw=2.0, zorder=3)
            ax.scatter(xy[:, 0], xy[:, 1], s=18, c="#c0392b", zorder=4)
        ax.scatter(*pts[src], s=70, c="#1f4e79", marker="s", zorder=5, label="Source")
        ax.scatter(*pts[dest], s=90, c="#117a3a", marker="*", zorder=5, label="Destination")
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.legend(loc="upper right", fontsize=8, frameon=True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle(
        f"Example greedy paths on the same source–destination pair (N={n}, seed={seed}, "
        f"src={src}, dest={dest})",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    rows = []
    raw_rows = []
    print(
        f"Greedy routing comparison: N={args.n}, seeds={args.seeds}, "
        f"pairs/seed={args.pairs}"
    )
    for seed in range(args.seeds):
        layout, pairs, _, routes = build_and_route(args.n, seed, args.pairs, args.k)
        print(
            f"  seed={seed:02d} connected={int(layout.connected)} pairs={len(pairs)}",
            end="",
        )
        line = []
        for name, rr in routes.items():
            m = routing_metrics(rr)
            row = {
                "n_nodes": args.n,
                "seed": seed,
                "k_neighbors": args.k,
                "tx_pct": layout.tx_pct,
                "connected": int(layout.connected),
                "n_pairs_requested": args.pairs,
                **m,
                "case": name,
            }
            rows.append(row)
            line.append(f"{name[0]} PDR={m['pdr']:.3f}")
            for r in rr:
                raw_rows.append(
                    {
                        "n_nodes": args.n,
                        "seed": seed,
                        "case": name,
                        "src": r.src,
                        "dest": r.dest,
                        "status": r.status,
                        "hop_count": r.hop_count,
                        "shortest_hops": r.shortest_hops,
                        "stretch": r.stretch,
                        "decision_agreement": r.next_hop_agreement
                        if r.next_hop_agreement is not None
                        else np.nan,
                    }
                )
        print("  " + "  ".join(line))

    raw = pd.DataFrame(raw_rows)
    per_seed = pd.DataFrame(rows)
    summary = (
        per_seed.groupby("case", as_index=False)
        .agg(
            n_seeds=("seed", "nunique"),
            n_pairs=("n_pairs", "sum"),
            pdr=("pdr", "mean"),
            pdr_std=("pdr", "std"),
            mean_hops_delivered=("mean_hops_delivered", "mean"),
            mean_stretch_delivered=("mean_stretch_delivered", "mean"),
            greedy_failure_rate=("greedy_failure_rate", "mean"),
            loop_rate=("loop_rate", "mean"),
            dead_end_rate=("dead_end_rate", "mean"),
            hop_limit_rate=("hop_limit_rate", "mean"),
            disconnected_rate=("disconnected_rate", "mean"),
            decision_agreement=("decision_agreement", "mean"),
        )
        .sort_values("case")
    )

    raw_path = RESULTS / "routing_raw.csv"
    seed_path = RESULTS / "routing_per_seed.csv"
    sum_path = RESULTS / "routing_summary.csv"
    raw.to_csv(raw_path, index=False)
    per_seed.to_csv(seed_path, index=False)
    summary.to_csv(sum_path, index=False)

    bar_plot(per_seed, "pdr", "Packet delivery ratio", RESULTS / "pdr_comparison.png", (0, 1.05))
    bar_plot(
        per_seed,
        "mean_stretch_delivered",
        "Mean hop stretch (delivered routes)",
        RESULTS / "path_stretch.png",
    )
    bar_plot(
        per_seed,
        "greedy_failure_rate",
        "Greedy failure rate",
        RESULTS / "failure_rate.png",
        (0, None),
    )
    # Manuscript copies
    import shutil

    shutil.copyfile(RESULTS / "pdr_comparison.png", FIGS / "figC_pdr_comparison.png")
    shutil.copyfile(RESULTS / "path_stretch.png", FIGS / "figC_path_stretch.png")
    shutil.copyfile(RESULTS / "failure_rate.png", FIGS / "figC_failure_rate.png")

    example_route_figure(
        args.n, args.example_seed, args.k, FIGS / "figB_example_routes.png"
    )

    print("\nSummary:")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nWrote:")
    for p in (raw_path, seed_path, sum_path, RESULTS / "pdr_comparison.png",
              RESULTS / "path_stretch.png", RESULTS / "failure_rate.png",
              FIGS / "figB_example_routes.png"):
        print(" ", p)


if __name__ == "__main__":
    main()
