"""
Dynamic GPS-denied routing visualization.

Each animated trial uses a different source–destination pair. The window cycles
through several packets instead of looping one route.

Qualitative GitHub demo only — not scientific validation.

  python demo/dynamic_gps_denied_routing.py
  python demo/dynamic_gps_denied_routing.py --trials 12
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.greedy_directional_routing import RouteResult, greedy_route, hop_distance_matrix
from src.metrics import format_path
from src.relative_localization import build_layout, embed_relative_map


@dataclass
class Trial:
    src: int
    dest: int
    rel: RouteResult
    ref: RouteResult


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animate GPS-denied greedy forwarding.")
    p.add_argument("--n", type=int, default=80)
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Layout seed. Omit to draw a new network each run.",
    )
    p.add_argument("--src", type=int, default=-1, help="Pin source (disables multi-trial).")
    p.add_argument("--dest", type=int, default=-1, help="Pin destination (disables multi-trial).")
    p.add_argument("--trials", type=int, default=8, help="Distinct src/dst packets to animate.")
    p.add_argument("--motion", action="store_true", help="Slow bounded random walk.")
    p.add_argument("--save-gif", action="store_true")
    p.add_argument("--save-png", action="store_true", default=True)
    p.add_argument("--out-dir", type=str, default="")
    return p.parse_args()


def pick_pair(
    hop_dist: np.ndarray,
    rng: np.random.Generator,
    min_hops: int = 5,
    used: Optional[Set[Tuple[int, int]]] = None,
) -> Tuple[int, int]:
    cand = np.argwhere(hop_dist >= min_hops)
    if len(cand) == 0:
        cand = np.argwhere(hop_dist > 0)
    if len(cand) == 0:
        raise RuntimeError("No connected source-destination pair in this realization.")
    used = used or set()
    order = rng.permutation(len(cand))
    for i in order:
        src, dest = int(cand[i, 0]), int(cand[i, 1])
        if (src, dest) not in used and (dest, src) not in used:
            return src, dest
    src, dest = int(cand[int(order[0]), 0]), int(cand[int(order[0]), 1])
    return src, dest


def make_trial(layout, hop_dist, src: int, dest: int) -> Trial:
    rel = greedy_route(
        src,
        dest,
        layout.relative,
        layout.radio_ids,
        hop_dist=hop_dist,
        reference_coords=layout.reference,
    )
    ref = greedy_route(src, dest, layout.reference, layout.radio_ids, hop_dist=hop_dist)
    return Trial(src, dest, rel, ref)


def trial_footer(trial: Trial) -> str:
    stretch = trial.rel.stretch if trial.rel.stretch == trial.rel.stretch else float("nan")
    status = "Packet delivered" if trial.rel.delivered else "Packet: " + trial.rel.status
    stretch_s = f"{stretch:.3f}" if stretch == stretch else "n/a"
    return (
        f"{status}   Hops: {trial.rel.hop_count}   "
        f"Reference-route hops: {trial.ref.hop_count}   "
        f"Route stretch: {stretch_s}   Absolute GPS coordinates used: NO"
    )


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "Results" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    pair_rng = np.random.default_rng()
    layout_seed = int(args.seed) if args.seed is not None else int(pair_rng.integers(0, 2**31))
    layout = embed_relative_map(build_layout(n_nodes=args.n, seed=layout_seed))
    layout.deny_gps()
    hop_dist = hop_distance_matrix(layout.radio_ids, layout.n_nodes)

    pinned = args.src >= 0 and args.dest >= 0
    n_trials = 1 if pinned else max(1, args.trials)
    used: Set[Tuple[int, int]] = set()
    trials: List[Trial] = []
    for _ in range(n_trials):
        if pinned:
            src, dest = args.src, args.dest
        else:
            src, dest = pick_pair(hop_dist, pair_rng, used=used)
        used.add((src, dest))
        trials.append(make_trial(layout, hop_dist, src, dest))

    pts0 = layout.relative.copy()
    vel = pair_rng.normal(0.0, 0.35, size=pts0.shape) if args.motion else np.zeros_like(pts0)
    hold = 4
    schedule: List[Tuple[int, int]] = []
    for t_i, trial in enumerate(trials):
        last = max(len(trial.rel.path) - 1, 0)
        for hop in range(last + 1):
            schedule.append((t_i, hop))
        for _ in range(hold):
            schedule.append((t_i, last))

    fig, ax = plt.subplots(figsize=(7.4, 7.6))
    fig.subplots_adjust(top=0.88, bottom=0.16)

    def draw(frame: int):
        t_i, hop = schedule[int(frame) % len(schedule)]
        trial = trials[t_i]
        src, dest, rel = trial.src, trial.dest, trial.rel
        ax.clear()
        pts = pts0.copy()
        if args.motion:
            jitter = np.sin((frame + 1) * 0.15) * 4.5
            pts = pts0 + jitter * np.tanh(vel)
        for i, nbrs in enumerate(layout.radio_ids):
            for j in nbrs:
                j = int(j)
                if j <= i:
                    continue
                ax.plot(
                    [pts[i, 0], pts[j, 0]],
                    [pts[i, 1], pts[j, 1]],
                    color="#d5dbe0",
                    lw=0.5,
                    zorder=1,
                )
        ax.scatter(pts[:, 0], pts[:, 1], s=18, c="#5c6b75", zorder=2)
        walked = rel.path[: hop + 1]
        if len(walked) >= 2:
            xy = pts[np.array(walked)]
            ax.plot(xy[:, 0], xy[:, 1], color="#c0392b", lw=2.2, zorder=3)
        ax.scatter(*pts[src], s=90, c="#1f4e79", marker="s", zorder=5, label="SOURCE")
        ax.scatter(*pts[dest], s=140, c="#117a3a", marker="*", zorder=5, label="DESTINATION")
        if walked:
            ax.scatter(*pts[walked[-1]], s=55, c="#c0392b", zorder=6)
        angle = rel.angles[hop - 1] if hop > 0 and hop - 1 < len(rel.angles) else 0.0
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.legend(loc="lower right", fontsize=8)
        ax.set_title(
            "GPS STATUS: DENIED      RELATIVE MAP: ACTIVE\n"
            f"Trial {t_i + 1}/{len(trials)}   {src} -> {dest}\n"
            f"PACKET: {format_path(walked, dest=dest if walked and walked[-1] == dest else None)}",
            fontsize=10,
            loc="left",
            color="#8b3a2a",
        )
        if hop > 0 and walked:
            ax.text(
                0.02,
                0.06,
                f"hop {hop}   chosen={walked[-1]}   angular error={angle:.1f}°",
                transform=ax.transAxes,
                fontsize=8,
                color="#333333",
            )
        ax.text(0.5, -0.08, trial_footer(trial), transform=ax.transAxes, ha="center", fontsize=8.5)

    anim = FuncAnimation(fig, draw, frames=len(schedule), interval=450, repeat=True)

    last_i = len(trials) - 1
    draw(schedule.index((last_i, max(len(trials[last_i].rel.path) - 1, 0))))
    png_path = out_dir / "demo_gps_denied_snapshot.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight")

    print("GPS STATUS: DENIED")
    print("RELATIVE MAP: ACTIVE")
    print(f"layout seed={layout_seed}  trials={len(trials)}")
    for i, trial in enumerate(trials, start=1):
        print(
            f"  trial {i}: {trial.src} -> {trial.dest}  "
            f"PACKET: {format_path(trial.rel.path, dest=trial.dest)}"
        )
        print("   ", trial_footer(trial))
    print("Wrote", png_path)

    if args.save_gif:
        gif_path = out_dir / "demo_gps_denied_routing.gif"
        try:
            anim.save(str(gif_path), writer=PillowWriter(fps=2))
            print("Wrote", gif_path)
        except Exception as exc:  # noqa: BLE001
            print("GIF not written:", exc)

    if not args.save_gif:
        try:
            plt.show()
        except Exception:
            plt.close(fig)
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
