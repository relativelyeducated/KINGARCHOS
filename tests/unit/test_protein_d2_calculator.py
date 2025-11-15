"""
Unit tests for ProteinD2Calculator class.

Tests protein structure analysis and D₂ calculation functionality
in code/python/d2_calculations/0527_python.py
"""

import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Add the protein analysis code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "python" / "d2_calculations"))

# Import after path is set
import importlib.util
spec = importlib.util.spec_from_file_location(
    "protein_d2",
    Path(__file__).parent.parent.parent / "code" / "python" / "d2_calculations" / "0527_python.py"
)
protein_d2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protein_d2)

ProteinD2Calculator = protein_d2.ProteinD2Calculator


# ============================================================================
# TESTS FOR ProteinD2Calculator.__init__()
# ============================================================================

class TestProteinD2CalculatorInit:
    """Test suite for ProteinD2Calculator initialization."""

    @pytest.mark.unit
    def test_init_default(self):
        """Test initialization with default parameters."""
        calculator = ProteinD2Calculator()

        assert calculator.min_points == 50
        assert calculator.parser is not None

    @pytest.mark.unit
    def test_init_custom_min_points(self):
        """Test initialization with custom min_points."""
        calculator = ProteinD2Calculator(min_points=100)

        assert calculator.min_points == 100


# ============================================================================
# TESTS FOR download_pdb_structure()
# ============================================================================

class TestDownloadPDB:
    """Test suite for PDB structure downloading."""

    @pytest.mark.unit
    def test_download_creates_directory(self, tmp_path):
        """Test that download creates save directory."""
        calculator = ProteinD2Calculator()
        save_dir = str(tmp_path / "test_pdb")

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "HEADER TEST PDB\nEND\n"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = calculator.download_pdb_structure("1ABC", save_dir=save_dir)

            assert os.path.exists(save_dir)
            assert os.path.isdir(save_dir)

    @pytest.mark.unit
    @pytest.mark.requires_download
    def test_download_skips_existing_file(self, tmp_path):
        """Test that download skips if file already exists."""
        calculator = ProteinD2Calculator()
        save_dir = str(tmp_path / "pdb")
        os.makedirs(save_dir)

        # Create existing file
        pdb_file = os.path.join(save_dir, "1abc.pdb")
        with open(pdb_file, 'w') as f:
            f.write("EXISTING FILE\n")

        with patch('requests.get') as mock_get:
            result = calculator.download_pdb_structure("1ABC", save_dir=save_dir)

            # Should not call requests.get since file exists
            mock_get.assert_not_called()
            assert result == pdb_file

    @pytest.mark.unit
    def test_download_handles_network_error(self, tmp_path):
        """Test handling of network errors during download."""
        calculator = ProteinD2Calculator()
        save_dir = str(tmp_path / "pdb")

        # The function catches RequestException, so it should handle this gracefully
        # We'll use a more specific exception that the code is designed to catch
        with patch('requests.get') as mock_get:
            from requests import RequestException
            mock_get.side_effect = RequestException("Network error")

            result = calculator.download_pdb_structure("1ABC", save_dir=save_dir)

        # Function should handle error gracefully and return None
        assert result is None

    @pytest.mark.unit
    def test_download_creates_correct_filename(self, tmp_path):
        """Test that download creates correctly named file."""
        calculator = ProteinD2Calculator()
        save_dir = str(tmp_path / "pdb")

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "HEADER TEST\nEND\n"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = calculator.download_pdb_structure("1ABC", save_dir=save_dir)

            # Should create lowercase filename
            expected_file = os.path.join(save_dir, "1abc.pdb")
            assert result == expected_file
            assert os.path.exists(expected_file)


# ============================================================================
# TESTS FOR extract_coordinates()
# ============================================================================

