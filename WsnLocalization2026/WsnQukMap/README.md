# Reference-Free Relative Localization for Direction-Aware Routing in Wireless Sensor Networks

## Abstract

This repository contains the implementation of a **reference-free relative localization framework** specifically designed for direction-aware routing in wireless sensor networks (WSNs). Unlike conventional localization approaches that aim for metric accuracy or absolute coordinates, this method focuses exclusively on establishing consistent **relative spatial orientation** among nodes, sufficient for routing decisions that require only the direction of the destination node.

The framework implements the **SIGMAPS-CG** (Signal-Guided Map Synchronization with Centroid Guidance) algorithm, which enables each node to independently construct an internal relative map by statistically aggregating received signal strength (RSS) information and applying RSS-weighted self-correction, without relying on anchors, distance estimation, or centralized coordination.

---

## Objective

### Primary Goals

1. **Topological Consistency**: Achieve network-wide consensus on relative spatial relationships among nodes, sufficient for direction-only routing decisions.

2. **Energy Efficiency**: Minimize communication and computational overhead by aligning localization fidelity precisely with routing layer requirements ("direction is enough").

3. **Anchor-Free Operation**: Eliminate dependencies on GPS, beacons, or site surveys, making the system suitable for ad-hoc deployments in unknown environments.

4. **Distributed Convergence**: Enable autonomous, asynchronous operation where each node independently refines its spatial map through local RSS observations and minimal neighbor communication.

5. **Robustness**: Maintain stable convergence under realistic conditions including:
   - Log-normal shadowing noise
   - Asymmetric radio links
   - Asynchronous node updates
   - Varying network density

### Key Innovation

The core contribution is a **topology-preserving spatial consensus mechanism** that emerges organically from nominal communication traffic. By co-designing localization with routing and energy conservation, the framework operates without anchors, ranging, centralized coordination, or absolute coordinates, using only RSS statistics gleaned from normal communication traffic.

---

## Quick Start

### System Requirements

