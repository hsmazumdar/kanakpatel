# kanakpatel

Research artifacts authored primarily by **Kanak Patel** (with Himanshu S. Mazumdar), hosted under [hsmazumdar](https://github.com/hsmazumdar).

## GPS-Denied Direction-Aware Routing

**Question.** Can a wireless sensor network continue direction-aware forwarding when absolute GPS coordinates are unavailable?

**Idea.** Rather than recovering geographic coordinates, construct a relative map that preserves enough directional structure to make local forwarding decisions.

```
Absolute GPS coordinates
          X  unavailable
Neighbour geometry
          |
          v
Relative coordinate map
          |
          v
Greedy neighbour selection
          |
          v
Packet delivery
```

| Folder | Description |
|--------|-------------|
| [**WsnLocalization2026**](./WsnLocalization2026/) | Code, results, and demo for *GPS-Denied Direction-Aware Routing Using Reference-Free Relative Localization* (manuscript not stored in this repository) |

```bash
cd WsnLocalization2026
pip install -r requirements.txt
python experiments/gps_denied_demo.py
python experiments/routing_reference_vs_relative.py --seeds 20 --pairs 500
```

Windows: double-click `run_demo.bat`.

**Direct project URL:** https://github.com/hsmazumdar/kanakpatel/tree/main/WsnLocalization2026

Contact: kanakpatel.rnd@ddu.ac.in
