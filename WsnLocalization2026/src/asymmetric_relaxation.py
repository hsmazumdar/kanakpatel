"""One-sided relative-map constraint relaxation (asymmetric neighbor attraction).

Expected inter-node distance is treated as an upper bound. Only violated pairs
are updated, and only one endpoint moves per elementary update. The selected
violated edge is guaranteed to shorten locally; global convergence is not claimed.
"""
from __future__ import annotations

from typing import List, Sequence

import numpy as np


def relax_violated_edges(
    coords: np.ndarray,
    node_u: int,
    neighbor_ids: Sequence[int],
    expected: Sequence[float],
    beta: float,
) -> bool:
    """Move each violated neighbor of ``node_u`` toward ``node_u``.

    Returns True if at least one endpoint was moved.
    """
    moved = False
    pu = coords[node_u]
    for v, d_star in zip(neighbor_ids, expected):
        v = int(v)
        delta = pu - coords[v]
        current = float(np.linalg.norm(delta))
        if current <= float(d_star) or current < 1e-12:
            continue
        coords[v] = coords[v] + beta * delta
        moved = True
    return moved


def tick_asymmetric(
    coords: np.ndarray,
    stored_ids: List[np.ndarray],
    stored_dist: List[np.ndarray],
    sampled_nodes: np.ndarray,
    beta: float,
) -> bool:
    """One randomized relaxation tick. Returns True if no sampled pair moved."""
    idle = True
    for u in sampled_nodes:
        u = int(u)
        nbrs = stored_ids[u]
        if len(nbrs) == 0:
            continue
        if relax_violated_edges(coords, u, nbrs, stored_dist[u], beta):
            idle = False
    return idle


def uniform_normalize(
    coords: np.ndarray,
    canvas_w: float = 800.0,
    canvas_h: float = 800.0,
    span: float = 0.9,
) -> None:
    """Similarity (uniform-scale) canvas normalization. Preserves angles."""
    if len(coords) == 0:
        return
    min_xy = coords.min(axis=0)
    max_xy = coords.max(axis=0)
    cur = max_xy - min_xy
    if cur[0] <= 0 or cur[1] <= 0:
        return
    s = min(canvas_w, canvas_h) * span / max(cur[0], cur[1])
    center = (min_xy + max_xy) / 2.0
    target = np.array([canvas_w / 2.0, canvas_h / 2.0])
    coords[:] = (coords - center) * s + target