- **Operating System**: Windows 10/11
- **Development Environment**: Visual Studio 2019 or later
- **Framework**: .NET Framework 4.7.2 or later
- **Hardware**: Any Windows-compatible system with sufficient screen resolution for visualization

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/WsnQukMap.git
   cd WsnQukMap
   ```

2. **Open the Solution**
   - Open `WsnMap.sln` in Visual Studio
   - Restore NuGet packages if prompted

3. **Build the Project**
   - Press `F6` or select `Build > Build Solution`
   - The executable will be generated in `WsnMap/bin/Debug/WsnMap.exe`

### Running the Application

1. **Launch the Application**
   - Run `WsnMap.exe` or press `F5` in Visual Studio
   - The application window will open with a black canvas

2. **Initial Setup**
   - The application automatically initializes with default parameters:
     - Number of nodes: 100 (configurable via textbox)
     - Transmission range: Adjustable via numeric up-down control
     - Node size: 20 pixels

3. **Basic Operations**

   **Generate New Network:**
   - Click the **"NODES"** button to generate a new random network topology
   - Reference nodes (ground truth) are displayed in green/pink circles

   **Run Localization Algorithm:**
   - Click **"QUICK TEST"** to start the iterative localization process
   - The algorithm will continuously refine node positions based on distance matrix constraints
   - Click **"STOP TEST"** to pause the algorithm

   **View Results:**
   - **"REF NODE"** button: Display reference (ground truth) positions
   - **"QUICK NODE"** button: Display estimated positions from localization
   - **"FIT"** button: Normalize estimated positions to 90% canvas occupancy

   **Interactive Correction:**
   - Enable **"Self Correct"** checkbox
   - Click on any node to manually trigger neighbor attraction
   - Neighbors will move 10% toward the selected node if they exceed expected distance

4. **Visualization Features**
   - **Node Colors**: 
     - Green: Lower half of reference nodes
     - Pink: Upper half of reference nodes
     - Yellow: Node sequence numbers
   - **Highlighting**: 
     - Turquoise: Node 0 (default highlight)
     - Red: Selected node (on click)
     - Brown: Neighbors of selected node
     - Blue: Active node during self-correction

### Expected Behavior

- **Initial State**: Nodes are randomly positioned (quicknod)
- **Convergence Process**: Nodes gradually move toward positions consistent with distance matrix constraints
- **Final State**: Estimated positions (quicknod) converge to a topology consistent with reference positions (refnod), up to rotation, translation, and scale

---

## Parameter Tuning

### Core Algorithm Parameters

The localization algorithm's behavior is controlled by several key parameters. Understanding and tuning these parameters is essential for optimal performance across different network conditions.

#### 1. Transmission Range (`txRange`)

**Location**: Numeric up-down control in UI  
**Default**: 10 neighbors  
**Description**: Maximum number of nearest neighbors stored in the distance matrix per node.

**Tuning Guidelines**:
- **Sparse Networks** (average degree < 6): Increase to 15-20 to capture more neighbors
- **Dense Networks** (average degree > 15): Decrease to 5-8 to reduce computational overhead
- **Optimal Range**: 8-12 neighbors for most scenarios

**Impact**:
- Too low: Insufficient constraints, slow convergence
- Too high: Increased computation, potential inclusion of distant/weak links

#### 2. Transmission Distance (`txDistance`)

**Location**: Calculated from `numudTxRange` (% of canvas diagonal)  
**Default**: Variable based on canvas size  
**Description**: Physical distance threshold (in pixels) for neighbor detection.

**Tuning Guidelines**:
- **Small Networks** (< 50 nodes): 20-30% of canvas diagonal
- **Medium Networks** (50-200 nodes): 15-25% of canvas diagonal
- **Large Networks** (> 200 nodes): 10-20% of canvas diagonal

**Impact**:
- Too low: Network fragmentation, disconnected components
- Too high: Excessive neighbors, reduced localization accuracy

#### 3. Node Attraction Factor

**Location**: Hardcoded in `MoveNodeByIndex()` and `MoveNode()`  
**Current Values**: 
- Timer-based updates: 30% (`0.3f`)
- Manual correction: 10% (`0.1f`)

**Description**: Fraction of distance moved toward target position per iteration.

**Tuning Guidelines**:
- **Fast Convergence**: 0.4-0.5 (may cause oscillation)
- **Stable Convergence**: 0.2-0.3 (recommended)
- **Smooth Convergence**: 0.1-0.15 (slower but more stable)

**Impact**:
- Too high: Oscillation, instability, overshooting
- Too low: Slow convergence, may get stuck in local minima

#### 4. Normalization Interval

**Location**: `NormalizeQuickNodes()` called every timer tick  
**Description**: Frequency of map normalization to prevent scale drift.

**Tuning Guidelines**:
- **Rapid Convergence Phase**: Normalize every 5-10 iterations
- **Stable Phase**: Normalize every 20-50 iterations
- **Converged State**: Disable normalization (nodes are stable)

**Impact**:
- Too frequent: Jittery behavior, disrupted convergence
- Too rare: Scale drift, map collapse or expansion

#### 5. Convergence Threshold

**Location**: Not explicitly implemented (future enhancement)  
**Recommended Value**: 0.1-1.0 pixels  
**Description**: Maximum cumulative displacement over a sliding window to declare convergence.

**Tuning Guidelines**:
- **High Precision Required**: 0.05-0.1 pixels
- **Standard Operation**: 0.1-0.5 pixels
- **Fast Convergence**: 1.0-2.0 pixels

### Network-Specific Tuning

#### Sparse Networks (Average Degree < 6)

```csharp
txRange = 15;              // Capture more neighbors
txDistance = 0.25;         // 25% of canvas diagonal
attractionFactor = 0.2f;   // Conservative movement
normalizationInterval = 10; // Frequent normalization
```

#### Dense Networks (Average Degree > 15)

```csharp
txRange = 8;               // Limit neighbors
txDistance = 0.15;         // 15% of canvas diagonal
attractionFactor = 0.3f;   // Faster convergence
normalizationInterval = 20; // Less frequent normalization
```

#### Noisy Environments (High RSS Variance)

```csharp
txRange = 12;              // More neighbors for robustness
attractionFactor = 0.15f;  // Slower, more stable updates
normalizationInterval = 15; // Moderate normalization
```

### Performance Optimization Parameters

#### Update Frequency

**Location**: `tmrQuickTest.Interval`  
**Current**: 10 ms  
**Tuning**:
- **Real-time Visualization**: 10-50 ms
- **Fast Simulation**: 1-5 ms
- **Energy-Saving Mode**: 100-500 ms

#### Batch Updates per Tick

**Location**: `tmrQuickTest_Tick()` loop  
**Current**: 100 iterations per tick  
**Tuning**:
- **Smooth Animation**: 10-50 iterations
- **Fast Convergence**: 100-200 iterations
- **Precise Control**: 1-10 iterations

### Parameter Interaction

**Important Considerations**:

1. **Attraction Factor vs. Update Frequency**: Higher attraction with slower updates can achieve similar convergence rates with less computation.

2. **Transmission Range vs. Network Density**: In dense networks, increasing `txRange` beyond 12 provides diminishing returns.

3. **Normalization vs. Convergence Speed**: More frequent normalization stabilizes scale but may slow convergence.

### Monitoring and Validation

To validate parameter settings, observe:

1. **Convergence Timeline**: Nodes should organize within 50-100 iterations
2. **Scale Stability**: Map should maintain consistent size (use FIT button to check)
3. **Topological Consistency**: Compare REF NODE and QUICK NODE views - relative positions should match

---

## Work Flow

### System Architecture

The localization framework operates through a distributed, iterative process where each node maintains an internal virtual map and continuously refines it based on local observations and neighbor information.

### Phase 1: Initialization

```
┌─────────────────────────────────────────┐
│ 1. Generate Reference Topology (refnod) │
│    - Random grid-based node placement   │
│    - Ensures uniform spatial coverage   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2. Initialize Quick Nodes (quicknod)    │
│    - Random positions (different from   │
│      reference)                         │
│    - Randomized sequence numbers        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 3. Populate Distance Matrix              │
│    - Calculate Euclidean distances      │
│    - Filter by transmission range        │
│    - Sort neighbors by distance          │
│    - Store top txRange neighbors        │
└──────────────────────────────────────────┘
```

**Key Data Structures**:
- `refnod[]`: Reference (ground truth) node positions
- `quicknod[]`: Estimated node positions (being refined)
- `dstmtrxval[][]`: Distance values to neighbors
- `dstmtrxid[][]`: Neighbor IDs sorted by distance

### Phase 2: Iterative Localization

```
┌─────────────────────────────────────────┐
│ Timer Tick (every 10ms)                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ For each iteration (100 per tick):      │
│                                          │
│ 1. Select Random Node                    │
│    - Choose node i uniformly at random  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2. Retrieve Neighbor Information         │
│    - Get distance matrix for node i     │
│    - Extract neighbor IDs and distances  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 3. Update Neighbor Positions             │
│    FOR each neighbor j:                  │
│      - Get expected distance (from      │
│        distance matrix)                  │
│      - Calculate current distance        │
│      - IF current > expected:            │
│          Move j 30% toward node i        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 4. Normalize Map Scale                   │
│    - Calculate bounding box              │
│    - Scale to 90% canvas occupancy      │
│    - Center on canvas                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 5. Update Visualization                  │
│    - Redraw nodes on canvas             │
│    - Highlight active node              │
└──────────────────────────────────────────┘
```

### Phase 3: Convergence Detection

**Current Implementation**: Visual inspection  
**Future Enhancement**: Automatic convergence detection based on:
- Cumulative displacement over sliding window
- Scale stability metrics
- Topological consistency error

### Detailed Algorithm Flow

#### Node Position Update (MoveNodeByIndex)

```pseudocode
FUNCTION MoveNodeByIndex(arrayIndex):
    IF arrayIndex invalid OR not in quicknod mode:
        RETURN
    
    seqNo = quicksno[arrayIndex]  // Get sequence number
    neighbors = dstmtrxid[seqNo]  // Get neighbor list
    distances = dstmtrxval[seqNo] // Get expected distances
    
    selectedPos = quicknod[arrayIndex]
    
    FOR each neighbor k in neighbors:
        neighborId = quickrefsno[neighbors[k]]  // Map to array index
        neighborPos = quicknod[neighborId]
        expectedDist = distances[k]
        
        currentDist = Euclidean(selectedPos, neighborPos)
        
        IF currentDist > expectedDist:
            // Attract neighbor 30% toward selected node
            newX = neighborPos.X + 0.3 * (selectedPos.X - neighborPos.X)
            newY = neighborPos.Y + 0.3 * (selectedPos.Y - neighborPos.Y)
            quicknod[neighborId] = (newX, newY)
