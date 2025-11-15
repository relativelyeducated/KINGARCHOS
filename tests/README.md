# ARCHOS Test Suite

This directory contains the test suite for the Dialectical Fractal Archestructure (DFA) codebase.

## Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and test configuration
├── unit/                           # Unit tests for individual functions/classes
│   ├── test_correlation_dimension.py     # Core D₂ algorithm tests
│   └── test_protein_d2_calculator.py     # Protein analysis tests
├── integration/                    # Integration tests for workflows
└── fixtures/                       # Test data files
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests
```bash
pytest tests/unit -m unit
```

### Run with coverage report
```bash
pytest --cov=code --cov=experiments --cov-report=html
```

### Run fast tests only (exclude slow tests)
```bash
pytest -m "not slow"
```

### Run specific test file
```bash
pytest tests/unit/test_correlation_dimension.py -v
```

### Run specific test function
```bash
pytest tests/unit/test_correlation_dimension.py::TestCorrelationDimension::test_uniform_2d_distribution -v
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (may be slower)
- `@pytest.mark.slow` - Slow tests (e.g., bootstrap with many iterations)
- `@pytest.mark.scientific` - Tests validating scientific correctness
- `@pytest.mark.requires_download` - Tests requiring external data downloads

### Running specific markers
```bash
pytest -m unit                    # Only unit tests
pytest -m "unit and not slow"     # Fast unit tests only
pytest -m integration             # Only integration tests
pytest -m scientific              # Only scientific validation tests
```

## Test Coverage

Current test coverage focuses on:

### 1. Core D₂ Calculation (`calculate_d2_icecube.py`)
- ✅ `calculate_correlation_dimension()` - Grassberger-Procaccia algorithm
- ✅ `calculate_d2_bootstrap()` - Bootstrap error estimation
- ✅ `load_icecube_data()` - Data loading and preprocessing
- ✅ `energy_stratified_d2()` - Energy-binned analysis
- ✅ `angular_correlation()` - Angular correlation analysis
- ✅ `cluster_analysis()` - DBSCAN clustering

### 2. Protein Analysis (`0527_python.py`)
- ✅ `ProteinD2Calculator.__init__()` - Initialization
- ✅ `download_pdb_structure()` - PDB file downloading
- ✅ `extract_coordinates()` - Coordinate extraction from PDB
- ✅ `calculate_correlation_integral()` - Correlation integral C(r)
- ✅ `fit_correlation_dimension()` - D₂ fitting from C(r)
- ✅ `analyze_protein()` - End-to-end protein analysis

### 3. Test Fixtures

Synthetic datasets with known fractal dimensions:

- **Uniform 2D/3D distributions** - D₂ equals embedding dimension
- **1D line in 2D space** - D₂ ≈ 1.0
- **Sierpinski triangle** - D₂ ≈ 1.585
- **Cantor set** - D₂ ≈ 0.631

## Coverage Goals

| Component | Current | Target |
|-----------|---------|--------|
| Core D₂ calculations | 85%+ | 90%+ |
| Protein analysis | 75%+ | 85%+ |
| Data processing | 60%+ | 75%+ |
| Overall | 70%+ | 80%+ |

## Adding New Tests

### 1. For new functions
```python
@pytest.mark.unit
def test_new_function():
    """Test description."""
    result = new_function(input_data)
    assert result == expected_value
```

### 2. For scientific validation
```python
@pytest.mark.scientific
def test_fractal_dimension_validation(assert_d2_in_range):
    """Test D₂ calculation on known fractal."""
    points = generate_known_fractal()
    d2, _ = calculate_correlation_dimension(points)
    assert_d2_in_range(d2, expected=1.585, tolerance=0.1)
```

### 3. For integration tests
```python
@pytest.mark.integration
def test_full_workflow():
    """Test complete analysis pipeline."""
    data = load_data()
    result = analyze(data)
    assert result['d2'] > 0
```

## Continuous Integration

Tests run automatically on:
- Every push to `main`, `develop`, or `claude/**` branches
- All pull requests
- Manual workflow dispatch

### CI Jobs:
1. **Test** - Run unit and integration tests on Python 3.8-3.11
2. **Test Slow** - Run slow tests on main branch only (Python 3.10)
3. **Lint** - Code quality checks (black, isort, flake8)
4. **Coverage Report** - Generate and upload coverage reports

## Test Data

### Sample Files
- `sample_neutrino_data.dat` - Synthetic neutrino events
- `sample_protein.pdb` - Minimal valid PDB structure
- `invalid_protein.pdb` - Malformed PDB for error testing

### Fixtures
Located in `conftest.py`:
- `synthetic_uniform_2d()` - Generate uniform 2D points
- `synthetic_uniform_3d()` - Generate uniform 3D points
- `synthetic_line_1d_in_2d()` - Generate line in 2D space
- `synthetic_sierpinski_triangle()` - Generate Sierpinski fractal
- `synthetic_fractal_cantor()` - Generate Cantor set
- `assert_d2_in_range()` - Helper for D₂ assertions

## Known Limitations

1. **Bootstrap tests** are marked as slow due to computational cost
2. **PDB download tests** require internet access (mocked in CI)
3. **Integration tests** may be flaky due to random sampling

## Troubleshooting

### Tests fail with import errors
```bash
# Ensure you're in the project root
cd /path/to/ARCHOS
pytest
```

### Coverage not working
```bash
# Install coverage plugin
pip install pytest-cov

# Run with coverage
pytest --cov=code --cov=experiments
```

### Slow tests taking too long
```bash
# Skip slow tests
pytest -m "not slow"
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing best practices](https://docs.python-guide.org/writing/tests/)
