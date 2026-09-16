"""Routing and directional-consistency metrics for GPS-denied forwarding."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np

from .greedy_directional_routing import RouteResult, choose_next_hop


def routing_metrics(routes: Sequence[RouteResult]) -> Dict[str, float]:
    """Aggregate packet-delivery and failure statistics over a route list."""
    usable = [r for r in routes if r.status != "same_node"]
    n = len(usable)
    if n == 0:
        return {
            "n_pairs": 0,
            "pdr": float("nan"),
            "mean_hops_delivered": float("nan"),
            "mean_stretch_delivered": float("nan"),
            "greedy_failure_rate": float("nan"),
            "loop_rate": float("nan"),
            "dead_end_rate": float("nan"),
            "hop_limit_rate": float("nan"),
            "disconnected_rate": float("nan"),
            "decision_agreement": float("nan"),
        }
    delivered = [r for r in usable if r.delivered]
    loops = sum(1 for r in usable if r.status == "loop")
    dead = sum(1 for r in usable if r.status == "dead_end")
    hop_lim = sum(1 for r in usable if r.status == "hop_limit")
    disc = sum(1 for r in usable if r.status == "disconnected")
    fail = loops + dead + hop_lim
    hops = [r.hop_count for r in delivered]
    stretch = [r.stretch for r in delivered if np.isfinite(r.stretch)]
    agrees = [r.next_hop_agreement for r in usable if r.next_hop_agreement is not None]
    return {
        "n_pairs": float(n),
        "pdr": len(delivered) / n,
        "mean_hops_delivered": float(np.mean(hops)) if hops else float("nan"),
        "mean_stretch_delivered": float(np.mean(stretch)) if stretch else float("nan"),
        "greedy_failure_rate": fail / n,
        "loop_rate": loops / n,
        "dead_end_rate": dead / n,
        "hop_limit_rate": hop_lim / n,
        "disconnected_rate": disc / n,
        "decision_agreement": float(np.mean(agrees)) if agrees else float("nan"),
    }


def summarize_routes(named: Dict[str, Sequence[RouteResult]]) -> List[dict]:
    rows = []
    for name, routes in named.items():
        row = {"case": name}
        row.update(routing_metrics(routes))
        rows.append(row)
    return rows


def sample_decision_agreement(
    coords_a: np.ndarray,
    coords_b: np.ndarray,
    neighbors: Sequence[Sequence[int]],
    pairs: Iterable[tuple[int, int]],
) -> float:
    """Fraction of (current, dest) pairs where A and B choose the same next hop."""
    hits = 0
    n = 0
    for u, d in pairs:
        if u == d:
            continue
        if len(neighbors[u]) == 0:
            continue
        a, _ = choose_next_hop(u, d, coords_a, neighbors)
        b, _ = choose_next_hop(u, d, coords_b, neighbors)
        n += 1
        if a is not None and a == b:
            hits += 1
    return hits / n if n else float("nan")


def format_path(path: Sequence[int], dest: Optional[int] = None) -> str:
    labels = [str(i) for i in path]
    if dest is not None and path and path[-1] == dest:
        labels[-1] = "DESTINATION"
    return " -> ".join(labels)