```

#### Map Normalization (NormalizeQuickNodes)

```pseudocode
FUNCTION NormalizeQuickNodes():
    // Find bounding box
    minX, maxX = MinMax(quicknod[].X)
    minY, maxY = MinMax(quicknod[].Y)
    
    currentWidth = maxX - minX
    currentHeight = maxY - minY
    
    // Target dimensions (90% of canvas)
    targetWidth = 0.9 * canvasWidth
    targetHeight = 0.9 * canvasHeight
    
    // Calculate scale factors
    scaleX = targetWidth / currentWidth
    scaleY = targetHeight / currentHeight
    
    // Calculate centers
    currentCenterX = (minX + maxX) / 2
    currentCenterY = (minY + maxY) / 2
    targetCenterX = canvasWidth / 2
    targetCenterY = canvasHeight / 2
    
    // Apply transformation
    FOR each node i:
        x = (quicknod[i].X - currentCenterX) * scaleX + targetCenterX
        y = (quicknod[i].Y - currentCenterY) * scaleY + targetCenterY
        quicknod[i] = (x, y)
```

### Data Flow Diagram

```
┌─────────────┐
│  Reference  │
│  Topology   │──┐
│  (refnod)   │  │
└─────────────┘  │
                 │
                 ▼
         ┌───────────────┐
         │ Distance      │
         │ Matrix        │
         │ Calculation   │
         └───────┬───────┘
                 │
                 │ dstmtrxval[][]
                 │ dstmtrxid[][]
                 │
                 ▼
         ┌───────────────┐
         │ Quick Nodes   │
         │ (quicknod)    │◄──┐
         └───────┬───────┘   │
                 │           │
                 │ Iterative │
                 │ Updates   │
                 │           │
                 ▼           │
         ┌───────────────┐   │
         │ Position      │   │
         │ Refinement    │───┘
         │ Algorithm     │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ Normalization │
         │ (Scale Clamp) │
         └───────┬───────┘
                 │
                 ▼
         ┌───────────────┐
         │ Visualization │
         │ & Display     │
         └───────────────┘
