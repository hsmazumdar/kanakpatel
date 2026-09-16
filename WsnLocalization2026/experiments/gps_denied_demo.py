"""
GPS-availability then GPS-denial demonstration.

Phase 1 — reference coordinates exist only as simulation ground truth.
Phase 2 — absolute coordinates are removed from the routing process.
Packets then forward exclusively in the relative coordinate frame.

The relative map is not built from GPS. Expected-distance constraints come from
planned geometry; GPS is never an algorithmic input to the embedding.

Quick start:
  python experiments/gps_denied_demo.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
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
from src.greedy_directional_routing import greedy_route  # noqa: E402
from src.metrics import format_path, routing_metrics  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GPS-denied greedy routing demo.")
    p.add_argument("--n", type=int, default=120)
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Layout seed. Omit to draw a new network each run.",
    )
    p.add_argument("--pairs", type=int, default=200)
    return p.parse_args()


def draw_concept_figure(outfile: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 8.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3f8", ec="#1f4e79"):
        patch = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor=fc, edgecolor=ec, linewidth=1.4, transform=ax.transData,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=9.5, color="#1b1b1b", wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="#333333", lw=1.3),
        )

    ax.set_title("GPS-denied direction-aware forwarding", fontsize=13, pad=8)
    box(2.4, 10.6, 5.2, 0.9, "GPS / absolute frame\nunavailable", fc="#f8e8e8", ec="#8b3a2a")
    arrow(5.0, 10.6, 5.0, 10.05)
    box(2.4, 9.15, 5.2, 0.85, "Neighbour expected-distance\nconstraints")
    arrow(5.0, 9.15, 5.0, 8.6)
    box(2.4, 7.7, 5.2, 0.85, "Relative embedding\n(up to similarity)")
    arrow(5.0, 7.7, 5.0, 7.15)
    box(2.4, 6.25, 5.2, 0.85, "Direction to destination\nin the virtual frame")
    arrow(5.0, 6.25, 5.0, 5.7)
    box(2.4, 4.8, 5.2, 0.85, "Greedy neighbour selection\n(minimum angular deviation)")
    arrow(5.0, 4.8, 5.0, 4.25)
    box(2.4, 3.35, 5.2, 0.85, "Packet forward\nGPS coordinates not used", fc="#e7f4ea", ec="#117a3a")

    ax.text(
        5.0,
        2.55,
        "A similarity transform (translation, rotation, uniform scale)\n"
        "preserves angles, so forwarding decisions remain well-defined\n"
        "without a geographically anchored frame.",
        ha="center",
        va="top",
        fontsize=8.5,
        color="#333333",
    )
    ax.text(
        5.0,
        1.15,
        "GPS STATUS: DENIED     RELATIVE MAP: ACTIVE",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#8b3a2a",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#fff6f0", edgecolor="#8b3a2a"),
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=180, bbox_inches="tight")
    plt.close(fig)


def print_banner(layout, route_ref, route_rel) -> None:
    print("=" * 64)
    print("GPS STATUS: DENIED")
    print("RELATIVE MAP: ACTIVE")
    print("=" * 64)
    print(f"Nodes: {layout.n_nodes}   seed: {layout.seed}   connected: {layout.connected}")
    print(f"Source: {route_rel.src}   Destination: {route_rel.dest}")
    print(f"PACKET: {format_path(route_rel.path, dest=route_rel.dest)}")
    print()
    print(f"Packet {'delivered' if route_rel.delivered else route_rel.status}")
    print(f"Hops: {route_rel.hop_count}")
    print(f"Reference-route hops: {route_ref.hop_count} ({route_ref.status})")
    stretch = route_rel.stretch if np.isfinite(route_rel.stretch) else float("nan")
    print(f"Route stretch: {stretch:.3f}" if np.isfinite(stretch) else "Route stretch: n/a")
    print("Absolute GPS coordinates used: NO")
    print("=" * 64)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    draw_concept_figure(FIGS / "figA_gps_denied_concept.png")

    rng = np.random.default_rng()
    seed = int(args.seed) if args.seed is not None else int(rng.integers(0, 2**31))
    layout, pairs, hop_dist, routes = build_and_route(
        args.n, seed, args.pairs, k_neighbors=10
    )
    layout.deny_gps()

    # GPS-denied campaign: route with relative map after absolute coords are unused.
    rel_metrics = routing_metrics(routes["C_mds_attraction"])
    ref_metrics = routing_metrics(routes["A_reference"])
    mds_metrics = routing_metrics(routes["B_mds_only"])

    # Prefer a moderately long delivered route; pick a new pair each run.
    delivered_rel = [r for r in routes["C_mds_attraction"] if r.delivered and r.hop_count >= 5]
    if not delivered_rel:
        delivered_rel = [r for r in routes["C_mds_attraction"] if r.delivered]
    example = (
        delivered_rel[int(rng.integers(0, len(delivered_rel)))]
        if delivered_rel
        else routes["C_mds_attraction"][0]
    )
    example_ref = greedy_route(
        example.src, example.dest, layout.reference, layout.radio_ids, hop_dist=hop_dist
    )
    print_banner(layout, example_ref, example)

    print("\nPhase 1  GPS / reference available as ground truth only")
    print(f"  Reference PDR={ref_metrics['pdr']:.3f}  stretch={ref_metrics['mean_stretch_delivered']:.3f}")
    print("Phase 2  GPS DENIED — forwarding uses the relative map")
    print(f"  Relative  PDR={rel_metrics['pdr']:.3f}  stretch={rel_metrics['mean_stretch_delivered']:.3f}")
    print(f"  MDS-only  PDR={mds_metrics['pdr']:.3f}  stretch={mds_metrics['mean_stretch_delivered']:.3f}")

    summary = pd.DataFrame(
        [
            {"phase": "GPS_available_ground_truth", "case": "A_reference", **ref_metrics},
            {"phase": "GPS_denied", "case": "B_mds_only", **mds_metrics},
            {"phase": "GPS_denied", "case": "C_mds_attraction", **rel_metrics},
        ]
    )
    out_csv = RESULTS / "gps_denied_demo_summary.csv"
    summary.to_csv(out_csv, index=False)
    print("\nWrote:")
    print(" ", FIGS / "figA_gps_denied_concept.png")
    print(" ", out_csv)


if __name__ == "__main__":
    main()
