# GPS-Denied Direction-Aware Routing

Companion **code and reproducible artifacts** for:

> **GPS-Denied Direction-Aware Routing Using Reference-Free Relative Localization**  
> Kanak Patel and Himanshu S. Mazumdar  
> Dharmsinh Desai University, Nadiad, India

The submitted manuscript is **not stored in this repository**.


---

## Question

Can a wireless sensor network continue direction-aware forwarding when absolute GPS coordinates are unavailable?

## Idea

Rather than recovering geographic coordinates, construct a relative map that preserves enough directional structure to make local forwarding decisions.

In this repository, **GPS-denied** means GPS is unavailable, inaccessible, unreliable, or intentionally not used. **Reference-free** means there are no absolute geographic anchors, not that the algorithm has zero geometric information.

```
Absolute GPS coordinates
          X
          X  unavailable
          X
Neighbour geometry
          |
          v
Relative coordinate map
          |
          v
Direction to destination
          |
          v
Greedy neighbour selection
          |
          v
Packet delivery
```

---

## Quick start

**Windows reviewers:** double-click `run_demo.bat` (this folder or the repository root). Choose **1** for the visual demo (a new source/destination each trial) or **3** to install requirements first.

```bash
pip install -r requirements.txt
python experiments/gps_denied_demo.py
python demo/dynamic_gps_denied_routing.py
```

Expected console output (values vary with seed):

```
GPS STATUS: DENIED
RELATIVE MAP: ACTIVE
PACKET: 108 -> 75 -> DESTINATION
Packet delivered
Hops: ...
Reference-route hops: ...
Route stretch: ...
Absolute GPS coordinates used: NO
```

Expected files:

| Output | Content |
|--------|---------|
| `Results/figures/figA_gps_denied_concept.png` | Concept diagram (manuscript Figure 1) |
| `Results/gps_denied_demo_summary.csv` | Phase-1 ground truth vs Phase-2 GPS-denied PDR/stretch |

Single-packet CLI:

```bash
python experiments/gps_denied_greedy_routing.py --n 120 --seed 13
```

Interactive / animated demo (qualitative only):

```bash
python demo/dynamic_gps_denied_routing.py --save-gif
```

writes `Results/figures/demo_gps_denied_snapshot.png` and `demo_gps_denied_routing.gif`.

---

## Reproduce the main routing results

One command regenerates the principal comparison:

```bash
python experiments/routing_reference_vs_relative.py --seeds 20 --pairs 500
```

This writes:

| File | Content |
|------|---------|
| `Results/routing_summary.csv` | PDR, hop count, stretch, failure/loop rates, next-hop agreement |
| `Results/pdr_comparison.png` | Figure C — packet delivery ratio |
| `Results/path_stretch.png` | Hop stretch |
| `Results/failure_rate.png` | Greedy failure rate |
| `Results/figures/figB_example_routes.png` | Same pair routed in reference vs relative frames |

Coordinate-error tolerance:

```bash
python experiments/localization_noise_sensitivity.py --seeds 10 --pairs 300
```

writes `Results/routing_noise_summary.csv`, `Results/noise_pdr.png`, `Results/figures/figD_noise_sensitivity.png`.

Rebuild logged routing figures from the experiment scripts (no manuscript file is generated in-repo):

---

## What the logged routing campaign showed

On connected planned-geometry unit-disk graphs, **N=250**, 20 seeds, 500 pairs/seed (10,000 paired routes per case):

| Case | PDR | Mean hops | Hop stretch | Next-hop agreement with reference |
|------|-----|-----------|-------------|-----------------------------------|
| A Reference coordinates | 1.000 | 4.469 | 1.147 | — |
| B MDS-only | 1.000 | 4.457 | 1.143 | 0.895 |
| C MDS + attraction | 1.000 | 4.457 | 1.143 | 0.895 |

Gaussian perturbation of the relative map up to **30% of nominal spacing** left PDR at 1.000; stretch rose from 1.142 to 1.167.

MDS-only and MDS+attraction are indistinguishable here, matching the geometric ablation (median ΔMAE = 0). Delivery saturation is a property of these well-connected graphs without large voids; it is not a claim of guaranteed GPS replacement. Frozen numbers: `Results/FROZEN_NUMBERS_GPS_DENIED_ROUTING.txt`.

---

## Repository layout

Existing density–Tx and topology-quality artefacts are kept. New routing code is added beside them.

```
README.md
LICENSE
requirements.txt
src/
    relative_localization.py      # planned geometry, MDS, relative map
    asymmetric_relaxation.py      # one-sided upper-bound updates
    mds_initialization.py
    greedy_directional_routing.py # min-angle next hop + safeguards
    metrics.py
experiments/
    gps_denied_demo.py
    gps_denied_greedy_routing.py
    routing_reference_vs_relative.py
    localization_noise_sensitivity.py
    routing_voids.py
    wsn_sim.py                    # original density–Tx simulator
    run_density_tx_sweep.py
    run_topology_quality.py
demo/
    dynamic_gps_denied_routing.py
Results/                          # CSVs, figures, frozen numbers
WsnQukMap/                        # original C# WinForms prototype
```

---

## Earlier density–Tx and topology-quality corpus

These experiments are unchanged and remain part of the manuscript.

```bash
cd experiments
python run_density_tx_sweep.py
python make_figures_and_tables.py
python run_topology_quality.py
python postprocess_topology_quality.py
```

Headline frozen numbers (see `Results/FROZEN_NUMBERS_PHASE1.txt`):

- For k=10, lowest tested Tx for mean degree ≥8 and connectivity falls from **20%** of the canvas diagonal at N=50 to **8%** at N=300 (~10× energy-proxy reduction).
- At N=250, median edge-direction MAE **≈2.86°**, directional-decision correctness **≈94.5%**.

---

## License

MIT. See [`LICENSE`](LICENSE).

## Contact

- Kanak Patel — kanakpatel.rnd@ddu.ac.in
- Himanshu S. Mazumdar — hsmazumdar@ddu.ac.in
