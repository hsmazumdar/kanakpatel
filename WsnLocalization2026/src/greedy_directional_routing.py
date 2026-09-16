"""Minimal greedy directional forwarding in a relative (or reference) frame.

At current node u with destination d, forward to the neighbor v minimizing the
angular deviation between vectors u→v and u→d. Similarity transformations
(translation, rotation, uniform scale) preserve these angles, so a consistent
relative map is sufficient: absolute GPS coordinates are not required.

This router is intentionally simple. Dead ends, revisits, loops, hop limits and
disconnected pairs are recorded rather than repaired with perimeter routing.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import numpy as np


def angular_deviation_deg(
    origin: np.ndarray,
    neighbor: np.ndarray,
    destination: np.ndarray,
) -> float:
    """Unsigned angular error in degrees between origin→neighbor and origin→dest."""
    vn = neighbor - origin
    vd = destination - origin
    nn = float(np.linalg.norm(vn))
    nd = float(np.linalg.norm(vd))
    if nn < 1e-12 or nd < 1e-12:
        return 180.0 if nd >= 1e-12 else 0.0
    vn = vn / nn
    vd = vd / nd
    cosang = float(np.clip(np.dot(vn, vd), -1.0, 1.0))
    return float(np.degrees(np.arccos(cosang)))


def choose_next_hop(
    current: int,
    dest: int,
    coords: np.ndarray,
    neighbors: Sequence[Sequence[int]],
    forbidden: Optional[set] = None,
) -> tuple[Optional[int], float]:
    """Neighbor with minimum angular deviation to the destination bearing."""
    if current == dest:
        return dest, 0.0
    best = None
    best_err = float("inf")
    origin = coords[current]
    target = coords[dest]
    for v in neighbors[current]:
        v = int(v)
        if forbidden is not None and v in forbidden:
            continue
        err = angular_deviation_deg(origin, coords[v], target)
        if err < best_err:
            best_err = err
            best = v
    if best is None:
        return None, float("nan")
    return best, float(best_err)


def hop_distance_matrix(neighbors: Sequence[Sequence[int]], n: int) -> np.ndarray:
    """Unweighted BFS hop distances on the (possibly directed) neighbor graph."""
    dist = np.full((n, n), -1, dtype=np.int32)
    for src in range(n):
        dist[src, src] = 0
        q = deque([src])
        while q:
            u = q.popleft()
            for v in neighbors[u]:
                v = int(v)
                if dist[src, v] < 0:
                    dist[src, v] = dist[src, u] + 1
                    q.append(v)
    return dist


@dataclass
class RouteResult:
    src: int
    dest: int
    path: List[int]
    status: str
    hop_count: int
    shortest_hops: int
    stretch: float
    angles: List[float] = field(default_factory=list)
    next_hop_agreement: Optional[float] = None

    @property
    def delivered(self) -> bool:
        return self.status == "delivered"


def greedy_route(
    src: int,
    dest: int,
    coords: np.ndarray,
    neighbors: Sequence[Sequence[int]],
    max_hops: Optional[int] = None,
    hop_dist: Optional[np.ndarray] = None,
    reference_coords: Optional[np.ndarray] = None,
) -> RouteResult:
    """Greedy angular forwarding from src to dest.

    Status is one of: delivered, disconnected, dead_end, loop, hop_limit, same_node.
    """
    n = len(coords)
    if src == dest:
        return RouteResult(src, dest, [src], "same_node", 0, 0, float("nan"))

    shortest = -1
    if hop_dist is not None:
        shortest = int(hop_dist[src, dest])
    if shortest < 0:
        # Lazy connectivity check
        seen = {src}
        q = deque([src])
        parent = {src: -1}
        found = False
        while q:
            u = q.popleft()
            if u == dest:
                found = True
                break
            for v in neighbors[u]:
                v = int(v)
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    q.append(v)
        if not found:
            return RouteResult(src, dest, [src], "disconnected", 0, -1, float("nan"))
        # reconstruct hop length
        hops = 0
        cur = dest
        while parent[cur] >= 0:
            hops += 1
            cur = parent[cur]
        shortest = hops

    if max_hops is None:
        max_hops = max(n, 4 * max(shortest, 1))

    path = [src]
    visited = {src}
    angles: List[float] = []
    agree_hits = 0
    agree_n = 0
    current = src

    while current != dest:
        if len(path) - 1 >= max_hops:
            stretch = (len(path) - 1) / shortest if shortest > 0 else float("nan")
            return RouteResult(
                src, dest, path, "hop_limit", len(path) - 1, shortest, stretch, angles
            )
        nxt, err = choose_next_hop(current, dest, coords, neighbors, forbidden=None)
        if nxt is None:
            stretch = (len(path) - 1) / shortest if shortest > 0 else float("nan")
            return RouteResult(
                src, dest, path, "dead_end", len(path) - 1, shortest, stretch, angles
            )
        if nxt in visited:
            path.append(nxt)
            angles.append(err)
            stretch = (len(path) - 1) / shortest if shortest > 0 else float("nan")
            return RouteResult(
                src, dest, path, "loop", len(path) - 1, shortest, stretch, angles
            )
        if reference_coords is not None:
            ref_nxt, _ = choose_next_hop(
                current, dest, reference_coords, neighbors, forbidden=None
            )
            agree_n += 1
            if ref_nxt == nxt:
                agree_hits += 1
        path.append(nxt)
        angles.append(float(err) if np.isfinite(err) else float("nan"))
        visited.add(nxt)
        current = nxt

    hop_count = len(path) - 1
    stretch = hop_count / shortest if shortest > 0 else float("nan")
    agreement = (agree_hits / agree_n) if agree_n else None
    return RouteResult(
        src,
        dest,
        path,
        "delivered",
        hop_count,
        shortest,
        stretch,
        angles,
        agreement,
    )
