"""
Localization-error tolerance of greedy directional forwarding.

Relative coordinates are perturbed with isotropic Gaussian noise at a fraction
of the nominal neighbor spacing. Absolute GPS is not restored. The question is
how inaccurate the virtual coordinates may become before packet delivery
deteriorates materially.

  python experiments/localization_noise_sensitivity.py --seeds 10 --pairs 300
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
    ensure_dirs,
    prepared_layout,
    sample_pairs,
)
from src.greedy_directional_routing import greedy_route, hop_distance_matrix  # noqa: E402
from src.metrics import routing_metrics  # noqa: E402
from src.relative_localization import perturb_coords  # noqa: E402

NOISE_LEVELS = (0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PDR vs relative-coordinate perturbation.")
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--pairs", type=int, default=300)
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--k", type=int, default=10)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()
    rows = []
    print(
        f"Noise sensitivity: N={args.n}, seeds={args.seeds}, pairs={args.pairs}, "
        f"levels={list(NOISE_LEVELS)}"
    )
    for seed in range(args.seeds):
        layout = prepared_layout(args.n, seed, args.k)
        hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
        rng_pairs = np.random.default_rng(20_000 + seed)
        pairs = sample_pairs(layout.n_nodes, args.pairs, rng_pairs, hop_dist)
        base = layout.relative
        for level in NOISE_LEVELS:
            rng = np.random.default_rng(30_000 + seed * 100 + int(level * 100))
            noisy = perturb_coords(base, level * layout.spacing, rng)
            routes = [
                greedy_route(s, d, noisy, layout.radio_ids, hop_dist=hop_dist)
                for s, d in pairs
            ]
            m = routing_metrics(routes)
            rows.append(
                {
                    "n_nodes": args.n,
                    "seed": seed,
                    "noise_frac_spacing": level,
                    "sigma_px": level * layout.spacing,
                    **m,
                }
            )
            print(
                f"  seed={seed:02d} noise={100*level:4.0f}%  "
                f"PDR={m['pdr']:.3f}  stretch={m['mean_stretch_delivered']:.3f}"
            )

    raw = pd.DataFrame(rows)
    summary = (
        raw.groupby("noise_frac_spacing", as_index=False)
        .agg(
            n_seeds=("seed", "nunique"),
            pdr=("pdr", "mean"),
            pdr_std=("pdr", "std"),
            mean_stretch_delivered=("mean_stretch_delivered", "mean"),
            stretch_std=("mean_stretch_delivered", "std"),
            greedy_failure_rate=("greedy_failure_rate", "mean"),
            loop_rate=("loop_rate", "mean"),
        )
        .sort_values("noise_frac_spacing")
    )
    raw_path = RESULTS / "routing_noise_raw.csv"
    sum_path = RESULTS / "routing_noise_summary.csv"
    raw.to_csv(raw_path, index=False)
    summary.to_csv(sum_path, index=False)

    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    x = 100.0 * summary["noise_frac_spacing"].to_numpy()
    y = summary["pdr"].to_numpy()
    yerr = summary["pdr_std"].fillna(0).to_numpy()
    ax.errorbar(x, y, yerr=yerr, marker="o", color="#1f4e79", lw=1.6, capsize=3)
    ax.set_xlabel("Relative-coordinate perturbation (% of nominal spacing)")
    ax.set_ylabel("Packet delivery ratio")
    ax.set_ylim(0, 1.05)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(RESULTS / "noise_pdr.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGS / "figD_noise_sensitivity.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    ys = summary["mean_stretch_delivered"].to_numpy()
    serr = summary["stretch_std"].fillna(0).to_numpy()
    ax.errorbar(x, ys, yerr=serr, marker="s", color="#8b3a2a", lw=1.6, capsize=3)
    ax.set_xlabel("Relative-coordinate perturbation (% of nominal spacing)")
    ax.set_ylabel("Mean hop stretch (delivered routes)")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(RESULTS / "noise_stretch.png", dpi=180, bbox_inches="tight")
    fig.savefig(FIGS / "figD_noise_stretch.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("\nSummary:")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print("\nWrote:")
    for pth in (
        raw_path,
        sum_path,
        RESULTS / "noise_pdr.png",
        RESULTS / "noise_stretch.png",
        FIGS / "figD_noise_sensitivity.png",
    ):
        print(" ", pth)


if __name__ == "__main__":
    main()
