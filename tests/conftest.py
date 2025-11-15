"""
Pytest configuration and shared fixtures for ARCHOS test suite.

This module provides fixtures and utilities used across all tests.
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path


# ============================================================================
# SYNTHETIC DATA GENERATORS
# ============================================================================

@pytest.fixture
def random_seed():
    """Set random seed for reproducible tests."""
    np.random.seed(42)
    return 42


@pytest.fixture
def synthetic_fractal_cantor():
    """
    Generate a 1D Cantor set with known fractal dimension.

    The Cantor set has D₀ ≈ 0.631 (Hausdorff dimension).
    For correlation dimension in 1D embedding: D₂ ≈ 0.631
    """
    def generate(iterations=5):
        # Start with [0, 1]
        points = np.array([[0.0], [1.0]])

        for _ in range(iterations):
            # For each segment, remove middle third
            new_points = []
            sorted_points = np.sort(points.flatten())
            for i in range(len(sorted_points) - 1):
                left = sorted_points[i]
                right = sorted_points[i + 1]
                # Add left and right thirds
                new_points.extend([
                    left,
                    left + (right - left) / 3,
                    left + 2 * (right - left) / 3,
                    right
                ])
            points = np.unique(new_points).reshape(-1, 1)

        return points

    return generate


@pytest.fixture
def synthetic_uniform_2d():
    """
    Generate uniformly distributed points in 2D.

    Expected D₂ ≈ 2.0 (equals embedding dimension for uniform distribution)
    """
    def generate(n_points=1000, seed=42):
        np.random.seed(seed)
        return np.random.uniform(0, 1, (n_points, 2))

    return generate


@pytest.fixture
def synthetic_uniform_3d():
    """
    Generate uniformly distributed points in 3D.

    Expected D₂ ≈ 3.0 (equals embedding dimension)
    """
    def generate(n_points=1000, seed=42):
        np.random.seed(seed)
        return np.random.uniform(0, 1, (n_points, 3))

    return generate


@pytest.fixture
def synthetic_line_1d_in_2d():
    """
    Generate points along a line embedded in 2D space.

    Expected D₂ ≈ 1.0 (intrinsic dimension of a line)
    """
    def generate(n_points=1000, seed=42):
        np.random.seed(seed)
        t = np.linspace(0, 1, n_points)
        # Line y = x with small noise
        noise = np.random.normal(0, 0.01, n_points)
        points = np.column_stack([t, t + noise])
        return points

    return generate


@pytest.fixture
def synthetic_sierpinski_triangle():
    """
    Generate Sierpinski triangle with known fractal dimension.

    Expected D₂ ≈ log(3)/log(2) ≈ 1.585
    """
    def generate(iterations=8, seed=42):
        np.random.seed(seed)

        # Three vertices of equilateral triangle
        vertices = np.array([
            [0, 0],
            [1, 0],
            [0.5, np.sqrt(3)/2]
        ])

        # Start at random point
        point = np.random.rand(2)
        points = [point]

        # Chaos game: repeatedly move halfway to random vertex
        for _ in range(iterations * 1000):
            vertex = vertices[np.random.randint(3)]
            point = (point + vertex) / 2
            points.append(point.copy())

        return np.array(points)

    return generate


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_neutrino_data(tmp_path):
    """
    Create sample neutrino event data file for testing.

    Format: Energy(GeV) Zenith(radians)
    """
    data_file = tmp_path / "test_neutrino_data.dat"

    # Generate synthetic neutrino-like data
    np.random.seed(42)
    n_events = 500

    # Energy: log-normal distribution (GeV)
    energies = np.random.lognormal(mean=5, sigma=2, size=n_events)

    # Zenith: uniform in [0, π]
    zeniths = np.random.uniform(0, np.pi, size=n_events)

    # Write to file
    with open(data_file, 'w') as f:
        for e, z in zip(energies, zeniths):
            f.write(f"{e:.6e} {z:.6f}\n")

    return str(data_file)


@pytest.fixture
def sample_pdb_file(tmp_path):
    """
    Create minimal valid PDB file for testing.

    This is a very simple 3-residue alpha helix structure.
    """
    pdb_file = tmp_path / "test_protein.pdb"

    pdb_content = """HEADER    TEST PROTEIN
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N
ATOM      2  CA  ALA A   1       1.458   0.000   0.000  1.00  0.00           C
ATOM      3  C   ALA A   1       2.009   1.420   0.000  1.00  0.00           C
ATOM      4  O   ALA A   1       1.270   2.394   0.000  1.00  0.00           O
ATOM      5  CB  ALA A   1       1.989  -0.729  -1.232  1.00  0.00           C
ATOM      6  N   ALA A   2       3.332   1.523   0.000  1.00  0.00           N
ATOM      7  CA  ALA A   2       4.024   2.808   0.000  1.00  0.00           C
ATOM      8  C   ALA A   2       5.532   2.611   0.000  1.00  0.00           C
ATOM      9  O   ALA A   2       6.087   1.513   0.000  1.00  0.00           O
ATOM     10  CB  ALA A   2       3.618   3.617   1.232  1.00  0.00           C
ATOM     11  N   ALA A   3       6.228   3.741   0.000  1.00  0.00           N
ATOM     12  CA  ALA A   3       7.682   3.741   0.000  1.00  0.00           C
ATOM     13  C   ALA A   3       8.233   5.161   0.000  1.00  0.00           C
ATOM     14  O   ALA A   3       7.494   6.135   0.000  1.00  0.00           O
ATOM     15  CB  ALA A   3       8.213   2.989  -1.232  1.00  0.00           C
END
"""

    with open(pdb_file, 'w') as f:
        f.write(pdb_content)

    return str(pdb_file)


@pytest.fixture
def invalid_pdb_file(tmp_path):
    """Create malformed PDB file for testing error handling."""
    pdb_file = tmp_path / "invalid_protein.pdb"

    pdb_content = """HEADER    INVALID PDB
ATOM      1  N   ALA A   1       NOT_A_NUMBER   0.000   0.000  1.00  0.00           N
ATOM      2  CA  ALA A   1       ALSO_INVALID
"""

    with open(pdb_file, 'w') as f:
        f.write(pdb_content)

    return str(pdb_file)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@pytest.fixture
def assert_d2_in_range():
    """Helper to assert D2 value is within expected range with tolerance."""
    def _assert(calculated_d2, expected_d2, tolerance=0.2, message=""):
        """
        Assert that calculated D2 is within tolerance of expected value.

        Args:
            calculated_d2: The calculated correlation dimension
            expected_d2: The expected theoretical value
            tolerance: Absolute tolerance (default ±0.2)
            message: Optional custom message
        """
        error = abs(calculated_d2 - expected_d2)
        msg = (f"D2 mismatch: calculated={calculated_d2:.3f}, "
               f"expected={expected_d2:.3f}, error={error:.3f}, "
               f"tolerance={tolerance:.3f}")
        if message:
            msg = f"{message}: {msg}"

        assert error <= tolerance, msg

    return _assert


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide temporary directory for test outputs."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return str(output_dir)
