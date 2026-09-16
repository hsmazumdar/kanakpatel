"""
Greedy routing around a communication void.

The connected planned-geometry graphs in the first routing campaign produced
PDR=1.000, so greedy failure modes were unused. This experiment inserts a
central obstacle: nodes are not placed inside it and radio links may not cross
it. The same source-destination pairs are then routed under reference, MDS-only
and MDS+attraction coordinates.

  python experiments/routing_voids.py --seeds 10 --pairs 300
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _routing_common import FIGS, RESULTS, CASES, ensure_dirs, route_cases, sample_pairs
from src.greedy_directional_routing import greedy_route, hop_distance_matrix
from src.metrics import routing_metrics
from src.relative_localization import (
    build_layout,
    default_center_void,
    embed_relative_map,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GPS-denied greedy routing with a central void.")
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--pairs", type=int, default=300)
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--example-seed", type=int, default=3)
    return p.parse_args()


def prepared_void_layout(n_nodes: int, seed: int, k_neighbors: int = 10):
    layout = build_layout(
        n_nodes=n_nodes,
        seed=seed,
        k_neighbors=k_neighbors,
        obstacles=default_center_void(),
        range_factor=2.8,
    )
    return embed_relative_map(layout, seed=seed)


def example_figure(n: int, seed: int, k: int, outfile: Path) -> None:
    layout = prepared_void_layout(n, seed, k)
    hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
    cand = np.argwhere(hop_dist >= 8)
    if len(cand) == 0:
        cand = np.argwhere(hop_dist > 0)
    rng = np.random.default_rng(seed + 51)
    src, dest = (int(x) for x in cand[int(rng.integers(0, len(cand)))])
    ref = greedy_route(src, dest, layout.reference, layout.radio_ids, hop_dist=hop_dist)
    rel = greedy_route(
        src, dest, layout.relative, layout.radio_ids, hop_dist=hop_dist,
        reference_coords=layout.reference,
    )

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 5.2))
    titles = (
        f"Reference  {ref.status}  hops={ref.hop_count}",
        f"Relative (GPS-denied)  {rel.status}  hops={rel.hop_count}",
    )
    for ax, coords, route, title in zip(
        axes, (layout.reference, layout.relative), (ref, rel), titles
    ):
        pts = coords
        for i, nbrs in enumerate(layout.radio_ids):
            for j in nbrs:
                j = int(j)
                if j <= i:
                    continue
                ax.plot(
                    [pts[i, 0], pts[j, 0]],
                    [pts[i, 1], pts[j, 1]],
                    color="#d8d8d8",
                    lw=0.3,
                    zorder=1,
                )
        ax.scatter(pts[:, 0], pts[:, 1], s=9, c="#5c6b75", zorder=2)
        for rect in layout.obstacles:
            x0, y0, x1, y1 = rect
            ax.add_patch(
                patches.Rectangle(
                    (x0, y0), x1 - x0, y1 - y0,
                    facecolor="#f4e4d4", edgecolor="#8b3a2a", lw=1.2, zorder=3, alpha=0.85,
                )
            )
            ax.text(
                (x0 + x1) / 2, (y0 + y1) / 2, "VOID",
                ha="center", va="center", fontsize=8, color="#8b3a2a", zorder=4,
            )
        if len(route.path) >= 2:
            xy = pts[np.array(route.path)]
            ax.plot(xy[:, 0], xy[:, 1], color="#c0392b", lw=2.0, zorder=5)
        ax.scatter(*pts[src], s=70, c="#1f4e79", marker="s", zorder=6, label="Source")
        ax.scatter(*pts[dest], s=90, c="#117a3a", marker="*", zorder=6, label="Destination")
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.legend(loc="upper right", fontsize=8)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle(
        f"Greedy forwarding around a communication void (N={n}, seed={seed}, src={src}, dest={dest})",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    rows = []
    print(f"Void routing: N={args.n}, seeds={args.seeds}, pairs={args.pairs}")
    for seed in range(args.seeds):
        layout = prepared_void_layout(args.n, seed, args.k)
        hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
        rng = np.random.default_rng(40_000 + seed)
        pairs = sample_pairs(layout.n_nodes, args.pairs, rng, hop_dist, min_hops=3)
        routes = route_cases(layout, pairs, hop_dist)
        line = [f"seed={seed:02d} connected={int(layout.connected)} pairs={len(pairs)}"]
        for name, rr in routes.items():
            m = routing_metrics(rr)
            rows.append(
                {
                    "n_nodes": args.n,
                    "seed": seed,
                    "connected": int(layout.connected),
                    "n_pairs": m["n_pairs"],
                    "case": name,
                    **m,
                }
            )
            line.append(f"{name[0]} PDR={m['pdr']:.3f} fail={m['greedy_failure_rate']:.3f}")
        print("  " + "  ".join(line))

    per = pd.DataFrame(rows)
    summary = (
        per.groupby("case", as_index=False)
        .agg(
            n_seeds=("seed", "nunique"),
            n_pairs=("n_pairs", "sum"),
            connected_rate=("connected", "mean"),
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
    per.to_csv(RESULTS / "routing_voids_per_seed.csv", index=False)
    summary.to_csv(RESULTS / "routing_voids_summary.csv", index=False)

    labels = ["Reference", "MDS-only", "MDS + attraction"]
    keys = ["A_reference", "B_mds_only", "C_mds_attraction"]
    colors = ["#1f4e79", "#6b7c85", "#8b3a2a"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for ax, col, ylab, ylim in (
        (axes[0], "pdr", "Packet delivery ratio", (0, 1.05)),
        (axes[1], "greedy_failure_rate", "Greedy failure rate", (0, None)),
    ):
        vals = [float(summary.loc[summary["case"] == k, col].mean()) for k in keys]
        ax.bar(labels, vals, color=colors, width=0.62, edgecolor="black", lw=0.6)
        ax.set_ylabel(ylab)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, linestyle=":", alpha=0.6)
        if ylim[1] is not None:
            ax.set_ylim(*ylim)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    fig.suptitle("GPS-denied greedy routing with a central communication void", fontsize=11)
    fig.tight_layout()
    fig.savefig(RESULTS / "void_pdr_comparison.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGS / "figE_void_pdr.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    example_figure(args.n, args.example_seed, args.k, FIGS / "figE_void_example_routes.png")

    print("\nSummary:")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\nWrote:")
    for pth in (
        RESULTS / "routing_voids_summary.csv",
        RESULTS / "void_pdr_comparison.png",
        FIGS / "figE_void_pdr.png",
        FIGS / "figE_void_example_routes.png",
    ):
        print(" ", pth)


if __name__ == "__main__":
    main()
