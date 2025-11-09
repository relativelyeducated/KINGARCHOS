# Code: Analysis Scripts and Tools

**Computational tools for DFA theory validation**

---

## Overview

This directory contains all code used to analyze data and validate Dialectical Fractal Archestructure (DFA) predictions.

**Languages**: Python, JavaScript, Jupyter notebooks

**Primary Focus**: Correlation dimension (D₂) calculations

---

## Directory Structure

```
code/
├── python/              # Python analysis scripts
│   ├── calculate_d2_icecube.py  # Primary IceCube D₂ calculator
│   └── dfa_utils.py    # Shared utility functions (pending)
├── javascript/          # Web-based visualizations (pending)
├── notebooks/           # Jupyter analysis notebooks (pending)
└── README.md           # This file
```

---

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install -r ../requirements.txt
```

**Requirements**:
- Python 3.9+
- NumPy, SciPy, pandas, scikit-learn, Matplotlib

### Running IceCube Analysis

```bash
cd python/
python calculate_d2_icecube.py
```

**Expected Output**:
```
Measured D₂: 1.46 ± 0.07
Predicted D₂: 1.45 ± 0.10
Agreement: ✅ CONFIRMED
```

**Runtime**: ~30 seconds on standard laptop

---

## Main Scripts

### calculate_d2_icecube.py

**Purpose**: Calculate correlation dimension D₂ for IceCube neutrino events

**Input**: `data.dat` (Energy, Zenith columns)

**Output**:
- D₂ measurement with error bars
- Energy-stratified D₂ values
- Angular correlation analysis
- Cluster statistics
- Visualizations (PNG files)

**Key Functions**:
- `calculate_correlation_dimension()` - Grassberger-Procaccia algorithm
- `energy_stratified_d2()` - Stratified analysis
- `angular_correlation()` - Power-law fitting
- `cluster_analysis()` - DBSCAN clustering

**Algorithm**: Grassberger-Procaccia correlation integral
```python
C(r) = (1/N²) Σ Θ(r - |x_i - x_j|)
D₂ = d(log C) / d(log r)
```

**Configuration**: Edit constants at top of file
- `SAMPLE_SIZE = 10000` - Events to analyze
- `R_MIN, R_MAX` - Radius range
- `N_RADII = 50` - Number of radius values

---

## License

All code licensed under **CC-BY 4.0**. See LICENSE file.

**Contact**: relativelyeducated@gmail.com

**Repository**: https://github.com/relativelyeducated/dialectical-fractal-theory