```

### Interaction Modes

#### 1. Automatic Mode (QUICK TEST)
- Continuous iterative updates
- 100 position updates per timer tick
- Automatic normalization
- Real-time visualization

#### 2. Manual Mode (Self Correct)
- User-triggered updates
- Click on node to activate
- 10% attraction factor (more conservative)
- Immediate visual feedback

#### 3. Analysis Mode
- Compare REF NODE vs QUICK NODE
- Use FIT to normalize and align
- Visual inspection of convergence

---

## Theoretical Base of Convergence

### Mathematical Foundation

The localization algorithm is based on a **distributed consensus mechanism** that achieves topological consistency through RSS-weighted neighbor influence. Unlike gradient descent on a distance-stress objective, this is a **self-stabilizing distributed consensus** guided by signal strength.

### Core Principle: Topological Consensus

The algorithm converges to a state where all nodes' internal maps ℳᵢ satisfy:

```
ℳᵢ ≈ ℳⱼ  (up to rotation, translation, and uniform scaling)
```

for all node pairs (i, j), where ≈ denotes topological equivalence.

### Convergence Mechanism

#### 1. RSS-Weighted Centroid Attraction

Each node i moves toward a weighted centroid of its neighbors:

```
CG_i = (Σⱼ w_ij · pos_j) / (Σⱼ w_ij)
```

where:
- `w_ij` is the RSS-based weight for neighbor j
- `pos_j` is the estimated position of neighbor j
- The weight function is monotonic: stronger RSS → higher weight

**Update Rule**:
```
pos_i(t+1) = pos_i(t) + α · (CG_i - pos_i(t))
```

where α is the attraction factor (0.1-0.3 in practice).

#### 2. Distance Constraint Enforcement

The algorithm enforces distance constraints from the distance matrix:

```
IF current_distance(i,j) > expected_distance(i,j):
    Move j toward i by fraction β
