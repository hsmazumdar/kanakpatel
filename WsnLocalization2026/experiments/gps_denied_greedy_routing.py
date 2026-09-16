"""Thin CLI wrapper: greedy directional routing on a GPS-denied relative map."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _routing_common import prepared_layout
from src.greedy_directional_routing import greedy_route, hop_distance_matrix
from src.metrics import format_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run one greedy directional route in the relative coordinate frame."
    )
    p.add_argument("--n", type=int, default=120)
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Layout seed. Omit to draw a new network each run.",
    )
    p.add_argument("--src", type=int, default=-1)
    p.add_argument("--dest", type=int, default=-1)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng()
    seed = int(args.seed) if args.seed is not None else int(rng.integers(0, 2**31))
    layout = prepared_layout(args.n, seed)
    layout.deny_gps()
    hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
    if args.src < 0 or args.dest < 0:
        cand = np.argwhere(hop_dist >= 5)
        if len(cand) == 0:
            cand = np.argwhere(hop_dist > 0)
        src, dest = (int(x) for x in cand[int(rng.integers(0, len(cand)))])
    else:
        src, dest = args.src, args.dest
    print(f"layout seed={seed}  source={src}  destination={dest}")
    rel = greedy_route(
        src,
        dest,
        layout.relative,
        layout.radio_ids,
        hop_dist=hop_dist,
        reference_coords=layout.reference,
    )
    ref = greedy_route(src, dest, layout.reference, layout.radio_ids, hop_dist=hop_dist)
    print("GPS STATUS: DENIED")
    print("RELATIVE MAP: ACTIVE")
    print(f"PACKET: {format_path(rel.path, dest=dest)}")
    print(f"status={rel.status} hops={rel.hop_count} reference_hops={ref.hop_count}")
    if rel.stretch == rel.stretch:
        print(f"stretch={rel.stretch:.3f}")
    else:
        print("stretch=n/a")
    print("Absolute GPS coordinates used: NO")


if __name__ == "__main__":
    main()
