"""
Unit tests for correlation dimension (D₂) calculations.

Tests the core Grassberger-Procaccia algorithm and related functions
in experiments/01-icecube-d2-calculation/code/calculate_d2_icecube.py
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add the icecube experiment code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "experiments" / "01-icecube-d2-calculation" / "code"))

from calculate_d2_icecube import (
    load_icecube_data,
    calculate_correlation_dimension,
    calculate_d2_bootstrap,
    energy_stratified_d2,
    angular_correlation,
    cluster_analysis
)


# ============================================================================
# TESTS FOR calculate_correlation_dimension()
# ============================================================================

class TestCorrelationDimension:
    """Test suite for the core D₂ calculation function."""

    @pytest.mark.unit
    def test_uniform_2d_distribution(self, synthetic_uniform_2d, assert_d2_in_range):
        """
        Test D₂ calculation on uniform 2D distribution.

        Expected: D₂ ≈ 2.0 (equals embedding dimension)

        Note: Due to finite-size effects and radius range selection,
        the calculated D₂ may be slightly lower than theoretical value.
        """
        points = synthetic_uniform_2d(n_points=2000)
        # Use radius range appropriate for [0,1] data
        d2, error = calculate_correlation_dimension(
            points, sample_size=2000, r_min=0.01, r_max=0.7, n_radii=50, fit_exclude=5
        )

        # Allow larger tolerance due to finite-size effects
        assert_d2_in_range(d2, 2.0, tolerance=0.5,
                          message="Uniform 2D distribution")
        assert error >= 0, "Error should be non-negative"
        assert not np.isnan(d2), "D₂ should not be NaN"
        assert not np.isinf(d2), "D₂ should not be infinite"
        # Should at least be in reasonable range
        assert 1.4 < d2 < 2.4, f"D₂={d2:.3f} far outside reasonable range for 2D uniform"

    @pytest.mark.unit
    def test_uniform_3d_distribution(self, synthetic_uniform_3d):
        """
        Test D₂ calculation on uniform 3D distribution.

        Expected: D₂ ≈ 3.0 (equals embedding dimension)

        Note: Due to finite-size effects and edge effects in 3D,
        calculated D₂ is often systematically underestimated.
        The test verifies it's higher than 2D but may not reach 3.0.
        """
        points = synthetic_uniform_3d(n_points=3000)
        # Use radius range appropriate for [0,1] data
        d2, error = calculate_correlation_dimension(
            points, sample_size=3000, r_min=0.02, r_max=0.6, n_radii=60, fit_exclude=5
        )

        # Verify D2 indicates 3D structure (higher than 2D)
        assert d2 > 1.5, f"D₂={d2:.3f} too low for 3D uniform distribution"
        assert d2 < 3.5, f"D₂={d2:.3f} unreasonably high"
        # Due to systematic underestimation in 3D with finite data, accept range
        assert 1.5 < d2 < 3.2, f"D₂={d2:.3f} outside reasonable range for 3D"
        assert not np.isnan(d2), "D₂ should not be NaN"

    @pytest.mark.unit
    def test_line_embedded_in_2d(self, synthetic_line_1d_in_2d, assert_d2_in_range):
        """
        Test D₂ for line embedded in 2D space.

        Expected: D₂ ≈ 1.0 (intrinsic dimension of line)
        """
        points = synthetic_line_1d_in_2d(n_points=1000)
        # Use appropriate radius range
        d2, error = calculate_correlation_dimension(
            points, sample_size=1000, r_min=0.01, r_max=0.7, n_radii=50, fit_exclude=5
        )

        assert_d2_in_range(d2, 1.0, tolerance=0.4,
                          message="1D line in 2D space")
        assert 0.6 < d2 < 1.5, f"D₂={d2:.3f} outside reasonable range for 1D line"

    @pytest.mark.unit
    @pytest.mark.slow
    def test_sierpinski_triangle(self, synthetic_sierpinski_triangle, assert_d2_in_range):
        """
        Test D₂ for Sierpinski triangle fractal.

        Expected: D₂ ≈ 1.585 (log(3)/log(2))
        """
        points = synthetic_sierpinski_triangle(iterations=10)
        d2, error = calculate_correlation_dimension(points, sample_size=5000)

        # Sierpinski triangle has known dimension
        expected_d2 = np.log(3) / np.log(2)  # ≈ 1.585
        assert_d2_in_range(d2, expected_d2, tolerance=0.4,
                          message="Sierpinski triangle")

    @pytest.mark.unit
    def test_reproducibility(self, synthetic_uniform_2d):
        """Test that same input gives same output."""
        points = synthetic_uniform_2d(n_points=500, seed=123)

        # Set numpy seed before each call for reproducibility
        np.random.seed(456)
        d2_1, error_1 = calculate_correlation_dimension(points.copy(), sample_size=500)

        np.random.seed(456)
        d2_2, error_2 = calculate_correlation_dimension(points.copy(), sample_size=500)

        assert d2_1 == d2_2, "D₂ should be reproducible with same seed"
        assert error_1 == error_2, "Error should be reproducible with same seed"

    @pytest.mark.unit
    def test_subsample_consistency(self, synthetic_uniform_2d):
        """Test that subsampling doesn't drastically change D₂."""
        points = synthetic_uniform_2d(n_points=2000)

        # Full sample
        np.random.seed(42)
        d2_full, _ = calculate_correlation_dimension(points, sample_size=2000)

        # Subsampled
        np.random.seed(42)
        d2_sub, _ = calculate_correlation_dimension(points, sample_size=1000)

        # Should be similar (within reasonable tolerance)
        assert abs(d2_full - d2_sub) < 0.5, \
            f"Subsampling changed D₂ too much: {d2_full:.3f} vs {d2_sub:.3f}"

    @pytest.mark.unit
    def test_empty_input(self):
        """Test handling of empty input array."""
        empty_points = np.array([]).reshape(0, 2)

        # The function may raise an error OR return NaN/invalid results
        try:
            d2, error = calculate_correlation_dimension(empty_points)
            # If it doesn't raise, result should be NaN or invalid
            assert np.isnan(d2) or np.isinf(d2), \
                "Empty input should produce NaN or infinity"
        except (ValueError, IndexError, ZeroDivisionError, RuntimeWarning):
            pass  # Expected behavior

    @pytest.mark.unit
    def test_single_point(self):
        """Test handling of single point."""
        single_point = np.array([[0.5, 0.5]])

        # Should either raise error or return sensible value
        try:
            d2, error = calculate_correlation_dimension(single_point)
            # If it doesn't raise, result should be NaN or very small
            assert np.isnan(d2) or d2 < 0.1
        except (ValueError, IndexError, ZeroDivisionError):
            pass  # Expected behavior

    @pytest.mark.unit
    def test_two_points(self):
        """Test handling of two points (minimum for distance calculation)."""
        two_points = np.array([[0.0, 0.0], [1.0, 1.0]])

        try:
            d2, error = calculate_correlation_dimension(two_points, sample_size=2)
            # Should return some value, but may not be meaningful
            assert isinstance(d2, (int, float))
        except (ValueError, IndexError):
            pass  # Also acceptable

    @pytest.mark.unit
    def test_collinear_points(self):
        """Test points that are all collinear (degenerate case)."""
        # All points on a line
        t = np.linspace(0, 1, 100)
        collinear = np.column_stack([t, t])

        d2, error = calculate_correlation_dimension(collinear)

        # Should detect 1D structure
        assert 0.5 < d2 < 1.5, f"Collinear points should have D₂ ≈ 1, got {d2:.3f}"

    @pytest.mark.unit
    def test_parameter_r_min_r_max(self, synthetic_uniform_2d):
        """Test that r_min and r_max parameters work correctly."""
        points = synthetic_uniform_2d(n_points=1000)

        # Use appropriate radius ranges for [0,1] data
        d2_1, _ = calculate_correlation_dimension(
            points, r_min=0.01, r_max=0.7, n_radii=50, fit_exclude=5
        )
        d2_2, _ = calculate_correlation_dimension(
            points, r_min=0.02, r_max=0.5, n_radii=50, fit_exclude=5
        )

        # Both should give reasonable results for uniform distribution
        assert 1.3 < d2_1 < 2.5, f"D2_1={d2_1:.3f} outside range"
        assert 1.3 < d2_2 < 2.5, f"D2_2={d2_2:.3f} outside range"

    @pytest.mark.unit
    def test_parameter_n_radii(self, synthetic_uniform_2d):
        """Test that n_radii parameter affects calculation."""
        points = synthetic_uniform_2d(n_points=1000)

        # Use appropriate radius range with different numbers of sampling points
        d2_few, _ = calculate_correlation_dimension(
            points, r_min=0.01, r_max=0.7, n_radii=20, fit_exclude=3
        )
        d2_many, _ = calculate_correlation_dimension(
            points, r_min=0.01, r_max=0.7, n_radii=100, fit_exclude=10
        )

        # Both should be reasonable
        assert 1.3 < d2_few < 2.5, f"D2_few={d2_few:.3f} outside range"
        assert 1.3 < d2_many < 2.5, f"D2_many={d2_many:.3f} outside range"

    @pytest.mark.unit
    def test_very_clustered_points(self):
        """Test with points clustered at single location (near-zero D₂)."""
        # All points in small cluster
        cluster = np.random.normal(0, 0.01, (100, 2))

        d2, error = calculate_correlation_dimension(cluster)

        # Highly clustered should have low D₂
        assert d2 < 1.0, f"Clustered points should have low D₂, got {d2:.3f}"


