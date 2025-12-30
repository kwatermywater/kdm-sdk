# KDM SDK Backlog

## High Priority

### Setup Self-Hosted Runner for CI/CD
**Status**: Planned
**Priority**: High
**Created**: 2025-12-30

**Background**:
- GitHub Actions pricing policy changed to require self-hosted runners for free tier
- CI workflow (`.github/workflows/ci.yml`) was removed in v0.2.1-beta to unblock deployment
- All tests currently run locally (84 tests, all passing)

**Requirements**:
1. Set up self-hosted runner infrastructure
   - Choose hosting platform (local server, cloud VM, etc.)
   - Install GitHub Actions runner
   - Configure security and access

2. Restore CI workflow with self-hosted runner
   - Modify `runs-on` from `ubuntu-latest` to `self-hosted`
   - Test all CI jobs:
     - Unit tests (Python 3.10, 3.11, 3.12)
     - Code quality checks (black, mypy)
     - Parallel test execution
     - Coverage reports

3. Documentation
   - Document runner setup process
   - Add maintenance guide
   - Update CONTRIBUTING.md with CI information

**Benefits**:
- Automated testing on every push/PR
- Prevents regressions
- Quality assurance before merging
- Coverage tracking

**Estimated Effort**: Medium (4-8 hours)

**Dependencies**: None

**References**:
- Removed workflow: commit `0fff25e`
- GitHub self-hosted runner docs: https://docs.github.com/en/actions/hosting-your-own-runners

---

## Medium Priority

(Empty - add future features here)

---

## Low Priority

(Empty - add nice-to-have features here)

---

## Completed

(Tasks will be moved here when completed)