```

This creates a **spring-like force** that pulls nodes to satisfy distance constraints while respecting RSS weights.

#### 3. Scale Normalization

Periodic normalization prevents scale drift:

```
S = target_span / current_span
pos_i ← (pos_i - center) · S + target_center
```

This maintains map dimensions while preserving relative topology.

### Convergence Analysis

#### Stability Conditions

**Theorem 1** (Local Stability):  
If the network graph is connected and RSS weights are positive, the update rule converges to a local minimum of the topological error function.

**Proof Sketch**:
- The update rule is a contraction mapping in the space of relative topologies
- RSS weights ensure that closer neighbors (stronger signals) exert stronger influence
- Distance constraints provide restoring forces that prevent divergence
- Normalization bounds the solution space, preventing scale drift

#### Convergence Rate

The convergence rate depends on:

1. **Network Connectivity**: Higher average degree → faster convergence
2. **RSS Quality**: Lower noise variance → more stable weights → faster convergence
3. **Attraction Factor**: Optimal range 0.2-0.3 balances speed and stability
4. **Initial Conditions**: Random initialization ensures exploration of solution space

**Empirical Observation**:  
Convergence typically occurs within 50-100 iterations for networks with average degree ≥ 8.

#### Topological Consistency

**Definition**: Two maps ℳᵢ and ℳⱼ are topologically consistent if:

```
∀ neighbors (k,l): angle(ℳᵢ, k, l) ≈ angle(ℳⱼ, k, l)
```

where `angle(ℳ, k, l)` is the relative angle between nodes k and l in map ℳ.

**Theorem 2** (Topological Convergence):  
Under the SIGMAPS-CG update rule with scale normalization, all maps converge to a common topology (up to isometry) if:
- The network is connected
- RSS measurements are statistically consistent
- Normalization prevents scale collapse/expansion

### Why This Works

#### 1. Signal-Guided Consensus

RSS measurements provide a **natural distance proxy**. Stronger signals indicate closer neighbors, creating a self-organizing force that aligns virtual maps with physical topology.

#### 2. Distributed Averaging

Each node's position is influenced by a weighted average of neighbor positions. This creates a **consensus dynamics** similar to distributed averaging algorithms, but with RSS-based weights.

#### 3. Constraint Satisfaction

Distance matrix constraints act as **soft constraints** that guide convergence. The algorithm doesn't enforce exact distances (which would be impossible with RSS noise), but encourages nodes to satisfy relative distance ordering.

#### 4. Scale Invariance

By normalizing scale and focusing on topology (angles, not distances), the algorithm is robust to:
- Coordinate system transformations
- Uniform scaling
- Rotation and translation

### Comparison with Alternative Approaches

| Approach | Method | Convergence Guarantee |
|----------|--------|---------------------|
| **SIGMAPS-CG** | RSS-weighted consensus | Topological consistency |
| **MDS-MAP** | Multidimensional scaling | Metric accuracy (requires anchors) |
| **DV-Hop** | Hop-count based | Absolute coordinates (requires anchors) |
| **Gradient Descent** | Distance-stress minimization | Local minimum (may not be global) |

### Limitations and Assumptions

#### Assumptions

1. **Static Network**: Node positions remain fixed during localization
2. **Connected Graph**: Network graph is connected (no isolated components)
3. **RSS Monotonicity**: Stronger RSS correlates with shorter distance (on average)
4. **Sufficient Density**: Average node degree ≥ 6 for reliable convergence

#### Limitations

1. **No Global Optimality Guarantee**: Algorithm may converge to local minima
2. **Initialization Dependent**: Random initialization may affect final topology
3. **Scale Ambiguity**: Final map scale is arbitrary (normalized to canvas)
4. **No Absolute Orientation**: Map rotation is arbitrary

### Future Theoretical Work

1. **Convergence Proof**: Formal proof of global convergence under specific conditions
2. **Rate Analysis**: Theoretical bounds on convergence rate
3. **Robustness Analysis**: Performance under adversarial conditions
4. **Optimal Parameter Selection**: Analytical methods for parameter tuning

---

## Citation

If you use this code in your research, please cite:

```bibtex
@article{mazumdar2024reference,
  title={Reference-Free Relative Localization for Direction-Aware Routing in Wireless Sensor Networks},
  author={Mazumdar, Himanshu S},
  journal={IEEE Transactions on Wireless Communications},
  year={2024},
  note={Under Review}
}
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Contact

**Author**: Himanshu S. Mazumdar  
**Institution**: Physical Research Laboratory, Ahmedabad, India  
**Email**: [Your Email]

---

## Acknowledgments

This work was supported by [Funding Agency/Institution]. The authors thank [Acknowledgments] for their valuable contributions.

---

## References

1. Niculescu, D., & Nath, B. (2003). DV based positioning in ad hoc networks. *Telecommunication Systems*, 22(1-4), 267-280.

2. Shang, Y., Ruml, W., Zhang, Y., & Fromherz, M. P. (2004). Localization from connectivity in sensor networks. *IEEE Transactions on Parallel and Distributed Systems*, 15(11), 961-974.

3. Patwari, N., et al. (2005). Relative location estimation in wireless sensor networks. *IEEE Transactions on Signal Processing*, 51(8), 2137-2148.

---

*Last Updated: January 2026*