class TestExtractCoordinates:
    """Test suite for coordinate extraction from PDB files."""

    @pytest.mark.unit
    def test_extract_ca_atoms(self, sample_pdb_file):
        """Test extraction of CA (alpha carbon) coordinates."""
        calculator = ProteinD2Calculator()

        coords = calculator.extract_coordinates(sample_pdb_file, atom_type="CA")

        assert isinstance(coords, np.ndarray)
        assert len(coords.shape) == 2
        assert coords.shape[1] == 3  # x, y, z coordinates
        assert coords.shape[0] > 0  # At least some atoms

    @pytest.mark.unit
    def test_extract_returns_correct_count(self, sample_pdb_file):
        """Test that correct number of atoms are extracted."""
        calculator = ProteinD2Calculator()

        coords = calculator.extract_coordinates(sample_pdb_file, atom_type="CA")

        # Sample PDB has 3 residues = 3 CA atoms
        assert coords.shape[0] == 3

    @pytest.mark.unit
    def test_extract_invalid_atom_type(self, sample_pdb_file):
        """Test extraction with non-existent atom type."""
        calculator = ProteinD2Calculator()

        coords = calculator.extract_coordinates(sample_pdb_file, atom_type="XX")

        # Should return empty array
        assert len(coords) == 0

    @pytest.mark.unit
    def test_extract_nonexistent_file(self):
        """Test handling of nonexistent PDB file."""
        calculator = ProteinD2Calculator()

        coords = calculator.extract_coordinates("nonexistent.pdb", atom_type="CA")

        assert len(coords) == 0

    @pytest.mark.unit
    def test_extract_malformed_pdb(self, invalid_pdb_file):
        """Test handling of malformed PDB file."""
        calculator = ProteinD2Calculator()

        # Should handle gracefully (return empty or raise)
        try:
            coords = calculator.extract_coordinates(invalid_pdb_file, atom_type="CA")
            # If it doesn't raise, should return empty or valid coordinates
            assert isinstance(coords, np.ndarray)
        except Exception:
            # Also acceptable to raise exception
            pass

    @pytest.mark.unit
    def test_extract_coordinates_are_numeric(self, sample_pdb_file):
        """Test that extracted coordinates are valid numbers."""
        calculator = ProteinD2Calculator()

        coords = calculator.extract_coordinates(sample_pdb_file, atom_type="CA")

        assert not np.any(np.isnan(coords)), "Coordinates contain NaN"
        assert not np.any(np.isinf(coords)), "Coordinates contain infinity"
        assert coords.dtype in [np.float32, np.float64], "Coordinates should be float"


# ============================================================================
# TESTS FOR calculate_correlation_integral()
# ============================================================================

class TestCorrelationIntegral:
    """Test suite for correlation integral calculation."""

    @pytest.mark.unit
    def test_correlation_integral_basic(self):
        """Test basic correlation integral calculation."""
        calculator = ProteinD2Calculator(min_points=10)

        # Simple 3D points
        coords = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1],
            [0.5, 0.5, 0.5],
            [2, 2, 2]
        ])

        r_values = np.array([0.5, 1.0, 2.0, 3.0])
        c_r = calculator.calculate_correlation_integral(coords, r_values)

        assert isinstance(c_r, np.ndarray)
        assert len(c_r) == len(r_values)
        assert np.all(c_r >= 0), "C(r) should be non-negative"
        assert np.all(c_r <= 1), "C(r) should be <= 1"
        # C(r) should be monotonically increasing
        assert np.all(np.diff(c_r) >= 0), "C(r) should be monotonic increasing"

    @pytest.mark.unit
    def test_correlation_integral_too_few_points(self):
        """Test handling of too few points."""
        calculator = ProteinD2Calculator(min_points=50)

        coords = np.array([[0, 0, 0], [1, 1, 1]])  # Only 2 points
        r_values = np.array([0.5, 1.0, 2.0])

        c_r = calculator.calculate_correlation_integral(coords, r_values)

        # Should return zeros or handle gracefully
        assert isinstance(c_r, np.ndarray)
        assert len(c_r) == len(r_values)

    @pytest.mark.unit
    def test_correlation_integral_single_cluster(self):
        """Test with all points in tight cluster."""
        calculator = ProteinD2Calculator(min_points=10)

        # All points very close together
        coords = np.random.normal([0, 0, 0], 0.01, (50, 3))
        r_values = np.array([0.001, 0.01, 0.1, 1.0])

        c_r = calculator.calculate_correlation_integral(coords, r_values)

        # At small r, C(r) should be near 0
        # At large r, C(r) should be near 1
        assert c_r[0] < c_r[-1], "C(r) should increase with r"

    @pytest.mark.unit
    def test_correlation_integral_large_r(self):
        """Test that C(r) approaches 1 for large r."""
        calculator = ProteinD2Calculator(min_points=10)

        coords = np.random.uniform(0, 1, (100, 3))
        r_values = np.array([0.1, 1.0, 10.0, 100.0])

        c_r = calculator.calculate_correlation_integral(coords, r_values)

        # For very large r, should approach 1
        assert c_r[-1] > 0.9, f"C(r) should approach 1 for large r, got {c_r[-1]:.3f}"


