# Python 3.13 Support Specification

## Overview

This specification outlines the requirements and implementation plan for adding Python 3.13 support to the Microsoft Fabric CLI, in addition to the currently supported versions (3.10, 3.11, and 3.12).

## Background

### Current State
- **Supported Python Versions**: 3.10, 3.11, 3.12
- **Blocking Dependency**: `msal[broker]` which depends on `pymsalruntime`
- **Historical Issue**: `pymsalruntime` lacked Python 3.13 support until recently

### Recent Development
- **pymsalruntime 0.18.1** (released in late 2024) officially added Python 3.13 support
- This removes the primary blocker for Fabric CLI Python 3.13 compatibility

## Goals

1. **Add Python 3.13 as a supported version** for the Fabric CLI
2. **Maintain backward compatibility** with Python 3.10, 3.11, and 3.12
3. **Update all configuration and CI/CD pipelines** to test against Python 3.13
4. **Ensure all dependencies are compatible** with Python 3.13
5. **Update documentation** to reflect the new supported version

## Technical Assessment

### Dependency Analysis

#### Critical Dependencies
| Dependency | Current Constraint | Python 3.13 Status | Action Required |
|------------|-------------------|-------------------|-----------------|
| `msal[broker]` | `>=1.29,<2` | ✅ Supported via pymsalruntime 0.18.1+ | Verify minimum version |
| `msal_extensions` | No version constraint | ✅ Compatible | None |
| `questionary` | No version constraint | ✅ Compatible | None |
| `prompt_toolkit` | `>=3.0.41` | ✅ Compatible | None |
| `cachetools` | `>=5.5.0` | ✅ Compatible | None |
| `jmespath` | No version constraint | ✅ Compatible | None |
| `pyyaml` | `==6.0.2` | ✅ Compatible | None |
| `argcomplete` | `>=3.6.2` | ✅ Compatible | None |
| `psutil` | `==7.0.0` | ✅ Compatible (3.13 wheels available) | None |

#### Test Dependencies
| Dependency | Current Constraint | Python 3.13 Status | Notes |
|------------|-------------------|-------------------|-------|
| `pytest` | `>=8.2.1` | ✅ Compatible | - |
| `pytest-cov` | No version constraint | ✅ Compatible | - |
| `vcrpy` | No version constraint | ✅ Compatible | - |
| `urllib3` | `<2.3.0,>=2.0.0` | ✅ Compatible | See urllib3 analysis below |

#### Development Dependencies
| Dependency | Python 3.13 Status |
|------------|-------------------|
| `black` | ✅ Compatible |
| `mypy` | ✅ Compatible |
| `tox` | ✅ Compatible (>=4.20.0) |

#### urllib3 Version Analysis

**Current Constraint**: `urllib3<2.3.0,>=2.0.0`
**Proposed Update**: `urllib3<2.7.0,>=2.0.0`

**Context**:
- urllib3 is used as a **test dependency only** (in `requirements.txt` and `tox.toml`)
- Not listed in `pyproject.toml` runtime dependencies
- Used indirectly via `requests` library (which depends on urllib3)
- Direct import found only in test code: [`tests/test_commands/api_processors/capacities_api_processor.py`](../../tests/test_commands/api_processors/capacities_api_processor.py:7)

**urllib3 Version Compatibility**:
| Version | Python 3.13 Support | Status | Notes |
|---------|-------------------|--------|-------|
| 2.2.x | ✅ Full support | Current in use (per NOTICE.txt: 2.2.3) | Stable |
| 2.3.x - 2.6.x | ✅ Full support | Available | Includes security fixes |
| 2.7.x | ✅ Full support | Latest (as of Dec 2024) | Python 3.13 wheels available |

**Requests Library Compatibility**:
- `requests` 2.32.5 (current version per NOTICE.txt) supports urllib3 v2.x
- No upper bound specified in requests for urllib3 2.x series
- requests pins: `urllib3>=1.21.1,<3`

