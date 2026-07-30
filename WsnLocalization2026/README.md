# WsnLocalization2026

**Companion code and reproducible artifacts** for the manuscript:

> *Direction-Aware Routing via Reference-Free Relative Localization in Wireless Sensor Networks*  
> **Submission version: V04** (Q1)  
> Authors: Kanak Patel & Himanshu S. Mazumdar  
> Dharmsinh Desai University, Nadiad, India

**Paper file:** [`paper/Direction-Aware Routing via Reference-Free Relative Localization in WSN V04.docx`](paper/Direction-Aware%20Routing%20via%20Reference-Free%20Relative%20Localization%20in%20WSN%20V04.docx)

---

## Repository contents

| Path | Description |
|------|-------------|
| `paper/` | Final V04 manuscript (Word) |
| `Results/` | Logged CSVs, tables, figure PNGs, captions |
| `experiments/` | Headless Python simulator + sweep scripts |
| `WsnQukMap/` | Interactive C# WinForms prototype (Visual Studio) |

---

## Quick start for reviewers

### A. Inspect published results (no run required)

- Density vs Tx figures: `Results/figures/fig1_*.png` … `fig5_*.png`
- Topology preservation (manuscript Figs 6–7):  
  `Results/figures/fig_topology_preservation_N250.png`  
  `Results/figures/fig_topology_guidelines_overlay_N250.png`
- Tables / captions: `Results/paper_tables.md`, `Results/captions.md`, `Results/table_*.csv`

### B. Reproduce Python experiments

**Requirements:** Python 3.9+, `numpy`, `pandas`, `matplotlib`

```bash
pip install numpy pandas matplotlib
cd experiments

# Density–Tx matrix (600 trials; several minutes)
python run_density_tx_sweep.py
python make_figures_and_tables.py

# Mode A topology quality + Figs 6–7 (N=250 figure uses seed 13 after postprocess)
python run_topology_quality.py
python postprocess_topology_quality.py
```

**Fig. 6–7 protocol (documented in the paper):** Mode A expected distances → classical MDS initialization on shortest-path distances → short asymmetric-attraction refine → uniform (similarity) normalize.  
Reproduce the exact figure trial:

```python
from run_topology_quality import make_topology_figure
make_topology_figure(250, 13)
```

### C. Interactive C# simulator

1. Open `WsnQukMap/WsnMap.sln` in Visual Studio 2019+ (.NET Framework 4.7.2+).
2. Build and run. Localization uses asymmetric neighbor attraction with global canvas normalization (simulation convenience; see manuscript §4.2).

---

## Relation to the algorithm in the paper

- **Proposed core rule:** asymmetric neighbor attraction under expected-distance constraints (Mode A / Mode B discussed in text).
- **Density–Tx study:** attraction-based headless runs (`wsn_sim.py`), auditable CSVs under `Results/`.
- **Topology Figs 6–7:** Mode A quality evaluation with **MDS init + attraction refine** (stated in captions). MDS alone largely determines the map; attraction is a short refine. Cold-start attraction-only can be multimodal—hence the documented MDS-init protocol for that section.

---

## License

MIT (see project history / `CODE_OF_CONDUCT.md`). Use for peer review and academic reproduction.

## Contact

- Kanak Patel — kanakpatel.rnd@ddu.ac.in  
- Himanshu S. Mazumdar — hsmazumdar@ddu.ac.in
