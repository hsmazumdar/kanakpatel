"""
Reference-free relative localization and GPS-denied greedy directional routing.

In this package, *reference-free* means the absence of absolute geographic anchors
or a globally surveyed coordinate system. It does not imply absence of all
inter-node geometric information (planned-geometry expected distances are used
in the reported experiments).
"""

from .asymmetric_relaxation import relax_violated_edges, tick_asymmetric
from .greedy_directional_routing import greedy_route, angular_deviation_deg
from .mds_initialization import classical_mds, mds_from_neighbor_distances
from .metrics import routing_metrics, summarize_routes
from .relative_localization import NetworkLayout, build_layout, embed_relative_map

__all__ = [
    "NetworkLayout",
    "angular_deviation_deg",
    "build_layout",
    "classical_mds",
    "embed_relative_map",
    "greedy_route",
    "mds_from_neighbor_distances",
    "relax_violated_edges",
    "routing_metrics",
    "summarize_routes",
    "tick_asymmetric",
]
