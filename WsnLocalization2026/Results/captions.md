# Figure and Table Captions

Publication-ready captions for artifacts under `Results/`. Soft convergence means: network connected, mean stored degree ≥ 6, and mean constraint violation ≤ 1 pixel. Canvas size is fixed at 800×800 pixels. Transmission range (`Tx`) is expressed as a percentage of the canvas diagonal. Neighbor cap \(k\) matches the simulator parameter `txRange`. Energy proxy uses \((R/\mathrm{diag})^{\eta}\) with \(\eta = 2.5\).

---

## Figures

**Fig. 1.** Minimum transmission range required to achieve mean stored degree ≥ 8 with a fully connected neighborhood graph, as a function of node count \(N\) (\(k = 10\)). Higher density reduces the feasible `Tx` percentage of the canvas diagonal.  
*File:* `figures/fig1_min_tx_vs_N.png`

**Fig. 2.** Relative transmission-energy proxy \((R/\mathrm{diag})^{\eta}\) (\(\eta = 2.5\)) at the energy-optimal `Tx` of Fig. 1 versus node count \(N\) (\(k = 10\)). Increasing density yields approximately an order-of-magnitude reduction in the proxy from \(N = 50\) to \(N = 300\).  
*File:* `figures/fig2_energy_vs_N.png`

**Fig. 3.** Mean number of stored neighbors (degree, capped at \(k = 10\)) versus transmission range for \(N \in \{50,100,150,200,300\}\). The dashed line marks the target degree of 8 used for deployment sizing; denser deployments reach this target at lower `Tx`.  
*File:* `figures/fig3_degree_vs_tx.png`

**Fig. 4.** Soft-convergence rate over five Monte-Carlo seeds as a function of node count \(N\) (rows) and transmission range (columns), for \(k = 10\). Soft success requires connectivity, degree ≥ 6, and residual constraint violation ≤ 1 px.  
*File:* `figures/fig4_soft_converge_heatmap.png`

**Fig. 5.** Fraction of trials in which the \(k\)-NN unit-disk graph forms a single connected component (no isolates), versus transmission range, for each \(N\) (\(k = 10\)). Connectedness is a prerequisite for reliable relative localization and for soft convergence.  
*File:* `figures/fig5_connected_vs_tx.png`

---

## Tables (paper)

**Table 1.** Energy-optimal transmission range versus node density for neighbor cap \(k = 10\) and target mean degree ≥ 8. For each \(N\), the smallest `Tx` (% of diagonal) that yields a connected graph with mean degree ≥ 8 is reported, together with the corresponding energy proxy, soft-convergence rate, and Procrustes RMSE after localization.  
*Source:* `table_energy_vs_density_k10_soft.csv` · also in `paper_tables.md`

**Table 2.** Sensitivity of the energy-optimal `Tx` to the neighbor cap \(k \in \{6,10,12\}\) under the same degree-≥-8 and connectivity criteria as Table 1. Entries marked “—” indicate that degree 8 is unreachable because \(k < 8\) caps stored neighbors below the target.  
*Source:* `table_min_tx_for_degree8_soft.csv` · also in `paper_tables.md`

**Table 3.** Soft-convergence rate (%) versus transmission range for \(k = 10\) and \(N \in \{50,100,150,200,300\}\) (five seeds per cell). Values highlight the operating region where lower `Tx` remains viable as density increases.  
*Source:* `results_summary_soft.csv` (pivot) · also in `paper_tables.md`

---

## Supporting / supplementary tables

**Table S1.** Full experimental input grid: node count, `Tx` (%), neighbor cap \(k\), random seed, and fixed algorithm controls (canvas size, attraction factor, moves per tick, iteration limit).  
*File:* `param_matrix.csv`

**Table S2.** Raw trial outcomes (one row per seed), including mean/min/max degree, connectivity, hard timer convergence, ticks, constraint violation, Procrustes RMSE, \(R/s\), and energy proxy.  
*File:* `results_raw.csv`

**Table S3.** Same as Table S2 with soft-convergence and meaningful-hard-convergence flags appended.  
*File:* `results_raw_with_soft.csv`