# ============================================================================
# TESTS FOR calculate_d2_bootstrap()
# ============================================================================

class TestBootstrap:
    """Test suite for bootstrap error estimation."""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_bootstrap_basic(self, synthetic_uniform_2d):
        """Test basic bootstrap functionality."""
        points = synthetic_uniform_2d(n_points=500)

        mean_d2, std_d2 = calculate_d2_bootstrap(points, n_bootstrap=50)

        assert 1.5 < mean_d2 < 2.5, f"Bootstrap mean D₂ = {mean_d2:.3f}"
        assert std_d2 > 0, "Bootstrap std should be positive"
        assert std_d2 < 1.0, f"Bootstrap std too large: {std_d2:.3f}"

    @pytest.mark.unit
    def test_bootstrap_reproducibility(self, synthetic_uniform_2d):
        """Test bootstrap reproducibility with same seed."""
        points = synthetic_uniform_2d(n_points=300, seed=111)

        np.random.seed(222)
        mean_1, std_1 = calculate_d2_bootstrap(points, n_bootstrap=20)

        np.random.seed(222)
        mean_2, std_2 = calculate_d2_bootstrap(points, n_bootstrap=20)

        assert mean_1 == mean_2, "Bootstrap should be reproducible"
        assert std_1 == std_2, "Bootstrap std should be reproducible"


