"""Build Phase-1 frozen numbers sheet from Results CSVs."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "Results"
OUT_ROOT = ROOT.parents[1] / "FROZEN_NUMBERS_PHASE1.txt"
OUT_RESULTS = R / "FROZEN_NUMBERS_PHASE1.txt"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> None:
    raw = pd.read_csv(R / "results_raw.csv")
    energy = pd.read_csv(R / "table_energy_vs_density_k10.csv")
    energy_soft = pd.read_csv(R / "table_energy_vs_density_k10_soft.csv")
    deg8 = pd.read_csv(R / "table_min_tx_for_degree8.csv")
    deg6 = pd.read_csv(R / "table_min_tx_for_degree6.csv")
    conv = pd.read_csv(R / "table_convergence_rate_k10.csv")
    topo = pd.read_csv(R / "table_topology_angle_mae.csv")
    topo_raw = pd.read_csv(R / "topology_quality_raw.csv")

    n250 = topo_raw[(topo_raw.n_nodes == 250) & (topo_raw.seed == 13)].iloc[0]
    e50 = float(energy.loc[energy.n_nodes == 50, "tx_energy_proxy"].iloc[0])
    e300 = float(energy.loc[energy.n_nodes == 300, "tx_energy_proxy"].iloc[0])
    ratio = e50 / e300
    mae250 = float(topo.loc[topo.n_nodes == 250, "angle_mae_deg"].iloc[0])
    dir250 = float(topo.loc[topo.n_nodes == 250, "directional_correctness"].iloc[0])
    succ250 = float(topo.loc[topo.n_nodes == 250, "success_rate_mae_lt6"].iloc[0])
    seed250 = int(topo.loc[topo.n_nodes == 250, "best_seed"].iloc[0])
    tx50 = float(energy.loc[energy.n_nodes == 50, "min_tx_pct"].iloc[0])
    tx300 = float(energy.loc[energy.n_nodes == 300, "min_tx_pct"].iloc[0])

    figs = [
        "fig1_min_tx_vs_N.png",
        "fig2_energy_vs_N.png",
        "fig3_degree_vs_tx.png",
        "fig4_soft_converge_heatmap.png",
        "fig5_connected_vs_tx.png",
        "fig_topology_preservation_N250.png",
        "fig_topology_guidelines_overlay_N250.png",
    ]

    lines: list[str] = []
    A = lines.append
    A("=" * 78)
    A("PHASE 1 FROZEN NUMBERS SHEET")
    A("Manuscript target: Reference-FreeRelativeLocalizationWsn.docx")
    A("Experiment root: kanakpatel-main/WsnLocalization2026")
    A(f"Frozen UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    A("Protocol labels: planned-geometry expected distances (no Mode A/B in paper text)")
    A("=" * 78)
    A("")
    A("0) RUN STATUS")
    A("-" * 40)
    A(f"Density-Tx trials in results_raw.csv: {len(raw)} (expect 600)")
    A(f"Topology trials in topology_quality_raw.csv: {len(topo_raw)} (expect 150)")
    A("Scripts completed: run_density_tx_sweep.py | make_figures_and_tables.py")
    A("                 run_topology_quality.py | postprocess_topology_quality.py")
    A("                 make_topology_figure(250, 13)")
    A("")
    A("Artifact SHA256 (first 16 hex) - use to detect accidental overwrite:")
    for name in [
        "results_raw.csv",
        "results_summary.csv",
        "table_energy_vs_density_k10.csv",
        "table_min_tx_for_degree8.csv",
        "table_min_tx_for_degree6.csv",
        "table_convergence_rate_k10.csv",
        "topology_quality_raw.csv",
        "topology_quality_summary.csv",
        "table_topology_angle_mae.csv",
    ]:
        p = R / name
        A(f"  {name:40s}  {sha(p)}  {p.stat().st_size} bytes")
    for name in figs:
        p = R / "figures" / name
        if p.exists():
            A(f"  figures/{name:31s}  {sha(p)}  {p.stat().st_size} bytes")
    A("")

    A("1) FIXED CONTROLS (density-Tx matrix)")
    A("-" * 40)
    A("Canvas: 800 x 800")
    A("N: 50, 100, 150, 200, 300")
    A("tx_pct: 5, 8, 10, 12, 15, 20, 25, 30  (% of canvas diagonal)")
    A("k_neighbors: 6, 10, 12")
    A("seeds: 0..4  => 5 x 8 x 3 x 5 = 600 trials")
    A("attraction=0.3, moves_per_tick=100, max_ticks=250, path_loss_eta=2.5")
    A("")

    A("2) DENSITY-Tx DEPLOYMENT TABLE (k=10) - USE IN PAPER Sec.6 / IoT PARAGRAPH")
    A("   Source: table_energy_vs_density_k10.csv")
    A("-" * 40)
    A(f"{'N':>6} {'density':>14} {'min_tx_%':>10} {'E_proxy':>12} {'conv_rate':>10} {'rmse_avg':>10}")
    for _, r in energy.iterrows():
        A(
            f"{int(r.n_nodes):6d} {r.density:14.6e} {r.min_tx_pct:10.1f} "
            f"{r.tx_energy_proxy:12.6f} {r.converge_rate:10.1f} {r.rmse_avg:10.3f}"
        )
    A("")
    A("KEY CLAIM NUMBERS (freeze for DOCX):")
    A(f"  N=50  -> min Tx = {tx50:.0f}% of diagonal; E_proxy = {e50:.6f}")
    A(f"  N=300 -> min Tx = {tx300:.0f}% of diagonal; E_proxy = {e300:.6f}")
    A(f"  Energy-proxy reduction factor (N50@minTx / N300@minTx) = {ratio:.2f}x")
    A("  IoT paragraph wording: for 800x800 deployment, raising density to 300 nodes")
    A("  allows cutting min Tx from 20% to 8% of diagonal while targeting mean degree ~8-10.")
    A("")

    A("2b) SOFT-THRESHOLD ENERGY TABLE (optional; from make_figures_and_tables)")
    A("   Source: table_energy_vs_density_k10_soft.csv")
    A("-" * 40)
    A(f"{'N':>6} {'min_tx_%':>10} {'E_proxy':>12} {'soft_conv':>10} {'mean_deg':>10}")
    for _, r in energy_soft.iterrows():
        A(
            f"{int(r.n_nodes):6d} {r.min_tx_pct:10.1f} {r.tx_energy_proxy:12.6f} "
            f"{r.soft_converge_rate:10.1f} {r.mean_degree_avg:10.3f}"
        )
    A("")

    A("3) MIN Tx FOR MEAN DEGREE >= 8 / CONNECTED")
    A("   Source: table_min_tx_for_degree8.csv")
    A("-" * 40)
    A(deg8.to_string(index=False))
    A("")
    A("4) MIN Tx FOR MEAN DEGREE >= 6 / CONNECTED")
    A("   Source: table_min_tx_for_degree6.csv")
    A("-" * 40)
    A(deg6.to_string(index=False))
    A("")

    A("5) CONVERGENCE RATE vs Tx (k=10)")
    A("   Source: table_convergence_rate_k10.csv")
    A("-" * 40)
    A(conv.to_string(index=False))
    A("")

    A("6) TOPOLOGY / DIRECTIONAL CONSISTENCY (PLANNED GEOMETRY)")
    A("   Protocol: classical MDS init on expected-distance shortest paths ->")
    A("             asymmetric-attraction refine -> uniform (similarity) normalize")
    A("   Paper table uses TRIAL MEDIANS (postprocess), not means.")
    A("   Source: table_topology_angle_mae.csv + topology_quality_summary.csv")
    A("-" * 40)
    A(
        f"{'N':>6} {'ref_cols':>8} {'MAE_med':>8} {'SD':>8} {'CV%':>8} "
        f"{'dir_corr':>9} {'succ<6':>8} {'assess':>16} {'best_seed':>9}"
    )
    for _, r in topo.iterrows():
        A(
            f"{int(r.n_nodes):6d} {int(r.reference_columns):8d} {r.angle_mae_deg:8.4f} "
            f"{r.angle_sd_deg:8.4f} {r.angle_cv_pct:8.4f} {100 * r.directional_correctness:8.1f}% "
            f"{100 * r.success_rate_mae_lt6:7.0f}% {r.assessment:>16} {int(r.best_seed):9d}"
        )
    A("")
    A("PRIMARY FIGURE / HEADLINE TOPOLOGY NUMBERS (freeze for DOCX):")
    A(f"  N=250 median relative edge-direction MAE = {mae250:.4f} deg")
    A(f"  N=250 directional correctness (+/-30 deg) = {100 * dir250:.1f}%")
    A(f"  N=250 success rate (MAE < 6 deg)         = {100 * succ250:.0f}%")
    A(f"  N=250 best/display seed                  = {seed250}  (Figs 6-7)")
    A(
        f"  N=250 seed=13 trial: MAE={n250.angle_mae_deg:.4f} deg, "
        f"dir={100 * n250.directional_correctness:.1f}%, "
        f"Procrustes RMSE={n250.procrustes_rmse:.2f} px"
    )
    A("")
    A("NOTE: Do NOT cite raw means from run_topology_quality stdout for small N;")
    A("      occasional reflection/flip trials inflate means (~90 deg). Paper uses medians.")
    A("")
    A("WARNING - numerical lookalike, NOT the old 23xN bug:")
    A("  At N=500, reference_columns = 23 (ceil(sqrt(500))). This is layout columns,")
    A("  NOT an iterations~23xN formula. Never write iterations ~ 23xN.")
    A("")

    A("7) FIGURE FILES TO EMBED / KEEP SYNCED")
    A("-" * 40)
    for name in figs:
        A(f"  Results/figures/{name}")
    A("")

    A("8) COPY-READY SENTENCES (Mode-label-free)")
    A("-" * 40)
    A("Density-Tx: On an 800x800 canvas with k=10, the minimum transmission range")
    A("meeting the degree~8 connectivity target falls from 20% of the diagonal at")
    A("N=50 to 8% at N=300, reducing the path-loss energy proxy by about an order")
    A(f"of magnitude ({ratio:.1f}x in the logged table).")
    A("")
    A("Topology: Under planned-geometry expected-distance constraints with MDS")
    A("initialization and asymmetric-attraction refine, the N=250 trial-median")
    A(f"relative edge-direction MAE is {mae250:.2f} deg with directional correctness")
    A(f"{100 * dir250:.1f}% (seed {seed250} shown in the preservation figures).")
    A("")
    A("9) NEXT GATE")
    A("-" * 40)
    A("Phase 2: COMPLETE (see PHASE2_REPO_SCRUB.txt).")
    A("Phase 3: edit Reference-FreeRelativeLocalizationWsn.docx using ONLY these numbers.")
    A("=" * 78)

    text = "\n".join(lines) + "\n"
    OUT_ROOT.write_text(text, encoding="utf-8")
    OUT_RESULTS.write_text(text, encoding="utf-8")
    # Avoid Windows console UnicodeEncodeError
    print(text.encode("ascii", errors="replace").decode("ascii"))
    print("WROTE", OUT_ROOT)
    print("WROTE", OUT_RESULTS)


if __name__ == "__main__":
    main()