**Table S4.** Aggregated means and standard deviations of connectivity, hard/soft convergence, ticks, RMSE, and energy proxy, grouped by \((N,\,\mathrm{Tx},\,k)\).  
*File:* `results_summary.csv` (hard metrics) · `results_summary_soft.csv` (soft metrics)

**Table S5.** Hard-convergence rate and mean degree versus `Tx` for \(k = 10\) (pre–soft-metric sweep summary).  
*File:* `table_convergence_rate_k10.csv`

**Table S6.** Minimum `Tx` satisfying mean degree ≥ 6 and full connectivity (hard-metric sweep), by \(N\) and \(k\).  
*File:* `table_min_tx_for_degree6.csv`

**Table S7.** Minimum `Tx` satisfying mean degree ≥ 8 and full connectivity using hard convergence rates (pre–soft-metric version of Table 2).  
*File:* `table_min_tx_for_degree8.csv`

**Table S8.** Energy-optimal `Tx` versus density for \(k = 10\) using hard metrics only (pre–soft-metric version of Table 1).  
*File:* `table_energy_vs_density_k10.csv`

---

## Short captions (figure list / LaTeX `\caption{}`)

```latex
% Figures
\caption{Minimum Tx (\% of canvas diagonal) vs.\ node count $N$ for mean degree $\ge 8$ and a connected graph ($k=10$).}
\caption{Transmission-energy proxy $(R/\mathrm{diag})^{\eta}$ ($\eta=2.5$) at the energy-optimal Tx of Fig.~1 vs.\ $N$ ($k=10$).}
\caption{Mean stored degree vs.\ Tx for several densities $N$; dashed line marks the degree-8 design target ($k=10$).}
\caption{Soft-convergence rate vs.\ $N$ and Tx ($k=10$; connected, degree $\ge 6$, violation $\le 1$\,px).}
\caption{Connectedness rate of the $k$-NN unit-disk graph vs.\ Tx for several $N$ ($k=10$).}

% Tables
\caption{Energy-optimal Tx vs.\ node density for $k=10$ and target mean degree $\ge 8$.}
\caption{Energy-optimal Tx vs.\ density for neighbor caps $k\in\{6,10,12\}$ (degree $\ge 8$).}
\caption{Soft-convergence rate (\%) vs.\ Tx for $k=10$ and varying $N$.}
```

---

## One-line captions (slide / poster)

| ID | One-liner |
|----|-----------|
| Fig. 1 | Denser nets need less Tx to keep degree ≥ 8. |
| Fig. 2 | Energy proxy falls ~10× as \(N\) grows from 50 to 300. |
| Fig. 3 | Degree rises with Tx; high \(N\) hits target degree sooner. |
| Fig. 4 | Soft success is sparse at low Tx; denser \(N\) opens lower-Tx cells. |
| Fig. 5 | Connectivity jumps to 1 once Tx exceeds a density-dependent threshold. |
| Table 1 | Deployment assist: recommended min Tx% and energy vs \(N\). |
| Table 2 | Same assist across \(k\); \(k=6\) cannot reach degree 8. |
| Table 3 | Soft-success map over the full Tx sweep. |

---

---

---

---

---

---

## Ver03 topology-quality figures (B1–B3)

**Fig. T1 (Ver03).** Topological preservation in a 250-node network (planned geometry supplies expected distances; classical MDS initialization on the distance graph; asymmetric-attraction refine; uniform scale normalization). Left: reference topology; right: localized map after similarity (Procrustes) alignment. Gray: communication edges; black: column guidelines. Shown trial seed=13.
*File:* `figures/fig_topology_preservation_N250.png`

**Fig. T2 (Ver03).** Correspondence guidelines after Procrustes alignment (N=250, same trial as Fig. T1): black segments join reference nodes to localized counterparts (subsampled).
*File:* `figures/fig_topology_guidelines_overlay_N250.png`

**Table T1 (Ver03).** Topological consistency vs network size (black-guideline edge-direction MAE/SD/CV and directional correctness ±30°). Values are trial **medians**; success rate = fraction with MAE < 6°. Auditable CSVs in `Results/`.
*Source:* `table_topology_angle_mae.csv` · also in `paper_tables.md`
