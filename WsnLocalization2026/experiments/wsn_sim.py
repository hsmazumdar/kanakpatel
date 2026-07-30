"""
Headless WSN localization simulator mirroring WsnMap.cs (SIGMAPS distance-constraint mode).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple
import heapq

import numpy as np


@dataclass
class SimConfig:
    n_nodes: int = 100
    tx_pct: float = 15.0
    k_neighbors: int = 10
    attraction: float = 0.3
    canvas_w: int = 800
    canvas_h: int = 800
    nod_size: int = 20
    moves_per_tick: int = 100
    max_ticks: int = 250
    normalize_span: float = 0.9
    path_loss_eta: float = 2.5
    seed: int = 0
    # False matches WsnMap.cs (independent X/Y). True = similarity (uniform scale).
    uniform_normalize: bool = False
    # "random" | "scrambled_reference" | "mds" (classical MDS on expected distances)
    init_mode: str = "random"
    # If False, always run max_ticks (avoids premature hard-stop on collapsed maps).
    early_stop: bool = True


def _mds_from_constraints(
    n: int, dst_id: List[np.ndarray], dst_val: List[np.ndarray]
) -> np.ndarray:
    """Classical MDS on shortest-path completion of expected neighbor distances."""
    # Dijkstra APSP (sparse); avoids O(N^3) Floyd–Warshall for large N.
    adj: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
    for i, nbrs in enumerate(dst_id):
        for k, j in enumerate(nbrs):
            j = int(j)
            d = float(dst_val[i][k])
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
    dist = np.where(np.isfinite(dist), dist, fill)
    jmat = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * jmat @ (dist ** 2) @ jmat
    evals, evecs = np.linalg.eigh(b)
    order = np.argsort(evals)[::-1][:2]
    coords = evecs[:, order] * np.sqrt(np.maximum(evals[order], 0.0))
    return coords


@dataclass
class SimResult:
    n_nodes: int
    tx_pct: float
    k_neighbors: int
    seed: int
    tx_distance: float
    density: float
    mean_degree: float
    min_degree: int
    max_degree: int
    isolated_nodes: int
    n_components: int
    connected: bool
    converged: bool
    ticks: int
    mean_constraint_violation: float
    procrustes_rmse: float
    tx_energy_proxy: float
    spacing_approx: float
    r_over_s: float


def _populate_nodes(cfg: SimConfig, rng: np.random.Generator) -> np.ndarray:
    margin = cfg.nod_size
    usable_w = cfg.canvas_w - margin
    usable_h = cfg.canvas_h - margin
    if usable_w <= 0 or usable_h <= 0:
        return np.zeros((0, 2), dtype=np.float64)

    grid_cols = int(math.ceil(math.sqrt(cfg.n_nodes)))
    grid_rows = int(math.ceil(cfg.n_nodes / grid_cols))
    cell_w = usable_w / grid_cols
    cell_h = usable_h / grid_rows

    nodes = np.zeros((cfg.n_nodes, 2), dtype=np.float64)
    idx = 0
    for row in range(grid_rows):
        for col in range(grid_cols):
            if idx >= cfg.n_nodes:
                break
            x = -margin + col * cell_w + rng.random() * cell_w
            y = -margin + row * cell_h + rng.random() * cell_h
            node_x = max(margin, min(cfg.canvas_w - margin - 1, int(x)))
            node_y = max(margin, min(cfg.canvas_h - margin - 1, int(y)))
            nodes[idx] = (node_x, node_y)
            idx += 1
    return nodes


def _tx_distance(cfg: SimConfig) -> float:
    diag = math.sqrt(cfg.canvas_w ** 2 + cfg.canvas_h ** 2)
    return (cfg.tx_pct / 100.0) * diag


def _build_distance_matrix(
    reference: np.ndarray, tx_dist: float, k: int
) -> Tuple[List[np.ndarray], List[np.ndarray], np.ndarray]:
    n = len(reference)
    degrees = np.zeros(n, dtype=np.int32)
    dst_val: List[np.ndarray] = []
    dst_id: List[np.ndarray] = []

    # Pairwise distances once
    diff = reference[:, None, :] - reference[None, :, :]
    dist = np.sqrt((diff ** 2).sum(axis=2))
    np.fill_diagonal(dist, np.inf)

    for i in range(n):
        mask = dist[i] <= tx_dist
        nbr_ids = np.where(mask)[0]
        degrees[i] = len(nbr_ids)
        if len(nbr_ids) == 0:
            dst_val.append(np.zeros(0, dtype=np.float64))
            dst_id.append(np.zeros(0, dtype=np.int32))
            continue
        order = np.argsort(dist[i, nbr_ids])
        nbr_ids = nbr_ids[order][:k]
        dst_id.append(nbr_ids.astype(np.int32))
        dst_val.append(dist[i, nbr_ids].astype(np.float64))
    return dst_val, dst_id, degrees


def _connected_components(dst_id: List[np.ndarray], n: int) -> int:
    parent = np.arange(n)

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = int(parent[a])
        return a

    for i, nbrs in enumerate(dst_id):
        for j in nbrs:
            ra, rb = find(i), find(int(j))
            if ra != rb:
                parent[rb] = ra
    return len({find(i) for i in range(n)})


def _normalize(nodes: np.ndarray, cfg: SimConfig) -> None:
    if len(nodes) == 0:
        return
    min_xy = nodes.min(axis=0)
    max_xy = nodes.max(axis=0)
    cur_w = max_xy[0] - min_xy[0]
    cur_h = max_xy[1] - min_xy[1]
    if cur_w <= 0 or cur_h <= 0:
        return
    if cfg.uniform_normalize:
        # Similarity: one scale from the larger span (preserves angles).
        span = max(cur_w, cur_h)
        target = min(cfg.canvas_w, cfg.canvas_h) * cfg.normalize_span
        s = target / span
        scale = np.array([s, s])
    else:
        # GUI / density–Tx default: independent axes (WsnMap.cs).
        scale = np.array(
            [
                (cfg.canvas_w * cfg.normalize_span) / cur_w,
                (cfg.canvas_h * cfg.normalize_span) / cur_h,
            ]
        )
    center = (min_xy + max_xy) / 2.0
    target_c = np.array([cfg.canvas_w / 2.0, cfg.canvas_h / 2.0])
    offset = target_c - center * scale
    nodes[:] = nodes * scale + offset


def _tick(
    localized: np.ndarray,
    seq: np.ndarray,
    ref_map: np.ndarray,
    dst_val: List[np.ndarray],
    dst_id: List[np.ndarray],
    attraction: float,
    indices: np.ndarray,
) -> bool:
    """One localization tick over pre-drawn node indices. True if no moves needed."""
    finish = True
    for array_index in indices:
        seq_no = int(seq[array_index])
        nbr_val = dst_val[seq_no]
        nbr_id = dst_id[seq_no]
        if len(nbr_id) == 0:
            continue
        selected = localized[array_index]
        for k in range(len(nbr_id)):
            neighbor_idx = int(ref_map[int(nbr_id[k])])
            neighbor_pos = localized[neighbor_idx]
            expected = nbr_val[k]
            dx = selected[0] - neighbor_pos[0]
            dy = selected[1] - neighbor_pos[1]
            current = math.sqrt(dx * dx + dy * dy)
            if current <= expected:
                continue
            finish = False
            localized[neighbor_idx, 0] = neighbor_pos[0] + attraction * dx
            localized[neighbor_idx, 1] = neighbor_pos[1] + attraction * dy
    return finish


def _mean_violation(
    localized: np.ndarray,
    seq: np.ndarray,
    ref_map: np.ndarray,
    dst_val: List[np.ndarray],
    dst_id: List[np.ndarray],
) -> float:
    total = 0.0
    count = 0
    for i in range(len(localized)):
        seq_no = int(seq[i])
        selected = localized[i]
        for k in range(len(dst_id[seq_no])):
            neighbor_idx = int(ref_map[int(dst_id[seq_no][k])])
            expected = float(dst_val[seq_no][k])
            d = float(np.linalg.norm(selected - localized[neighbor_idx]))
            total += max(0.0, d - expected)
            count += 1
    return total / count if count else 0.0


def _procrustes_align(
    reference: np.ndarray, localized: np.ndarray, ref_map: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Similarity-align localized[ref_map] to reference.
    Returns (ref_centered, aligned_localized_centered, rmse).
    """
    loc = localized[ref_map].astype(np.float64)
    ref = reference.astype(np.float64)
    ref_c = ref - ref.mean(axis=0)
    loc_c = loc - loc.mean(axis=0)
    h = loc_c.T @ ref_c
    u, s, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt = vt.copy()
        vt[-1, :] *= -1
        r = vt.T @ u.T
    scale = s.sum() / (np.sum(loc_c ** 2) + 1e-12)
    aligned = scale * (loc_c @ r.T)
    rmse = float(np.sqrt(np.mean(np.sum((aligned - ref_c) ** 2, axis=1))))
    return ref_c, aligned, rmse