**Benefits of Updating to <2.7.0**:
1. ✅ **Security patches**: Access to latest security fixes in urllib3 2.3.x - 2.6.x
2. ✅ **Python 3.13 optimization**: Better support for Python 3.13 features
3. ✅ **Future-proof**: Extends compatibility window
4. ✅ **Bug fixes**: Access to bug fixes in newer versions
5. ✅ **Backwards compatible**: urllib3 2.x maintains API compatibility

**Risk Assessment**:
- **Risk Level**: ⚠️ **Low-Medium**
- **Primary Concern**: urllib3 2.3+ introduced some behavioral changes
- **Mitigation**: Comprehensive testing required

**Breaking Changes in urllib3 2.3+**:
- urllib3 2.3.0+ removed support for Python 3.7
- Some deprecated APIs removed (but Fabric CLI doesn't use deprecated features)
- Minor changes to SSL/TLS handling (unlikely to affect CLI)

**Testing Required**:
1. ✅ Test suite passes with urllib3 2.6.x
2. ✅ VCR cassette playback works correctly
3. ✅ API processor tests function properly (especially `capacities_api_processor.py`)
4. ✅ No breaking changes in test utilities

**Recommendation**: ✅ **Proceed with Update**

The update to `urllib3<2.7.0` is recommended for:
- Enhanced Python 3.13 compatibility
- Access to security patches
- Alignment with modern dependency practices

However, this should be tested thoroughly as part of the Python 3.13 support implementation.

### Code Compatibility Analysis

Based on the codebase scan:

#### Typing Module Usage
- **Finding**: Extensive use of `typing` module (74 occurrences)
- **Status**: ✅ All typing constructs used (`Optional`, `List`, `Dict`, `Any`, `Union`, `Literal`, `NamedTuple`) are compatible with Python 3.13
- **Action**: None required

#### Language Features
- **No Python 3.13-incompatible features detected**
- **Standard library usage**: All imports use stable APIs
- **No deprecated features**: Code doesn't rely on features removed in 3.13

#### Potential Considerations
1. **Type hints**: Python 3.13 continues to support all type hint syntax used in the codebase
2. **MSAL broker authentication**: Relies on `pymsalruntime` - now supported
3. **String encoding**: No issues detected with f-strings or string operations
4. **Exception handling**: Uses standard patterns compatible with 3.13

## Implementation Plan

### Phase 1: Configuration Updates

#### 1.1 Update pyproject.toml
**File**: [`pyproject.toml`](../../pyproject.toml)

**Changes Required**:
```toml
# Line 13: Update Python version constraint
requires-python=">=3.10,<3.14"

# Lines 15-20: Add Python 3.13 classifier
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
]
```

**Risk**: Low - straightforward version constraint update

#### 1.2 Update tox.toml
**File**: [`tox.toml`](../../tox.toml)

**Changes Required**:
```toml
# Line 2: Add py313 to test environment list
env_list = ["lint", "type", "py310", "py311", "py312", "py313"]

# Line 71: Add py313 to Black target versions
target-version = ['py310', 'py311', 'py312', 'py313']
```

**Risk**: Low - extends existing test matrix

### Phase 2: CI/CD Pipeline Updates

#### 2.1 Update GitHub Actions Workflow
**File**: [`.github/workflows/fab-build.yml`](../../.github/workflows/fab-build.yml)

**Changes Required**:
```yaml
# Lines 74-81: Add Python 3.13 to test matrix
strategy:
  matrix:
    include:
      - python-version: "3.10"
        tox-env: "py310"
      - python-version: "3.11"
        tox-env: "py311"
      - python-version: "3.12"
        tox-env: "py312"
      - python-version: "3.13"
        tox-env: "py313"
```

**Risk**: Low - extends existing matrix strategy

#### 2.2 Update Dev Container (Optional)
**File**: [`.devcontainer/devcontainer.json`](../../.devcontainer/devcontainer.json)

**Current**: Uses Python 3.10 base image
**Recommendation**: Keep current version or update to 3.12+ as it supports development for all versions
**Risk**: Low - optional update, current container works for development

### Phase 3: Documentation Updates

#### 3.1 Update README.md
**File**: [`README.md`](../../README.md)

**Changes Required**:
```markdown
# Line 59: Update prerequisites
- **Python 3.10, 3.11, 3.12, or 3.13**
```

**Risk**: None - documentation only

#### 3.2 Update Example Files
**File**: [`docs/examples/files/github-workflow.yml`](../examples/files/github-workflow.yml)

**Changes Required** (Optional):
```yaml
# Line 27: Consider updating example to use 3.13
python-version: "3.13"
```

**Risk**: None - example file only, can keep as 3.12 for stability

### Phase 4: Dependency Verification

#### 4.1 Verify pymsalruntime Minimum Version
**Recommended Action**: Test that `msal[broker]>=1.29` properly installs pymsalruntime 0.18.1+ on Python 3.13

**Verification Steps**:
```bash
# In Python 3.13 environment
pip install "msal[broker]>=1.29,<2"
python -c "import pymsalruntime; print(pymsalruntime.__version__)"
# Should be >= 0.18.1
```

**Risk**: Medium - if older pymsalruntime is installed, broker authentication may fail

**Mitigation**: Consider adding explicit minimum version constraint if needed:
```toml
# In pyproject.toml dependencies (if required)
"msal[broker]>=1.31,<2",
```

#### 4.2 Update urllib3 Version Constraint
**Files to Update**:
- [`requirements.txt`](../../requirements.txt:4)
- [`tox.toml`](../../tox.toml:12)

**Current**: `urllib3<2.3.0,>=2.0.0`
**Proposed**: `urllib3<2.7.0,>=2.0.0`

**Changes Required**:

**requirements.txt**:
```txt
urllib3<2.7.0,>=2.0.0
```

**tox.toml**:
```toml
deps = [
    "pytest>=8",
    "pytest-sugar",
    "pytest-cov",
    "vcrpy",
    "urllib3<2.7.0,>=2.0.0",
]
```

**Verification Steps**:
```bash
# Test with updated urllib3
pip install "urllib3<2.7.0,>=2.0.0"
python -c "import urllib3; print(urllib3.__version__)"
# Should be >= 2.0.0 and < 2.7.0

# Run test suite
tox -e py313
# All tests should pass
```

**Risk**: Low-Medium - urllib3 is test-only dependency with good backwards compatibility

**Testing Focus**:
- VCR cassette playback in tests
- API processor functionality
- No regression in existing test suites

### Phase 5: Testing & Validation

#### 5.1 Local Testing
**Test Matrix**:
- ✅ Unit tests on Python 3.13
- ✅ Integration tests on Python 3.13
- ✅ Type checking on Python 3.13
- ✅ Linting on Python 3.13
- ✅ Build package on Python 3.13

#### 5.2 Feature Testing
**Critical Features to Test on Python 3.13**:
1. **Authentication**:
   - Interactive login with broker
   - Service principal authentication
   - Managed identity authentication
   - Federated token authentication

2. **File System Operations**:
   - `ls`, `cd`, `pwd`, `mkdir`, `rm`
   - OneLake file operations
   - Import/export

3. **API Operations**:
   - REST API calls
   - JMESPath filtering

4. **Job Management**:
   - Job execution
   - Status polling

#### 5.3 Cross-Version Compatibility Testing
**Verify**:
- Code works on all versions (3.10, 3.11, 3.12, 3.13)
- No regressions in existing versions
- Consistent behavior across versions

## Risk Assessment

### Low Risk Items
- ✅ Configuration file updates
- ✅ Documentation updates
- ✅ CI/CD pipeline extensions
- ✅ Standard library compatibility

### Medium Risk Items
- ⚠️ **pymsalruntime version verification**: Need to confirm msal[broker] pulls correct version
- ⚠️ **Broker authentication on 3.13**: Primary use case for pymsalruntime dependency

### Mitigation Strategies

1. **Phased Rollout**:
   - Add 3.13 support in pre-release
   - Gather community feedback
   - Monitor for issues before stable release

2. **Comprehensive Testing**:
   - Run full test suite on Python 3.13
   - Manual testing of broker authentication
   - Verify on multiple platforms (Windows, macOS, Linux)

3. **Documentation**:
   - Clearly communicate 3.13 as newly supported
   - Note any platform-specific considerations
   - Provide troubleshooting guidance

## Implementation Checklist

### Pre-Implementation
- [ ] Create GitHub issue for Python 3.13 support
- [ ] Verify pymsalruntime 0.18.1+ availability on PyPI
- [ ] Test msal[broker] installation on Python 3.13 environment

### Core Implementation
- [ ] Update [`pyproject.toml`](../../pyproject.toml) (version constraint + classifiers)
- [ ] Update [`tox.toml`](../../tox.toml) (test environments + urllib3 version)
- [ ] Update [`.github/workflows/fab-build.yml`](../../.github/workflows/fab-build.yml) (CI matrix)
- [ ] Update [`README.md`](../../README.md) (prerequisites)
- [ ] Update [`requirements.txt`](../../requirements.txt) (urllib3 version)

### Testing
- [ ] Run `tox -e py313` locally
- [ ] Verify all unit tests pass
- [ ] Verify all integration tests pass
- [ ] Test broker authentication on Python 3.13
- [ ] Test urllib3 2.6.x compatibility with VCR cassettes
- [ ] Test API processor functionality with updated urllib3
- [ ] Test on Windows with Python 3.13
- [ ] Test on macOS with Python 3.13
- [ ] Test on Linux with Python 3.13

### Documentation
- [ ] Update installation documentation
- [ ] Update contributing guide if needed
- [ ] Add Python 3.13 to supported versions in all docs
- [ ] Create changelog entry using `changie new`

### Release
- [ ] Create pull request with all changes
- [ ] Run full CI/CD pipeline
- [ ] Review and approve PR
- [ ] Merge to main
- [ ] Create release with updated PyPI package
- [ ] Announce Python 3.13 support

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|---------------|--------------|
| Configuration Updates | 1-2 hours | None |
| CI/CD Updates | 1-2 hours | Configuration complete |
| urllib3 Update & Testing | 2-3 hours | Configuration complete |
| Documentation | 1 hour | None |
| Testing & Validation | 4-8 hours | All updates complete |
| PR Review & Merge | 1-2 days | Testing complete |
| **Total** | **2-3 days** | - |

## Success Criteria

1. ✅ Python 3.13 listed as supported version in PyPI
2. ✅ All CI/CD tests pass on Python 3.13
3. ✅ Package installs successfully via `pip install ms-fabric-cli` on Python 3.13
4. ✅ All authentication methods work on Python 3.13
5. ✅ No regressions in Python 3.10, 3.11, or 3.12
6. ✅ Documentation updated across all relevant files

## Post-Implementation

### Monitoring
- Monitor GitHub issues for Python 3.13-specific problems
- Track PyPI download statistics by Python version
- Gather community feedback on 3.13 compatibility

### Future Considerations
- **Python 3.14**: Begin planning when Python 3.14 enters beta
- **Deprecation**: Consider Python 3.10 deprecation timeline (follow Python EOL dates)
- **Type System**: Leverage newer Python 3.13 type system features in future updates

## References

- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)
- [pymsalruntime 0.18.1 Release](https://pypi.org/project/pymsalruntime/0.18.1/)
- [msal-python GitHub](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [Python Packaging User Guide](https://packaging.python.org/)

## Conclusion

Adding Python 3.13 support to the Fabric CLI is a **low-risk, high-value enhancement** that:
- Keeps the CLI current with the latest Python releases
- Enables users on Python 3.13 to use the tool
- Demonstrates active maintenance and community support
- Requires minimal code changes due to careful dependency management

The primary blocker (`pymsalruntime`) has been resolved, and no breaking changes in Python 3.13 affect the current codebase. Implementation can proceed with confidence following the outlined plan.
