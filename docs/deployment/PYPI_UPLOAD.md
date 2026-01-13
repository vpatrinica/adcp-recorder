# PyPI Upload Guide - ADCP Recorder

This guide provides step-by-step instructions for uploading the ADCP Recorder package to PyPI (Python Package Index).

## Prerequisites

Before uploading to PyPI, ensure you have:

- [ ] A PyPI account (create at https://pypi.org/account/register/)
- [ ] A TestPyPI account for testing (create at https://test.pypi.org/account/register/)
- [ ] API tokens configured for both PyPI and TestPyPI
- [ ] All tests passing
- [ ] Documentation complete and reviewed
- [ ] CHANGELOG.md updated with release notes
- [ ] Version number updated in `pyproject.toml` and `adcp_recorder/__init__.py`

---

## Step 1: Update Package Metadata

### 1.1 Update Author Information

Edit `pyproject.toml` and replace placeholder author information:

```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"},
]
```

**Action**: Replace with actual author name and email.

### 1.2 Verify Version Number

Ensure version is consistent across files:

- `pyproject.toml`: `version = "0.1.0"`
- `adcp_recorder/__init__.py`: `__version__ = "0.1.0"`

**Action**: Update version if needed (follow semantic versioning).

### 1.3 Review Package URLs

Verify all URLs in `pyproject.toml` are correct:

```toml
[project.urls]
Homepage = "https://github.com/vpatrinica/adcp-recorder"
Documentation = "https://github.com/vpatrinica/adcp-recorder/tree/main/docs"
Repository = "https://github.com/vpatrinica/adcp-recorder"
Issues = "https://github.com/vpatrinica/adcp-recorder/issues"
Changelog = "https://github.com/vpatrinica/adcp-recorder/blob/main/CHANGELOG.md"
```

**Action**: Verify URLs are accessible.

---

## Step 2: Install Required Tools

Install build and upload tools:

```bash
# Install build tools
pip install --upgrade build

# Install twine for uploading
pip install --upgrade twine

# Verify installations
python -m build --version
twine --version
```

**Expected Output**:
```
build 1.0.0
twine version 5.0.0
```

---

## Step 3: Run Quality Checks

### 3.1 Run All Tests

```bash
# Run full test suite
pytest

# Run with coverage
pytest --cov=adcp_recorder --cov-report=term-missing

# Ensure 100% pass rate
```

**Action**: Fix any failing tests before proceeding.

### 3.2 Run Linting

```bash
# Install ruff if not already installed
pip install ruff

# Run linting
ruff check adcp_recorder/

# Fix any issues
ruff check --fix adcp_recorder/
```

**Action**: Resolve all linting errors.

### 3.3 Verify Package Structure

```bash
# Check that all required files exist
ls -la README.md LICENSE CHANGELOG.md pyproject.toml
ls -la adcp_recorder/__init__.py
ls -la adcp_recorder/templates/linux/
ls -la adcp_recorder/templates/windows/
```

**Action**: Ensure all files are present.

---

## Step 4: Build the Package

### 4.1 Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info
rm -rf adcp_recorder.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

### 4.2 Build Distribution Packages

```bash
# Build wheel and source distribution
python -m build

# Verify build artifacts
ls -lh dist/
```

**Expected Output**:
```
dist/
├── adcp_recorder-0.1.0-py3-none-any.whl
└── adcp_recorder-0.1.0.tar.gz
```

### 4.3 Verify Package Contents

```bash
# Check wheel contents
unzip -l dist/adcp_recorder-0.1.0-py3-none-any.whl

# Verify metadata
python -m twine check dist/*
```

**Expected Output**:
```
Checking dist/adcp_recorder-0.1.0-py3-none-any.whl: PASSED
Checking dist/adcp_recorder-0.1.0.tar.gz: PASSED
```

**Action**: Fix any warnings or errors before proceeding.

---

## Step 5: Test Upload to TestPyPI

### 5.1 Configure TestPyPI Credentials

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**Action**: Replace tokens with your actual API tokens from:
- PyPI: https://pypi.org/manage/account/token/
- TestPyPI: https://test.pypi.org/manage/account/token/

**Security Note**: Keep this file secure with `chmod 600 ~/.pypirc`

### 5.2 Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Enter credentials if not using API token
```

**Expected Output**:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading adcp_recorder-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.0/50.0 kB • 00:00
Uploading adcp_recorder-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.0/45.0 kB • 00:00

View at:
https://test.pypi.org/project/adcp-recorder/0.1.0/
```

### 5.3 Test Installation from TestPyPI

```bash
# Create a clean virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ adcp-recorder

# Verify installation
adcp-recorder --help
python -c "import adcp_recorder; print(adcp_recorder.__version__)"

# Test basic functionality
adcp-recorder list-ports
adcp-recorder status

# Cleanup
deactivate
rm -rf test-env
```

**Action**: Verify package installs and runs correctly. Fix any issues and repeat from Step 4.

---

## Step 6: Upload to PyPI (Production)

### 6.1 Final Pre-Upload Checklist

- [ ] All tests passing
- [ ] TestPyPI upload successful and tested
- [ ] Version number is correct and not already published
- [ ] CHANGELOG.md updated
- [ ] README.md reviewed and accurate
- [ ] Author information correct
- [ ] All URLs verified
- [ ] License file present
- [ ] Git repository tagged with version

### 6.2 Create Git Tag

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag to remote
git push origin v0.1.0

# Verify tag
git tag -l
```

### 6.3 Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Enter credentials if not using API token
```

**Expected Output**:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading adcp_recorder-0.1.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.0/50.0 kB • 00:00
Uploading adcp_recorder-0.1.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.0/45.0 kB • 00:00

View at:
https://pypi.org/project/adcp-recorder/0.1.0/
```

**⚠️ WARNING**: This step is irreversible. You cannot delete or replace a version once uploaded to PyPI.

---

## Step 7: Verify Production Upload

### 7.1 Check PyPI Project Page

Visit: https://pypi.org/project/adcp-recorder/

Verify:
- [ ] Version number is correct
- [ ] Description renders correctly
- [ ] All metadata is accurate
- [ ] Links work correctly
- [ ] README displays properly

### 7.2 Test Installation from PyPI

```bash
# Create a clean virtual environment
python -m venv verify-env
source verify-env/bin/activate  # On Windows: verify-env\Scripts\activate

# Install from PyPI
pip install adcp-recorder

# Verify installation
adcp-recorder --help
python -c "import adcp_recorder; print(adcp_recorder.__version__)"

# Test functionality
adcp-recorder list-ports
adcp-recorder status

# Cleanup
deactivate
rm -rf verify-env
```

### 7.3 Test on Different Platforms

Test installation on:
- [ ] Linux (Ubuntu/Debian)
- [ ] Linux (RHEL/Fedora)
- [ ] Windows 10/11
- [ ] macOS (if applicable)

---

## Step 8: Post-Release Tasks

### 8.1 Create GitHub Release

1. Go to: https://github.com/vpatrinica/adcp-recorder/releases/new
2. Select tag: `v0.1.0`
3. Release title: `ADCP Recorder v0.1.0`
4. Description: Copy from CHANGELOG.md
5. Attach build artifacts (optional):
   - `adcp_recorder-0.1.0-py3-none-any.whl`
   - `adcp_recorder-0.1.0.tar.gz`
   - `SHA256SUMS`
6. Click "Publish release"

### 8.2 Update Documentation

Update installation instructions in documentation to reference PyPI:

```bash
# Update docs/user-guide/INSTALL.md
# Change installation command to:
pip install adcp-recorder
```

### 8.3 Announce Release

Consider announcing the release:
- [ ] GitHub Discussions
- [ ] Project mailing list
- [ ] Social media
- [ ] Relevant forums or communities

### 8.4 Monitor for Issues

After release, monitor:
- [ ] GitHub Issues for bug reports
- [ ] PyPI download statistics
- [ ] User feedback

---

## Troubleshooting

### Issue: "File already exists"

**Problem**: Trying to upload a version that already exists on PyPI.

**Solution**: 
1. Increment version number in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md
3. Rebuild package
4. Upload new version

### Issue: "Invalid distribution"

**Problem**: Package metadata is invalid.

**Solution**:
```bash
# Check package with twine
python -m twine check dist/*

# Review error messages and fix pyproject.toml
```

### Issue: "Authentication failed"

**Problem**: API token is incorrect or expired.

**Solution**:
1. Generate new API token at https://pypi.org/manage/account/token/
2. Update `~/.pypirc` with new token
3. Retry upload

### Issue: "README rendering incorrectly"

**Problem**: README.md has formatting issues on PyPI.

**Solution**:
1. Test README locally: `python -m readme_renderer README.md`
2. Fix markdown formatting
3. Rebuild and re-upload to TestPyPI first

---

## Quick Reference Commands

```bash
# Complete upload workflow
rm -rf build/ dist/ *.egg-info
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*  # Test first
python -m twine upload dist/*  # Production

# Create git tag
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ adcp-recorder  # TestPyPI
pip install adcp-recorder  # PyPI
```

---

## Version Numbering Guide

Follow Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.0` → `0.2.0`: New feature
- `0.1.0` → `1.0.0`: First stable release or breaking change

---

## Security Best Practices

1. **Use API Tokens**: Never use username/password
2. **Protect .pypirc**: Set permissions to `chmod 600 ~/.pypirc`
3. **Rotate Tokens**: Periodically regenerate API tokens
4. **Scope Tokens**: Use project-scoped tokens when possible
5. **2FA**: Enable two-factor authentication on PyPI account

---

## Additional Resources

- **PyPI Help**: https://pypi.org/help/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Documentation**: https://twine.readthedocs.io/
- **Build Documentation**: https://build.pypa.io/
- **PEP 517/518**: https://peps.python.org/pep-0517/

---

**Ready to publish!** Follow these steps carefully and your package will be available on PyPI for the world to use.
