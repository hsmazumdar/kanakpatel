"""Classical multidimensional scaling for relative-map initialization."""
from __future__ import annotations

import heapq
from typing import List, Sequence, Tuple

import numpy as np


def shortest_path_completion(
    n: int,
    neighbor_ids: Sequence[np.ndarray],
    neighbor_dist: Sequence[np.ndarray],
) -> np.ndarray:
    """All-pairs shortest paths on the undirected expected-distance graph."""
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for i, nbrs in enumerate(neighbor_ids):
        for k, j in enumerate(nbrs):
            j = int(j)
            d = float(neighbor_dist[i][k])
            adj[i].append((j, d))
            adj[j].append((i, d))

    dist = np.full((n, n), np.inf, dtype=np.float64)
    for src in range(n):
        dist[src, src] = 0.0
        heap: List[Tuple[float, int]] = [(0.0, src)]
        while heap:
            du, u = heapq.heappop(heap)
            if du > dist[src, u]:
                continue
            for v, w in adj[u]:
                nd = du + w
                if nd < dist[src, v]:
                    dist[src, v] = nd
                    heapq.heappush(heap, (nd, v))

    finite = dist[np.isfinite(dist)]
    fill = float(np.max(finite) * 1.5) if len(finite) else 1.0
    return np.where(np.isfinite(dist), dist, fill)


def classical_mds(dist: np.ndarray, dim: int = 2) -> np.ndarray:
    """Classical MDS embedding of a complete distance matrix."""
    n = dist.shape[0]
    jmat = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * jmat @ (dist ** 2) @ jmat
    evals, evecs = np.linalg.eigh(b)
    order = np.argsort(evals)[::-1][:dim]
    coords = evecs[:, order] * np.sqrt(np.maximum(evals[order], 0.0))
    return coords


def mds_from_neighbor_distances(
    neighbor_ids: Sequence[np.ndarray],
    neighbor_dist: Sequence[np.ndarray],
) -> np.ndarray:
    """Classical MDS on shortest-path completion of stored expected distances."""
    n = len(neighbor_ids)
    completed = shortest_path_completion(n, neighbor_ids, neighbor_dist)
    return classical_mds(completed, dim=2)