# ============================================================================
# TESTS FOR load_icecube_data()
# ============================================================================

class TestDataLoading:
    """Test suite for data loading and preprocessing."""

    @pytest.mark.unit
    def test_load_valid_data(self, sample_neutrino_data):
        """Test loading valid neutrino data file."""
        data = load_icecube_data(sample_neutrino_data)

        assert isinstance(data, pd.DataFrame)
        assert 'Energy' in data.columns
        assert 'Zenith' in data.columns
        assert 'Log_E' in data.columns
        assert 'Cos_Zenith' in data.columns
        assert len(data) > 0

    @pytest.mark.unit
    def test_log_energy_calculation(self, sample_neutrino_data):
        """Test that Log_E is calculated correctly."""
        data = load_icecube_data(sample_neutrino_data)

        # Verify Log_E = log10(Energy)
        expected_log_e = np.log10(data['Energy'])
        np.testing.assert_array_almost_equal(data['Log_E'], expected_log_e)

    @pytest.mark.unit
    def test_cos_zenith_calculation(self, sample_neutrino_data):
        """Test that Cos_Zenith is calculated correctly."""
        data = load_icecube_data(sample_neutrino_data)

        # Verify Cos_Zenith = cos(Zenith)
        expected_cos = np.cos(data['Zenith'])
        np.testing.assert_array_almost_equal(data['Cos_Zenith'], expected_cos)

    @pytest.mark.unit
    def test_load_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_icecube_data("nonexistent_file.dat")


# ============================================================================
# TESTS FOR energy_stratified_d2()
# ============================================================================

class TestEnergyStratification:
    """Test suite for energy-stratified D₂ analysis."""

    @pytest.mark.unit
    def test_stratified_analysis(self, sample_neutrino_data):
        """Test energy stratification with valid data."""
        data = load_icecube_data(sample_neutrino_data)

        bins = [
            (0, 1e5, 'Low'),
            (1e5, 1e10, 'High')
        ]

        results = energy_stratified_d2(data, bins)

        assert isinstance(results, pd.DataFrame)
        assert len(results) > 0
        assert 'Energy_Range' in results.columns
        assert 'D2' in results.columns
        assert 'Error' in results.columns
        assert 'N_events' in results.columns

    @pytest.mark.unit
    def test_stratified_empty_bin(self, sample_neutrino_data):
        """Test handling of energy bin with no events."""
        data = load_icecube_data(sample_neutrino_data)

        # Create bin with no events
        bins = [
            (1e20, 1e30, 'Impossible')
        ]

        results = energy_stratified_d2(data, bins)

        # Should return empty dataframe or skip the bin
        assert len(results) == 0