def _procrustes_rmse(
    reference: np.ndarray, localized: np.ndarray, ref_map: np.ndarray
) -> float:
    _, _, rmse = _procrustes_align(reference, localized, ref_map)
    return rmse


@dataclass
class DetailedSimResult:
    summary: SimResult
    reference: np.ndarray
    localized: np.ndarray
    seq: np.ndarray
    ref_map: np.ndarray
    dst_id: List[np.ndarray]
    dst_val: List[np.ndarray]


def run_trial_detailed(cfg: SimConfig) -> DetailedSimResult:
    rng = np.random.default_rng(cfg.seed)
    reference = _populate_nodes(cfg, rng)
    seq = rng.permutation(cfg.n_nodes).astype(np.int32)
    ref_map = np.empty(cfg.n_nodes, dtype=np.int32)
    ref_map[seq] = np.arange(cfg.n_nodes, dtype=np.int32)

    tx_dist = _tx_distance(cfg)
    dst_val, dst_id, _ = _build_distance_matrix(reference, tx_dist, cfg.k_neighbors)

    if cfg.init_mode == "scrambled_reference":
        localized = reference[rng.permutation(cfg.n_nodes)].copy()
    elif cfg.init_mode == "mds":
        # MDS coords are in reference-node order; place into localized slots via ref_map.
        mds = _mds_from_constraints(cfg.n_nodes, dst_id, dst_val)
        mds = mds - mds.mean(axis=0)
        scale = max(np.abs(mds).max(), 1e-9)
        target = 0.35 * min(cfg.canvas_w, cfg.canvas_h)
        mds = mds / scale * target
        center = np.array([cfg.canvas_w / 2.0, cfg.canvas_h / 2.0])
        mds = mds + center
        localized = np.zeros_like(reference)
        for ref_i in range(cfg.n_nodes):
            localized[int(ref_map[ref_i])] = mds[ref_i]
    else:
        localized = _populate_nodes(cfg, rng)

    stored_deg = np.array([len(x) for x in dst_id], dtype=np.int32)
    n_comp = _connected_components(dst_id, cfg.n_nodes)
    area = float(cfg.canvas_w * cfg.canvas_h)
    density = cfg.n_nodes / area
    spacing = math.sqrt(area / cfg.n_nodes)

    converged = False
    ticks = 0
    for t in range(cfg.max_ticks):
        indices = rng.integers(0, cfg.n_nodes, size=cfg.moves_per_tick)
        finish = _tick(localized, seq, ref_map, dst_val, dst_id, cfg.attraction, indices)
        _normalize(localized, cfg)
        ticks = t + 1
        if cfg.early_stop and finish:
            converged = True
            break
    if not cfg.early_stop:
        indices = rng.integers(0, cfg.n_nodes, size=cfg.moves_per_tick)
        converged = _tick(
            localized.copy(), seq, ref_map, dst_val, dst_id, cfg.attraction, indices
        )

    viol = _mean_violation(localized, seq, ref_map, dst_val, dst_id)
    rmse = _procrustes_rmse(reference, localized, ref_map)
    diag = math.sqrt(cfg.canvas_w ** 2 + cfg.canvas_h ** 2)
    energy = (tx_dist / diag) ** cfg.path_loss_eta

    summary = SimResult(
        n_nodes=cfg.n_nodes,
        tx_pct=cfg.tx_pct,
        k_neighbors=cfg.k_neighbors,
        seed=cfg.seed,
        tx_distance=tx_dist,
        density=density,
        mean_degree=float(stored_deg.mean()) if len(stored_deg) else 0.0,
        min_degree=int(stored_deg.min()) if len(stored_deg) else 0,
        max_degree=int(stored_deg.max()) if len(stored_deg) else 0,
        isolated_nodes=int(np.sum(stored_deg == 0)),
        n_components=n_comp,
        connected=(n_comp == 1 and int(np.sum(stored_deg == 0)) == 0),
        converged=converged,
        ticks=ticks,
        mean_constraint_violation=viol,
        procrustes_rmse=rmse,
        tx_energy_proxy=float(energy),
        spacing_approx=spacing,
        r_over_s=(tx_dist / spacing) if spacing > 0 else 0.0,
    )
    return DetailedSimResult(
        summary=summary,
        reference=reference,
        localized=localized,
        seq=seq,
        ref_map=ref_map,
        dst_id=dst_id,
        dst_val=dst_val,
    )


def run_trial(cfg: SimConfig) -> SimResult:
    return run_trial_detailed(cfg).summary
