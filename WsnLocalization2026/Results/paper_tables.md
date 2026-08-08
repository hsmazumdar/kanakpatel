# Density vs Transmission Range — Experimental Tables

Canvas fixed at 800×800. Soft converge: connected, mean degree ≥ 6, constraint violation ≤ 1.0 px.

## Table 1. Energy-optimal Tx vs node density (k = 10, degree ≥ 8)

| N | Density (nodes/px²) | Min Tx (% diag) | Tx energy proxy R^η | Soft converge | RMSE |
|--:|--------------------:|----------------:|--------------------:|--------------:|-----:|
| 50 | 7.81e-05 | 20 | 0.0179 | 100% | 247.2 |
| 100 | 1.56e-04 | 15 | 0.0087 | 60% | 116.1 |
| 150 | 2.34e-04 | 10 | 0.0032 | 40% | 191.2 |
| 200 | 3.13e-04 | 10 | 0.0032 | 20% | 214.4 |
| 300 | 4.69e-04 | 8 | 0.0018 | 20% | 307.8 |

## Table 2. Min Tx for mean degree ≥ 8 (all k)

| N | k | Min Tx% | Energy proxy | Soft converge | Mean degree |
|--:|--:|--------:|-------------:|--------------:|------------:|
| 50 | 6 | — | — | — | — |
| 100 | 6 | — | — | — | — |
| 150 | 6 | — | — | — | — |
| 200 | 6 | — | — | — | — |
| 300 | 6 | — | — | — | — |
| 50 | 10 | 20 | 0.0179 | 100% | 8.76 |
| 100 | 10 | 15 | 0.0087 | 60% | 9.33 |
| 150 | 10 | 10 | 0.0032 | 40% | 8.12 |
| 200 | 10 | 10 | 0.0032 | 20% | 9.52 |
| 300 | 10 | 8 | 0.0018 | 20% | 9.52 |
| 50 | 12 | 20 | 0.0179 | 80% | 9.60 |
| 100 | 12 | 15 | 0.0087 | 100% | 10.51 |
| 150 | 12 | 10 | 0.0032 | 20% | 8.29 |
| 200 | 12 | 10 | 0.0032 | 80% | 10.79 |
| 300 | 12 | 8 | 0.0018 | 40% | 10.63 |

## Table 3. Soft converge rate vs Tx% (k = 10)

| N | Tx 5% | Tx 8% | Tx 10% | Tx 12% | Tx 15% | Tx 20% | Tx 25% | Tx 30% |
|--:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| 50 | 0% | 0% | 0% | 0% | 60% | 100% | 100% | 100% |
| 100 | 0% | 0% | 0% | 80% | 60% | 100% | 100% | 80% |
| 150 | 0% | 0% | 40% | 60% | 80% | 60% | 60% | 60% |
| 200 | 0% | 40% | 20% | 40% | 40% | 40% | 40% | 40% |
| 300 | 0% | 20% | 40% | 40% | 40% | 40% | 40% | 40% |

## LaTeX (Table 1)

```latex
\begin{tabular}{rrrrrr}
\hline
$N$ & Density & Min Tx (\%) & Energy proxy & Soft conv. & RMSE \\
\hline
50 & 7.81e-05 & 20 & 0.0179 & 1.00 & 247.2 \\
100 & 1.56e-04 & 15 & 0.0087 & 0.60 & 116.1 \\
150 & 2.34e-04 & 10 & 0.0032 & 0.40 & 191.2 \\
200 & 3.13e-04 & 10 & 0.0032 & 0.20 & 214.4 \\
300 & 4.69e-04 & 8 & 0.0018 & 0.20 & 307.8 \\
\hline
\end{tabular}
```

## Table (Ver03). Topological consistency — black guideline angle analysis (planned geometry)

Planned-geometry expected distances; classical MDS initialization on expected-distance shortest paths, then asymmetric-attraction refine; uniform normalize. Reported MAE/SD/CV and directional correctness are **trial medians**. Success = fraction of trials with MAE < 6°. Seeds: 20 (N<1000) or 10 (N≥1000).

| Nodes | Ref. columns | SD [°] | CV [%] | Angle MAE [°] | Dir. correct. | Success (MAE<6°) | Assessment |
|------:|-------------:|-------:|-------:|--------------:|--------------:|----------------:|:-----------|
| 25 | 5 | 5.90 | 80.69 | 7.34 | 98.8% | 45% | Well Achieved |
| 64 | 8 | 8.22 | 82.17 | 9.30 | 97.2% | 40% | Well Achieved |
| 100 | 10 | 27.42 | 74.31 | 45.40 | 96.8% | 50% | Needs Attention |
| 250 | 16 | 2.66 | 91.76 | 2.86 | 94.5% | 100% | Excellent |
| 500 | 23 | 2.89 | 91.28 | 3.11 | 94.8% | 95% | Excellent |
| 750 | 28 | 3.03 | 95.03 | 3.15 | 94.0% | 95% | Excellent |
| 1000 | 32 | 3.46 | 99.25 | 3.33 | 93.2% | 100% | Excellent |
| 1500 | 39 | 3.38 | 98.29 | 3.40 | 91.2% | 90% | Excellent |
| 2000 | 45 | 3.49 | 102.36 | 3.49 | 93.8% | 80% | Excellent |

*Artifacts:* `topology_quality_raw.csv`, `topology_quality_summary.csv`, `table_topology_angle_mae.csv`, `figures/fig_topology_preservation_N250.png`, `figures/fig_topology_guidelines_overlay_N250.png`.
