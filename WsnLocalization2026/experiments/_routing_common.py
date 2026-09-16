"""Shared helpers for GPS-denied routing experiments."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.greedy_directional_routing import greedy_route, hop_distance_matrix
from src.relative_localization import NetworkLayout, build_layout, embed_relative_map

RESULTS = ROOT / "Results"
FIGS = RESULTS / "figures"

CASES = (
    ("reference", "A_reference"),
    ("mds", "B_mds_only"),
    ("relative", "C_mds_attraction"),
)


def ensure_dirs() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)


def prepared_layout(n_nodes: int, seed: int, k_neighbors: int = 10) -> NetworkLayout:
    layout = build_layout(n_nodes=n_nodes, seed=seed, k_neighbors=k_neighbors)
    return embed_relative_map(layout, seed=seed)


def sample_pairs(
    n: int,
    n_pairs: int,
    rng: np.random.Generator,
    hop_dist: np.ndarray,
    min_hops: int = 2,
) -> List[Tuple[int, int]]:
    """Sample connected source–destination pairs with hop distance ≥ min_hops."""
    candidates = np.argwhere(hop_dist >= min_hops)
    if len(candidates) == 0:
        # fall back to any distinct pair in the same component
        candidates = np.argwhere(hop_dist > 0)
    if len(candidates) == 0:
        return []
    rng.shuffle(candidates)
    take = min(n_pairs, len(candidates))
    return [(int(a), int(b)) for a, b in candidates[:take]]


def route_cases(
    layout: NetworkLayout,
    pairs: Sequence[Tuple[int, int]],
    hop_dist: np.ndarray,
) -> dict:
    out = {}
    for key, name in CASES:
        coords = layout.routing_coords(key)
        ref = layout.reference if key != "reference" else None
        routes = [
            greedy_route(
                s,
                d,
                coords,
                layout.radio_ids,
                hop_dist=hop_dist,
                reference_coords=ref,
            )
            for s, d in pairs
        ]
        out[name] = routes
    return out


def build_and_route(n_nodes: int, seed: int, n_pairs: int, k_neighbors: int = 10):
    layout = prepared_layout(n_nodes, seed, k_neighbors)
    hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)
    rng = np.random.default_rng(10_000 + seed)
    pairs = sample_pairs(layout.n_nodes, n_pairs, rng, hop_dist)
    routes = route_cases(layout, pairs, hop_dist)
    return layout, pairs, hop_dist, routes
