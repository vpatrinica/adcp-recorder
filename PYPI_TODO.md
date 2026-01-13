# PyPI Upload TODO Checklist

Quick reference checklist for uploading ADCP Recorder to PyPI.

## Pre-Upload Preparation

- [ ] **Update author information** in `pyproject.toml`
  - Replace "Your Name" with actual name
  - Replace "your.email@example.com" with actual email

- [ ] **Verify version number** is correct in:
  - [ ] `pyproject.toml` → `version = "0.1.0"`
  - [ ] `adcp_recorder/__init__.py` → `__version__ = "0.1.0"`

- [ ] **Update CHANGELOG.md** with release notes

- [ ] **Review README.md** for accuracy

- [ ] **Run all tests**
  ```bash
  pytest
  pytest --cov=adcp_recorder --cov-report=term-missing
  ```

- [ ] **Run linting**
  ```bash
  ruff check adcp_recorder/
  ```

## PyPI Account Setup

- [ ] **Create PyPI account** at https://pypi.org/account/register/
- [ ] **Create TestPyPI account** at https://test.pypi.org/account/register/
- [ ] **Generate API token** for PyPI
- [ ] **Generate API token** for TestPyPI
- [ ] **Configure ~/.pypirc** with API tokens
- [ ] **Set permissions**: `chmod 600 ~/.pypirc`

## Build Package

- [ ] **Install build tools**
  ```bash
  pip install --upgrade build twine
  ```

- [ ] **Clean previous builds**
  ```bash
  rm -rf build/ dist/ *.egg-info
  ```

- [ ] **Build distributions**
  ```bash
  python -m build
  ```

- [ ] **Verify package**
  ```bash
  python -m twine check dist/*
  ```

## Test on TestPyPI

- [ ] **Upload to TestPyPI**
  ```bash
  python -m twine upload --repository testpypi dist/*
  ```

- [ ] **Test installation from TestPyPI**
  ```bash
  python -m venv test-env
  source test-env/bin/activate
  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ adcp-recorder
  adcp-recorder --help
  deactivate
  rm -rf test-env
  ```

- [ ] **Verify package works correctly**

## Upload to PyPI (Production)

- [ ] **Create git tag**
  ```bash
  git tag -a v0.1.0 -m "Release version 0.1.0"
  git push origin v0.1.0
  ```

- [ ] **Upload to PyPI**
  ```bash
  python -m twine upload dist/*
  ```

- [ ] **Verify on PyPI**: https://pypi.org/project/adcp-recorder/

- [ ] **Test installation from PyPI**
  ```bash
  python -m venv verify-env
  source verify-env/bin/activate
  pip install adcp-recorder
  adcp-recorder --help
  deactivate
  rm -rf verify-env
  ```

## Post-Release

- [ ] **Create GitHub release** at https://github.com/vpatrinica/adcp-recorder/releases/new
  - Tag: v0.1.0
  - Title: ADCP Recorder v0.1.0
  - Description: Copy from CHANGELOG.md
  - Attach build artifacts

- [ ] **Update documentation** if needed

- [ ] **Announce release** (optional)

- [ ] **Monitor for issues**

---

## Quick Commands

```bash
# Complete workflow
rm -rf build/ dist/ *.egg-info
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*  # Test
python -m twine upload dist/*  # Production
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

**For detailed instructions, see**: [PYPI_UPLOAD.md](PYPI_UPLOAD.md)
