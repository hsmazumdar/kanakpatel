"""Build a planned-geometry WSN layout and a reference-free relative map.

GPS / absolute coordinates are used only as simulation ground truth. The relative
map is formed from expected-distance upper bounds and does not consume GPS
positions as routing coordinates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .asymmetric_relaxation import tick_asymmetric, uniform_normalize
from .mds_initialization import mds_from_neighbor_distances


@dataclass
class NetworkLayout:
    n_nodes: int
    seed: int
    tx_pct: float
    k_neighbors: int
    canvas_w: int
    canvas_h: int
    reference: np.ndarray
    stored_ids: List[np.ndarray]
    stored_dist: List[np.ndarray]
    radio_ids: List[np.ndarray]
    spacing: float
    connected: bool
    mds: Optional[np.ndarray] = None
    relative: Optional[np.ndarray] = None
    gps_available: bool = True
    obstacles: List[tuple] = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def deny_gps(self) -> None:
        """Remove absolute coordinates from the routing process (simulation hook)."""
        self.gps_available = False

    def routing_coords(self, case: str) -> np.ndarray:
        case = case.lower()
        if case in ("reference", "gps", "a"):
            if self.reference is None:
                raise RuntimeError("Reference coordinates are unavailable.")
            return self.reference
        if case in ("mds", "mds-only", "b"):
            if self.mds is None:
                raise RuntimeError("MDS coordinates have not been computed.")
            return self.mds
        if case in ("relative", "attraction", "mds+attraction", "c"):
            if self.relative is None:
                raise RuntimeError("Relative-map coordinates have not been computed.")
            return self.relative
        raise ValueError(f"Unknown coordinate case: {case}")


def tx_distance(tx_pct: float, canvas_w: int = 800, canvas_h: int = 800) -> float:
    diag = math.sqrt(canvas_w ** 2 + canvas_h ** 2)
    return (tx_pct / 100.0) * diag


def tx_pct_for_density(n: int, canvas: int = 800, range_factor: float = 2.8) -> float:
    diag = math.sqrt(2 * canvas * canvas)
    spacing = math.sqrt((canvas * canvas) / n)
    r = range_factor * spacing
    return float(np.clip(100.0 * r / diag, 5.0, 45.0))


def populate_grid_jitter(
    n: int,
    rng: np.random.Generator,
    canvas_w: int = 800,
    canvas_h: int = 800,
    nod_size: int = 20,
) -> np.ndarray:
    margin = nod_size
    usable_w = canvas_w - margin
    usable_h = canvas_h - margin
    grid_cols = int(math.ceil(math.sqrt(n)))
    grid_rows = int(math.ceil(n / grid_cols))
    cell_w = usable_w / grid_cols
    cell_h = usable_h / grid_rows
    nodes = np.zeros((n, 2), dtype=np.float64)
    idx = 0
    for row in range(grid_rows):
        for col in range(grid_cols):
            if idx >= n:
                break
            x = -margin + col * cell_w + rng.random() * cell_w
            y = -margin + row * cell_h + rng.random() * cell_h
            nodes[idx, 0] = max(margin, min(canvas_w - margin - 1, x))
            nodes[idx, 1] = max(margin, min(canvas_h - margin - 1, y))
            idx += 1
    return nodes


def default_center_void(canvas_w: int = 800, canvas_h: int = 800) -> List[tuple]:
    """A wide central rectangle that forces detours (classic greedy-void geometry)."""
    return [
        (
            0.28 * canvas_w,
            0.34 * canvas_h,
            0.72 * canvas_w,
            0.66 * canvas_h,
        )
    ]


def _point_in_rect(pt: np.ndarray, rect: tuple) -> bool:
    x0, y0, x1, y1 = rect
    return x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1


def _orient(a, b, c) -> float:
    return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])


def _seg_intersect(p, q, a, b) -> bool:
    o1 = _orient(p, q, a)
    o2 = _orient(p, q, b)
    o3 = _orient(a, b, p)
    o4 = _orient(a, b, q)
    if o1 == 0 and o2 == 0 and o3 == 0 and o4 == 0:
        return False
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def segment_hits_obstacles(p: np.ndarray, q: np.ndarray, obstacles: List[tuple]) -> bool:
    for rect in obstacles:
        x0, y0, x1, y1 = rect
        if _point_in_rect(p, rect) or _point_in_rect(q, rect):
            return True
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for i in range(4):
            if _seg_intersect(p, q, corners[i], corners[(i + 1) % 4]):
                return True
    return False


def populate_grid_jitter_free(
    n: int,
    rng: np.random.Generator,
    canvas_w: int = 800,
    canvas_h: int = 800,
    nod_size: int = 20,
    obstacles: Optional[List[tuple]] = None,
) -> np.ndarray:
    """Grid-with-jitter placement that rejects samples inside obstacle rectangles."""
    obstacles = obstacles or []
    if not obstacles:
        return populate_grid_jitter(n, rng, canvas_w, canvas_h, nod_size)
    margin = nod_size
    nodes = np.zeros((n, 2), dtype=np.float64)
    filled = 0
    attempts = 0
    limit = n * 80
    while filled < n and attempts < limit:
        attempts += 1
        x = margin + rng.random() * (canvas_w - 2 * margin)
        y = margin + rng.random() * (canvas_h - 2 * margin)
        pt = np.array([x, y])
        if any(_point_in_rect(pt, r) for r in obstacles):
            continue
        nodes[filled] = pt
        filled += 1
    if filled < n:
        raise RuntimeError("Could not place requested nodes outside obstacles.")
    return nodes


def _pairwise_dist(pts: np.ndarray) -> np.ndarray:
    diff = pts[:, None, :] - pts[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    np.fill_diagonal(dist, np.inf)
    return dist


def build_neighbor_tables(
    reference: np.ndarray,
    tx_dist: float,
    k: int,
    obstacles: Optional[List[tuple]] = None,
) -> tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray]]:
    """Return (stored k-NN ids, stored distances, unit-disk radio neighbor ids)."""
    n = len(reference)
    dist = _pairwise_dist(reference)
    stored_ids: List[np.ndarray] = []
    stored_dist: List[np.ndarray] = []
    radio_ids: List[np.ndarray] = []
    obstacles = obstacles or []
    for i in range(n):
        mask = dist[i] <= tx_dist
        nbrs = np.where(mask)[0]
        if obstacles:
            keep = []
            for j in nbrs:
                if not segment_hits_obstacles(reference[i], reference[int(j)], obstacles):
                    keep.append(int(j))
            nbrs = np.asarray(keep, dtype=np.int32)
        radio_ids.append(nbrs.astype(np.int32))
        if len(nbrs) == 0:
            stored_ids.append(np.zeros(0, dtype=np.int32))
            stored_dist.append(np.zeros(0, dtype=np.float64))
            continue
        order = np.argsort(dist[i, nbrs])
        kept = nbrs[order][:k]
        stored_ids.append(np.asarray(kept, dtype=np.int32))
        stored_dist.append(dist[i, kept].astype(np.float64))
    return stored_ids, stored_dist, radio_ids


def _connected(radio_ids: List[np.ndarray], n: int) -> bool:
    parent = np.arange(n)

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = int(parent[a])
        return a

    for i, nbrs in enumerate(radio_ids):
        for j in nbrs:
            ra, rb = find(i), find(int(j))
            if ra != rb:
                parent[rb] = ra
    roots = {find(i) for i in range(n)}
    isolates = sum(1 for nbrs in radio_ids if len(nbrs) == 0)
    return len(roots) == 1 and isolates == 0


def build_layout(
    n_nodes: int = 250,
    seed: int = 0,
    k_neighbors: int = 10,
    tx_pct: Optional[float] = None,
    canvas_w: int = 800,
    canvas_h: int = 800,
    obstacles: Optional[List[tuple]] = None,
    range_factor: float = 2.8,
) -> NetworkLayout:
    rng = np.random.default_rng(seed)
    obstacles = list(obstacles) if obstacles else []
    if tx_pct is None:
        tx_pct = tx_pct_for_density(n_nodes, canvas=canvas_w, range_factor=range_factor)
    reference = populate_grid_jitter_free(
        n_nodes, rng, canvas_w, canvas_h, obstacles=obstacles
    )
    tx_dist = tx_distance(tx_pct, canvas_w, canvas_h)
    stored_ids, stored_dist, radio_ids = build_neighbor_tables(
        reference, tx_dist, k_neighbors, obstacles=obstacles
    )
    area = float(canvas_w * canvas_h)
    spacing = math.sqrt(area / n_nodes)
    return NetworkLayout(
        n_nodes=n_nodes,
        seed=seed,
        tx_pct=float(tx_pct),
        k_neighbors=k_neighbors,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        reference=reference,
        stored_ids=stored_ids,
        stored_dist=stored_dist,
        radio_ids=radio_ids,
        spacing=spacing,
        connected=_connected(radio_ids, n_nodes),
        gps_available=True,
        obstacles=obstacles,
        notes={"tx_distance": tx_dist, "n_obstacles": len(obstacles)},
    )


def embed_relative_map(
    layout: NetworkLayout,
    attraction: float = 0.3,
    moves_per_tick: int = 200,
    max_ticks: int = 150,
    seed: Optional[int] = None,
    normalize: bool = True,
) -> NetworkLayout:
    """Form MDS-only and MDS+attraction relative maps. GPS is not an input."""
    rng = np.random.default_rng(layout.seed if seed is None else seed)
    mds = mds_from_neighbor_distances(layout.stored_ids, layout.stored_dist)
    mds = mds - mds.mean(axis=0)
    scale = max(float(np.abs(mds).max()), 1e-9)
    target = 0.35 * min(layout.canvas_w, layout.canvas_h)
    mds = mds / scale * target
    center = np.array([layout.canvas_w / 2.0, layout.canvas_h / 2.0])
    mds = mds + center
    if normalize:
        uniform_normalize(mds, layout.canvas_w, layout.canvas_h)

    relative = mds.copy()
    for _ in range(max_ticks):
        indices = rng.integers(0, layout.n_nodes, size=moves_per_tick)
        tick_asymmetric(
            relative, layout.stored_ids, layout.stored_dist, indices, attraction
        )
        if normalize:
            uniform_normalize(relative, layout.canvas_w, layout.canvas_h)

    layout.mds = mds
    layout.relative = relative
    return layout


def perturb_coords(
    coords: np.ndarray,
    sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Isotropic Gaussian perturbation (absolute GPS is still not restored)."""
    if sigma <= 0:
        return coords.copy()
    return coords + rng.normal(0.0, sigma, size=coords.shape)
