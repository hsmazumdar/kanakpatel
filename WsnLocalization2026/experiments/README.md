# Density vs Tx experiment controller

## Input parameter matrix

| Factor | Values | Meaning |
|--------|--------|---------|
| `n_nodes` | 50, 100, 150, 200, 300 | Density on fixed 800×800 canvas |
| `tx_pct` | 5, 8, 10, 12, 15, 20, 25, 30 | Radio range = % of canvas diagonal (Tx proxy) |
| `k_neighbors` | 6, 10, 12 | Max stored neighbors (`txRange`) |
| `seeds` | 0..4 | Monte-Carlo repeats |

**Fixed:** canvas 800×800, attraction 0.3, 100 moves/tick, max 250 ticks, η=2.5 energy proxy.

Total combos: `5 × 8 × 3 × 5 = 600`.

## Run

```bash
python experiments/run_density_tx_sweep.py
python experiments/make_figures_and_tables.py
```

## Topology quality (Ver03 B1–B3)

Restores V01-style localization-quality figure + angle MAE table (Mode A).

```bash
python experiments/run_topology_quality.py
python experiments/postprocess_topology_quality.py
```

**Protocol:** classical MDS init on expected-distance shortest paths → asymmetric-attraction refine → uniform (similarity) normalize. Metrics: black-guideline edge-direction MAE/SD/CV and directional correctness (±30°). Figure: N=250 side-by-side reference vs localized.

| Output | Content |
|--------|---------|
| `topology_quality_raw.csv` | Per-trial metrics |
| `topology_quality_summary.csv` | Medians / success rates by N |
| `table_topology_angle_mae.csv` | Paper table |
| `figures/fig_topology_preservation_N250.png` | Fig. T1 |
| `figures/fig_topology_guidelines_overlay_N250.png` | Fig. T2 |

## Outputs (`Results/`)

| File | Content |
|------|---------|
| `param_matrix.csv` | Full input grid |
| `param_matrix_definition.json` | Factor definitions |
| `results_raw.csv` | One row per trial |
| `results_summary.csv` | Mean/std by (N, tx_pct, k) |
| `table_min_tx_for_degree8.csv` | Min Tx% with mean degree ≥ 8 + connected |
| `table_min_tx_for_degree6.csv` | Same for degree ≥ 6 |
| `table_energy_vs_density_k10.csv` | Deployment assist: density → min Tx |
| `table_convergence_rate_k10.csv` | Converge/degree vs Tx for k=10 |
