# GitHub Actions CI/CD Documentation

This directory contains GitHub Actions workflows for automated testing, building, and deployment of the ADCP Recorder package.

## Workflows Overview

### 1. Tests (`tests.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual dispatch

**Jobs**:
- **test**: Runs tests across multiple OS (Ubuntu, Windows, macOS) and Python versions (3.9-3.12)
  - Installs dependencies
  - Runs linting with Ruff
  - Runs pytest with coverage
  - Uploads coverage to Codecov (Ubuntu + Python 3.11 only)
- **test-install**: Tests package installation from both wheel and source distributions

**Status Badge**:
```markdown
![Tests](https://github.com/vpatrinica/adcp-recorder/workflows/Tests/badge.svg)
```

---

### 2. Build (`build.yml`)

**Triggers**:
- Push to `main` branch
- Version tags (`v*`)
- Pull requests to `main`
- Manual dispatch

**Jobs**:
- **build**: Builds distribution packages
  - Creates wheel and source distributions
  - Validates with twine
  - Generates SHA256 checksums
  - Uploads build artifacts (30-day retention)
  - Creates GitHub release on version tags

**Status Badge**:
```markdown
![Build](https://github.com/vpatrinica/adcp-recorder/workflows/Build/badge.svg)
```

---

### 3. Publish to PyPI (`publish.yml`)

**Triggers**:
- GitHub release published
- Manual dispatch (with environment selection)

**Jobs**:
- **publish**: Publishes package to PyPI or TestPyPI
  - Runs tests before publishing
  - Builds distributions
  - Uses trusted publishing (OIDC)
  - Supports both PyPI and TestPyPI
  - Creates deployment summary

**Configuration Required**:
1. Configure PyPI trusted publisher:
   - Go to https://pypi.org/manage/account/publishing/
   - Add GitHub publisher:
     - Owner: `vpatrinica`
     - Repository: `adcp-recorder`
     - Workflow: `publish.yml`
     - Environment: `pypi`

2. Configure TestPyPI trusted publisher (optional):
   - Go to https://test.pypi.org/manage/account/publishing/
   - Add same configuration with environment: `testpypi`

3. Create GitHub environments:
   - Go to repository Settings → Environments
   - Create `pypi` environment
   - Create `testpypi` environment (optional)
   - Add protection rules as needed

**Manual Dispatch**:
```
Actions → Publish to PyPI → Run workflow
Select environment: testpypi or pypi
```

**Status Badge**:
```markdown
![Publish](https://github.com/vpatrinica/adcp-recorder/workflows/Publish%20to%20PyPI/badge.svg)
```

---

### 4. Code Quality (`code-quality.yml`)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Weekly schedule (Monday 00:00 UTC)
- Manual dispatch

**Jobs**:
- **lint**: Linting and formatting checks
  - Ruff linting
  - Ruff formatting check
  - MyPy type checking (optional)
- **security**: Security scanning
  - Safety check for vulnerable dependencies
  - Bandit security linter
  - Uploads security reports
- **coverage**: Detailed coverage reporting
  - Generates HTML coverage report
  - Uploads coverage artifacts
  - Posts coverage comment on PRs

**Status Badge**:
```markdown
![Code Quality](https://github.com/vpatrinica/adcp-recorder/workflows/Code%20Quality/badge.svg)
```

---

## Setup Instructions

### 1. Enable GitHub Actions

GitHub Actions should be enabled by default. Verify in:
- Repository Settings → Actions → General
- Ensure "Allow all actions and reusable workflows" is selected

### 2. Configure Secrets (Optional)

For additional integrations, configure secrets in:
- Repository Settings → Secrets and variables → Actions

**Optional Secrets**:
- `CODECOV_TOKEN`: For Codecov integration (if repository is private)

### 3. Configure PyPI Trusted Publishing

**For PyPI**:
1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in:
   - PyPI Project Name: `adcp-recorder`
   - Owner: `vpatrinica`
   - Repository name: `adcp-recorder`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
4. Save

**For TestPyPI** (recommended for testing):
1. Go to https://test.pypi.org/manage/account/publishing/
2. Repeat same steps with environment name: `testpypi`

### 4. Create GitHub Environments

1. Go to repository Settings → Environments
2. Click "New environment"
3. Name: `pypi`
4. Add protection rules (optional):
   - Required reviewers
   - Wait timer
   - Deployment branches (only `main`)
5. Repeat for `testpypi` environment

---

## Usage

### Running Tests Locally

Before pushing, run tests locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check adcp_recorder/

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=adcp_recorder --cov-report=term-missing
```

### Creating a Release

1. **Update version** in:
   - `pyproject.toml`
   - `adcp_recorder/__init__.py`

2. **Update CHANGELOG.md** with release notes

3. **Commit and push** changes:
   ```bash
   git add .
   git commit -m "Prepare release v0.1.0"
   git push origin main
   ```

4. **Create and push tag**:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

5. **Create GitHub release**:
   - Go to Releases → Draft a new release
   - Choose tag: `v0.1.0`
   - Title: `ADCP Recorder v0.1.0`
   - Description: Copy from CHANGELOG.md
   - Publish release

6. **Automatic publishing**:
   - Build workflow creates GitHub release artifacts
   - Publish workflow automatically publishes to PyPI

### Manual PyPI Publishing

To manually publish (e.g., to TestPyPI):

1. Go to Actions → Publish to PyPI
2. Click "Run workflow"
3. Select environment: `testpypi` or `pypi`
4. Click "Run workflow"

### Testing on TestPyPI First

**Recommended workflow**:

1. Create release as draft
2. Manually run publish workflow with `testpypi`
3. Test installation:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ adcp-recorder
   ```
4. If successful, publish release (triggers PyPI upload)

---

## Workflow Status Badges

Add to README.md:

```markdown
[![Tests](https://github.com/vpatrinica/adcp-recorder/workflows/Tests/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/tests.yml)
[![Build](https://github.com/vpatrinica/adcp-recorder/workflows/Build/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/build.yml)
[![Code Quality](https://github.com/vpatrinica/adcp-recorder/workflows/Code%20Quality/badge.svg)](https://github.com/vpatrinica/adcp-recorder/actions/workflows/code-quality.yml)
[![PyPI](https://img.shields.io/pypi/v/adcp-recorder)](https://pypi.org/project/adcp-recorder/)
[![Python](https://img.shields.io/pypi/pyversions/adcp-recorder)](https://pypi.org/project/adcp-recorder/)
```

---

## Troubleshooting

### Workflow Fails on Tests

1. Check test output in Actions tab
2. Run tests locally to reproduce
3. Fix issues and push

### PyPI Publishing Fails

**Error: "Trusted publishing not configured"**
- Configure trusted publisher on PyPI (see Setup Instructions)

**Error: "File already exists"**
- Version already published
- Increment version number
- Create new tag and release

**Error: "Invalid credentials"**
- Verify trusted publishing configuration
- Check environment name matches workflow

### Build Artifacts Not Uploaded

- Check if tag matches pattern `v*`
- Verify `GITHUB_TOKEN` has required permissions
- Check workflow logs for errors

---

## Maintenance

### Updating Workflows

When updating workflows:

1. Test changes in a feature branch
2. Create PR to review changes
3. Merge to main after approval

### Dependency Updates

Workflows use specific action versions:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `actions/upload-artifact@v4`

Update periodically for security and features.

### Monitoring

Monitor workflow runs:
- Actions tab shows all workflow runs
- Set up notifications for failures
- Review security scan results weekly

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

---

**All workflows are configured and ready to use!**