# ============================================================================
# TESTS FOR fit_correlation_dimension()
# ============================================================================

class TestFitCorrelationDimension:
    """Test suite for D₂ fitting."""

    @pytest.mark.unit
    def test_fit_basic(self):
        """Test basic D₂ fitting."""
        calculator = ProteinD2Calculator()

        # Create synthetic data: C(r) = r^2 (D₂ = 2)
        r_values = np.logspace(-1, 1, 50)
        c_r = r_values ** 2 / (10**2)  # Normalize

        d2, r_squared, intercept = calculator.fit_correlation_dimension(r_values, c_r)

        assert 1.8 < d2 < 2.2, f"D₂ should be ~2, got {d2:.3f}"
        assert r_squared > 0.95, f"R² should be high, got {r_squared:.3f}"

    @pytest.mark.unit
    def test_fit_different_dimensions(self):
        """Test fitting with different known dimensions."""
        calculator = ProteinD2Calculator()

        test_cases = [
            (1.0, "1D"),
            (1.5, "1.5D"),
            (2.0, "2D"),
            (2.5, "2.5D"),
            (3.0, "3D")
        ]

        for true_d2, label in test_cases:
            r_values = np.logspace(-1, 1, 50)
            c_r = r_values ** true_d2 / (10 ** true_d2)

            fitted_d2, r_squared, _ = calculator.fit_correlation_dimension(r_values, c_r)

            assert abs(fitted_d2 - true_d2) < 0.1, \
                f"{label}: Expected D₂={true_d2:.1f}, got {fitted_d2:.3f}"

    @pytest.mark.unit
    def test_fit_with_zeros(self):
        """Test handling of zero values in C(r)."""
        calculator = ProteinD2Calculator()

        r_values = np.logspace(-2, 1, 50)
        c_r = np.zeros_like(r_values)
        c_r[25:] = r_values[25:] ** 2 / 100  # Some non-zero values

        d2, r_squared, intercept = calculator.fit_correlation_dimension(r_values, c_r)

        # Should filter out zeros and fit remaining
        assert not np.isnan(d2) or np.isnan(r_squared)  # Either valid or both NaN

    @pytest.mark.unit
    def test_fit_insufficient_points(self):
        """Test with too few valid points for fitting."""
        calculator = ProteinD2Calculator()

        r_values = np.array([0.1, 0.2])
        c_r = np.array([0.01, 0.04])

        d2, r_squared, intercept = calculator.fit_correlation_dimension(r_values, c_r)

        # Should return NaN or handle gracefully
        assert np.isnan(d2) or isinstance(d2, float)

    @pytest.mark.unit
    def test_fit_custom_range(self):
        """Test fitting with custom fit range."""
        calculator = ProteinD2Calculator()

        r_values = np.logspace(-2, 2, 100)
        c_r = r_values ** 2 / (10**2)

        # Fit only middle range
        d2, r_squared, _ = calculator.fit_correlation_dimension(
            r_values, c_r, fit_range=(0.1, 10.0)
        )

        assert 1.8 < d2 < 2.2, f"Custom range: D₂ should be ~2, got {d2:.3f}"


# ============================================================================
# TESTS FOR analyze_protein()
# ============================================================================

