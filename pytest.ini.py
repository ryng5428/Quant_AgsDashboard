# =============================================================================
# File: pytest.ini (PyTest Configuration File)
# addopts
    # a configuration option used to specify default command-line options that are automatically applied when running pytest.
    # This allows you to set up a consistent testing environment without repeatedly typing the same options on the command line.
# =============================================================================
"""
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --durations=10
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    parametrize: marks parametrized tests
"""

