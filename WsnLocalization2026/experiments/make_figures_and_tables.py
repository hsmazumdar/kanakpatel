"""
Post-process Results CSVs: soft convergence, paper tables, publication plots.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "Results"
FIGS = RESULTS / "figures"

# Soft success: residual constraint violation below threshold (pixels)
SOFT_VIOL_THRESH = 1.0
# Also require network was worth localizing (mean degree >= 6)
SOFT_MIN_DEGREE = 6.0


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RESULTS / "results_raw.csv")
    df["soft_converged"] = (
        (df["mean_constraint_violation"] <= SOFT_VIOL_THRESH)
        & (df["mean_degree"] >= SOFT_MIN_DEGREE)
        & (df["connected"] == 1)
    ).astype(int)
    # Trivial "hard converge" on near-empty graphs is not a localization success
    df["meaningful_hard"] = (
        (df["converged"] == 1) & (df["mean_degree"] >= SOFT_MIN_DEGREE) & (df["connected"] == 1)
    ).astype(int)
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["n_nodes", "tx_pct", "k_neighbors"], as_index=False).agg(
        n_trials=("seed", "count"),
        mean_degree_avg=("mean_degree", "mean"),
        mean_degree_std=("mean_degree", "std"),
        connected_rate=("connected", "mean"),
        hard_converge_rate=("converged", "mean"),
        meaningful_hard_rate=("meaningful_hard", "mean"),
        soft_converge_rate=("soft_converged", "mean"),
        ticks_avg=("ticks", "mean"),
        ticks_std=("ticks", "std"),
        rmse_avg=("procrustes_rmse", "mean"),
        rmse_std=("procrustes_rmse", "std"),
        violation_avg=("mean_constraint_violation", "mean"),
        r_over_s_avg=("r_over_s", "mean"),
        tx_energy_proxy=("tx_energy_proxy", "mean"),
        isolated_avg=("isolated_nodes", "mean"),
    )
    return g.round(
        {
            "mean_degree_avg": 3,
            "mean_degree_std": 3,
            "connected_rate": 3,
            "hard_converge_rate": 3,
            "meaningful_hard_rate": 3,
            "soft_converge_rate": 3,
            "ticks_avg": 1,
            "ticks_std": 1,
            "rmse_avg": 3,
            "rmse_std": 3,
            "violation_avg": 4,
            "r_over_s_avg": 4,
            "tx_energy_proxy": 6,
            "isolated_avg": 2,
        }
    )


def min_tx_table(summary: pd.DataFrame, target_degree: float, k: int = 10) -> pd.DataFrame:
    rows = []
    for n in sorted(summary["n_nodes"].unique()):
        cand = summary[
            (summary["n_nodes"] == n)
            & (summary["k_neighbors"] == k)
            & (summary["mean_degree_avg"] >= target_degree)
            & (summary["connected_rate"] >= 1.0)
        ]
        if cand.empty:
            rows.append(
                {
                    "n_nodes": n,
                    "k_neighbors": k,
                    "target_degree": target_degree,
                    "min_tx_pct": np.nan,
                    "tx_energy_proxy": np.nan,
                    "soft_converge_rate": np.nan,
                    "rmse_avg": np.nan,
                    "mean_degree_avg": np.nan,
                    "note": "no feasible tx in matrix",
                }
            )
            continue
        best = cand.loc[cand["tx_pct"].idxmin()]
        rows.append(
            {
                "n_nodes": int(n),
                "k_neighbors": k,
                "target_degree": target_degree,
                "min_tx_pct": best["tx_pct"],
                "tx_energy_proxy": best["tx_energy_proxy"],
                "soft_converge_rate": best["soft_converge_rate"],
                "rmse_avg": best["rmse_avg"],
                "mean_degree_avg": best["mean_degree_avg"],
                "note": "energy-optimal Tx for density",
            }
        )
    return pd.DataFrame(rows)


def write_paper_markdown(energy: pd.DataFrame, min8: pd.DataFrame, summary_k10: pd.DataFrame) -> None:
    area = 800 * 800
    lines = [
        "# Density vs Transmission Range — Experimental Tables",
        "",
        "Canvas fixed at 800×800. Soft converge: connected, mean degree ≥ 6, "
        f"constraint violation ≤ {SOFT_VIOL_THRESH} px.",
        "",
        "## Table 1. Energy-optimal Tx vs node density (k = 10, degree ≥ 8)",
        "",
        "| N | Density (nodes/px²) | Min Tx (% diag) | Tx energy proxy R^η | Soft converge | RMSE |",
        "|--:|--------------------:|----------------:|--------------------:|--------------:|-----:|",
    ]
    for _, r in energy.iterrows():
        dens = int(r["n_nodes"]) / area
        mtx = "" if pd.isna(r["min_tx_pct"]) else f"{r['min_tx_pct']:.0f}"
        en = "" if pd.isna(r["tx_energy_proxy"]) else f"{r['tx_energy_proxy']:.4f}"
        sc = "" if pd.isna(r["soft_converge_rate"]) else f"{r['soft_converge_rate']:.0%}"
        rm = "" if pd.isna(r["rmse_avg"]) else f"{r['rmse_avg']:.1f}"
        lines.append(
            f"| {int(r['n_nodes'])} | {dens:.2e} | {mtx} | {en} | {sc} | {rm} |"
        )

    lines += [
        "",
        "## Table 2. Min Tx for mean degree ≥ 8 (all k)",
        "",
        "| N | k | Min Tx% | Energy proxy | Soft converge | Mean degree |",
        "|--:|--:|--------:|-------------:|--------------:|------------:|",
    ]
    for _, r in min8.iterrows():
        if pd.isna(r["min_tx_pct"]):
            lines.append(
                f"| {int(r['n_nodes'])} | {int(r['k_neighbors'])} | — | — | — | — |"
            )
        else:
            lines.append(
                f"| {int(r['n_nodes'])} | {int(r['k_neighbors'])} | {r['min_tx_pct']:.0f} | "
                f"{r['tx_energy_proxy']:.4f} | {r['soft_converge_rate']:.0%} | {r['mean_degree_avg']:.2f} |"
            )

    lines += [
        "",
        "## Table 3. Soft converge rate vs Tx% (k = 10)",
        "",
    ]
    txs = sorted(summary_k10["tx_pct"].unique())
    header = "| N |" + "".join(f" Tx {int(t)}% |" for t in txs)
    sep = "|--:|" + "-----:|" * len(txs)
    lines += [header, sep]
    for n in sorted(summary_k10["n_nodes"].unique()):
        row = f"| {int(n)} |"
        for t in txs:
            v = summary_k10[
                (summary_k10["n_nodes"] == n) & (summary_k10["tx_pct"] == t)
            ]["soft_converge_rate"]
            row += f" {float(v.iloc[0]):.0%} |" if len(v) else " — |"
        lines.append(row)

    lines += [
        "",
        "## LaTeX (Table 1)",
        "",
        "```latex",
        r"\begin{tabular}{rrrrrr}",
        r"\hline",
        r"$N$ & Density & Min Tx (\%) & Energy proxy & Soft conv. & RMSE \\",
        r"\hline",
    ]
    for _, r in energy.iterrows():
        dens = int(r["n_nodes"]) / area
        if pd.isna(r["min_tx_pct"]):
            lines.append(rf"{int(r['n_nodes'])} & {dens:.2e} & --- & --- & --- & --- \\")
        else:
            lines.append(
                rf"{int(r['n_nodes'])} & {dens:.2e} & {r['min_tx_pct']:.0f} & "
                rf"{r['tx_energy_proxy']:.4f} & {r['soft_converge_rate']:.2f} & {r['rmse_avg']:.1f} \\"
            )
    lines += [r"\hline", r"\end{tabular}", "```", ""]
    (RESULTS / "paper_tables.md").write_text("\n".join(lines), encoding="utf-8")


def style_ax(ax, title, xlabel, ylabel):
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)


def make_plots(summary: pd.DataFrame, energy: pd.DataFrame) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    k10 = summary[summary["k_neighbors"] == 10].copy()

    # 1) Min Tx vs N
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    e = energy.dropna(subset=["min_tx_pct"])
    ax.plot(e["n_nodes"], e["min_tx_pct"], "o-", color="#1f4e79", lw=2, ms=7)
    style_ax(
        ax,
        "Minimum Tx range for degree ≥ 8 (k=10)",
        "Number of nodes N",
        "Min Tx (% of canvas diagonal)",
    )
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_min_tx_vs_N.png", dpi=160)
    plt.close(fig)

    # 2) Energy proxy vs N
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(e["n_nodes"], e["tx_energy_proxy"], "s-", color="#8b3a2a", lw=2, ms=7)
    style_ax(
        ax,
        "Tx energy proxy vs density (η=2.5, k=10)",
        "Number of nodes N",
        r"Energy proxy $(R/\mathrm{diag})^\eta$",
    )
    fig.tight_layout()
    fig.savefig(FIGS / "fig2_energy_vs_N.png", dpi=160)
    plt.close(fig)

    # 3) Mean degree heatmap-like lines
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for n, g in k10.groupby("n_nodes"):
        g = g.sort_values("tx_pct")
        ax.plot(g["tx_pct"], g["mean_degree_avg"], "o-", label=f"N={int(n)}", ms=4)
    ax.axhline(8, color="gray", ls="--", lw=1, label="degree=8")
    style_ax(ax, "Mean stored degree vs Tx range (k=10)", "Tx (% diagonal)", "Mean degree")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_degree_vs_tx.png", dpi=160)
    plt.close(fig)

    # 4) Soft converge heatmap (imshow)
    ns = sorted(k10["n_nodes"].unique())
    txs = sorted(k10["tx_pct"].unique())
    mat = np.full((len(ns), len(txs)), np.nan)
    for i, n in enumerate(ns):
        for j, t in enumerate(txs):
            v = k10[(k10["n_nodes"] == n) & (k10["tx_pct"] == t)]["soft_converge_rate"]
            if len(v):
                mat[i, j] = float(v.iloc[0])
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    im = ax.imshow(mat, aspect="auto", cmap="YlGn", vmin=0, vmax=1, origin="lower")
    ax.set_xticks(range(len(txs)))
    ax.set_xticklabels([str(int(t)) for t in txs])
    ax.set_yticks(range(len(ns)))
    ax.set_yticklabels([str(int(n)) for n in ns])
    ax.set_xlabel("Tx (% diagonal)")
    ax.set_ylabel("N")
    ax.set_title("Soft convergence rate (k=10)")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046)
    cbar.set_label("Soft converge rate")
    fig.tight_layout()
    fig.savefig(FIGS / "fig4_soft_converge_heatmap.png", dpi=160)
    plt.close(fig)

    # 5) Connected rate vs Tx
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for n, g in k10.groupby("n_nodes"):
        g = g.sort_values("tx_pct")
        ax.plot(g["tx_pct"], g["connected_rate"], "o-", label=f"N={int(n)}", ms=4)
    style_ax(ax, "Network connectedness vs Tx (k=10)", "Tx (% diagonal)", "Connected rate")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_connected_vs_tx.png", dpi=160)
    plt.close(fig)


def main() -> None:
    raw = load_raw()
    raw.to_csv(RESULTS / "results_raw_with_soft.csv", index=False)
    summary = summarize(raw)
    summary.to_csv(RESULTS / "results_summary_soft.csv", index=False)

    min8_parts = [min_tx_table(summary, 8.0, k) for k in [6, 10, 12]]
    min8 = pd.concat(min8_parts, ignore_index=True)
    min8.to_csv(RESULTS / "table_min_tx_for_degree8_soft.csv", index=False)

    energy = min_tx_table(summary, 8.0, k=10)
    energy = energy.assign(density=energy["n_nodes"] / (800 * 800))
    energy.to_csv(RESULTS / "table_energy_vs_density_k10_soft.csv", index=False)

    k10 = summary[summary["k_neighbors"] == 10]
    write_paper_markdown(energy, min8, k10)
    make_plots(summary, energy)

    print("Soft threshold: violation <=", SOFT_VIOL_THRESH, "and degree >=", SOFT_MIN_DEGREE)
    print(energy.to_string(index=False))
    print("\nWrote:")
    for p in sorted(RESULTS.glob("*soft*")):
        print(" ", p.name)
    for p in sorted(FIGS.glob("*.png")):
        print(" ", "figures/" + p.name)
    print("  paper_tables.md")


if __name__ == "__main__":
    main()