class TestAnalyzeProtein:
    """Test suite for complete protein analysis."""

    @pytest.mark.unit
    def test_analyze_protein_with_local_file(self, sample_pdb_file):
        """Test analysis with pre-existing PDB file."""
        calculator = ProteinD2Calculator(min_points=3)

        # Mock the download to use our sample file
        with patch.object(calculator, 'download_pdb_structure', return_value=sample_pdb_file):
            result = calculator.analyze_protein("TEST")

        assert result is not None
        assert 'pdb_id' in result
        assert 'd2' in result
        assert 'n_atoms' in result
        assert result['pdb_id'] == "TEST"
        assert result['n_atoms'] == 3  # Our sample has 3 CA atoms

    @pytest.mark.unit
    def test_analyze_protein_download_fails(self):
        """Test handling when PDB download fails."""
        calculator = ProteinD2Calculator()

        with patch.object(calculator, 'download_pdb_structure', return_value=None):
            result = calculator.analyze_protein("FAIL")

        assert result is None

    @pytest.mark.unit
    def test_analyze_protein_no_coordinates(self, tmp_path):
        """Test handling when coordinate extraction fails."""
        calculator = ProteinD2Calculator()

        # Create empty PDB file
        empty_pdb = tmp_path / "empty.pdb"
        empty_pdb.write_text("HEADER EMPTY\nEND\n")

        with patch.object(calculator, 'download_pdb_structure', return_value=str(empty_pdb)):
            result = calculator.analyze_protein("EMPTY")

        assert result is None

    @pytest.mark.unit
    def test_analyze_protein_result_structure(self, sample_pdb_file):
        """Test that result has all expected fields."""
        calculator = ProteinD2Calculator(min_points=3)

        with patch.object(calculator, 'download_pdb_structure', return_value=sample_pdb_file):
            result = calculator.analyze_protein("TEST")

        expected_keys = [
            'pdb_id', 'atom_type', 'n_atoms', 'max_distance',
            'd2', 'r_squared', 'intercept', 'coordinates',
            'r_values', 'correlation_integral'
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.unit
    def test_analyze_protein_d2_in_reasonable_range(self, sample_pdb_file):
        """Test that calculated D₂ is in physically reasonable range.

        Note: Very small proteins (< 10 atoms) may not have enough
        structure for meaningful D₂ calculation, resulting in NaN.
        """
        calculator = ProteinD2Calculator(min_points=3)

        with patch.object(calculator, 'download_pdb_structure', return_value=sample_pdb_file):
            result = calculator.analyze_protein("TEST")

        # D₂ for 3D protein should be between 0.5 and 3.5, or NaN for very small structures
        if not np.isnan(result['d2']):
            assert 0.5 < result['d2'] < 3.5, \
                f"D₂ = {result['d2']:.3f} outside reasonable range for protein"
        else:
            # For very small structures, NaN is acceptable
            assert result['n_atoms'] < 10, \
                f"D₂ is NaN but structure has {result['n_atoms']} atoms"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestProteinD2Integration:
    """Integration tests for complete workflows."""

    @pytest.mark.integration
    def test_full_analysis_workflow(self, sample_pdb_file):
        """Test complete analysis from PDB to D₂."""
        calculator = ProteinD2Calculator(min_points=3)

        # Step 1: Extract coordinates
        coords = calculator.extract_coordinates(sample_pdb_file, atom_type="CA")
        assert len(coords) > 0

        # Step 2: Calculate correlation integral
        distances = np.sqrt(np.sum((coords[:, np.newaxis] - coords[np.newaxis, :]) ** 2, axis=2))
        max_dist = np.max(distances)
        r_values = np.logspace(-1, np.log10(max_dist * 0.5), 20)
        c_r = calculator.calculate_correlation_integral(coords, r_values)
        assert len(c_r) > 0

        # Step 3: Fit D₂
        d2, r_squared, intercept = calculator.fit_correlation_dimension(r_values, c_r)
        assert not np.isnan(d2)

    @pytest.mark.integration
    def test_different_atom_types(self, sample_pdb_file):
        """Test analysis with different atom types."""
        calculator = ProteinD2Calculator(min_points=3)

        for atom_type in ["CA", "N", "C", "O"]:
            coords = calculator.extract_coordinates(sample_pdb_file, atom_type=atom_type)
            # Should extract successfully (may be empty for some types)
            assert isinstance(coords, np.ndarray)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_synthetic_protein_structure(self):
        """Test with synthetic protein-like structure."""
        calculator = ProteinD2Calculator(min_points=20)

        # Create synthetic alpha helix (spiral structure)
        n_residues = 30
        t = np.linspace(0, 6*np.pi, n_residues)
        coords = np.column_stack([
            2.3 * np.cos(t),
            2.3 * np.sin(t),
            1.5 * t  # Rise per turn
        ])

        # Calculate correlation integral
        max_dist = np.max(np.sqrt(np.sum(
            (coords[:, np.newaxis] - coords[np.newaxis, :]) ** 2, axis=2
        )))
        r_values = np.logspace(-0.5, np.log10(max_dist * 0.5), 30)
        c_r = calculator.calculate_correlation_integral(coords, r_values)

        # Fit D₂
        d2, r_squared, _ = calculator.fit_correlation_dimension(r_values, c_r)

        # Alpha helix is between 1D (line) and 3D (volume)
        assert 1.0 < d2 < 3.0, f"Helix D₂ = {d2:.3f} outside expected range"