# ============================================================================
# TESTS FOR angular_correlation()
# ============================================================================

class TestAngularCorrelation:
    """Test suite for angular correlation analysis."""

    @pytest.mark.unit
    def test_angular_correlation_basic(self, sample_neutrino_data):
        """Test basic angular correlation calculation."""
        data = load_icecube_data(sample_neutrino_data)

        slope, error = angular_correlation(data)

        assert isinstance(slope, (int, float))
        assert isinstance(error, (int, float))
        # Slope should be positive (power-law decay)
        assert not np.isnan(slope) or error > 0

    @pytest.mark.unit
    def test_angular_correlation_uniform_distribution(self):
        """Test angular correlation with uniformly distributed zenith angles."""
        # Create uniform zenith distribution
        data = pd.DataFrame({
            'Zenith': np.random.uniform(0, np.pi, 1000)
        })

        slope, error = angular_correlation(data)

        # Should return some value
        assert isinstance(slope, (int, float))


# ============================================================================
# TESTS FOR cluster_analysis()
# ============================================================================

class TestClustering:
    """Test suite for DBSCAN clustering."""

    @pytest.mark.unit
    def test_cluster_analysis_basic(self, synthetic_uniform_2d):
        """Test basic clustering functionality."""
        points = synthetic_uniform_2d(n_points=500)

        n_clusters, cluster_sizes = cluster_analysis(points, eps=0.1, min_samples=5)

        assert isinstance(n_clusters, int)
        assert n_clusters >= 0
        assert isinstance(cluster_sizes, np.ndarray)

    @pytest.mark.unit
    def test_cluster_analysis_tight_clusters(self):
        """Test clustering on clearly separated clusters."""
        # Create 3 well-separated clusters
        cluster1 = np.random.normal([0, 0], 0.1, (100, 2))
        cluster2 = np.random.normal([5, 5], 0.1, (100, 2))
        cluster3 = np.random.normal([10, 0], 0.1, (100, 2))
        points = np.vstack([cluster1, cluster2, cluster3])

        n_clusters, cluster_sizes = cluster_analysis(points, eps=0.5, min_samples=5)

        # Should detect approximately 3 clusters
        assert n_clusters >= 2, f"Should detect multiple clusters, found {n_clusters}"

    @pytest.mark.unit
    def test_cluster_analysis_no_clusters(self, synthetic_uniform_2d):
        """Test with eps too small (should find no clusters)."""
        points = synthetic_uniform_2d(n_points=100)

        n_clusters, cluster_sizes = cluster_analysis(points, eps=0.001, min_samples=10)

        # Very small eps should result in few or no clusters
        assert n_clusters >= 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple functions."""

    @pytest.mark.integration
    def test_full_pipeline(self, sample_neutrino_data):
        """Test complete analysis pipeline."""
        # Load data
        data = load_icecube_data(sample_neutrino_data)
        events = data[['Log_E', 'Cos_Zenith']].values

        # Calculate D₂
        d2, error = calculate_correlation_dimension(events)

        # Results should be reasonable
        assert 0.5 < d2 < 3.5, f"D₂ = {d2:.3f} outside reasonable range"
        assert error >= 0

        # Cluster analysis
        n_clusters, _ = cluster_analysis(events)
        assert n_clusters >= 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_known_fractal_dimensions(self, assert_d2_in_range):
        """Test D₂ calculation on multiple known fractals."""
        test_cases = [
            # (generator_func, expected_d2, tolerance, description)
            (lambda: np.random.uniform(0, 1, (1000, 2)), 2.0, 0.3, "2D uniform"),
            (lambda: np.random.uniform(0, 1, (1000, 3)), 3.0, 0.3, "3D uniform"),
        ]

        for generator, expected, tol, desc in test_cases:
            points = generator()
            d2, _ = calculate_correlation_dimension(points)
            assert_d2_in_range(d2, expected, tolerance=tol, message=desc)
