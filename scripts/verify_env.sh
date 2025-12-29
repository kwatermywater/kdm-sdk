#!/bin/bash
# KDM SDK Environment Verification Script
# Validates development environment setup

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 체크 카운터
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 함수: 성공 체크
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

# 함수: 실패 체크
check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

# 함수: 경고 체크
check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

# 함수: 정보 출력
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 헤더
echo ""
echo "=========================================="
echo "KDM SDK Environment Verification"
echo "=========================================="
echo ""

# 1. Python 버전 확인
info "Python 버전 확인 중..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
        check_pass "Python $PYTHON_VERSION (>= 3.10 required)"
    else
        check_fail "Python $PYTHON_VERSION (>= 3.10 required)"
        echo "  → Current: $PYTHON_VERSION"
        echo "  → Required: >= $REQUIRED_VERSION"
    fi
else
    check_fail "Python not found"
fi

# 2. Python 3.11 시스템 설치 확인 (선택사항)
if command -v python3.11 &> /dev/null; then
    PY311_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
    check_pass "Python 3.11 available at $(which python3.11)"
else
    check_warn "Python 3.11 not found (optional for venv setup)"
fi

# 3. 프로젝트 구조 확인
info "프로젝트 구조 확인 중..."

if [ -d "src/kdm_sdk" ]; then
    check_pass "src/kdm_sdk/ directory exists"
else
    check_fail "src/kdm_sdk/ directory not found"
fi

if [ -d "tests" ]; then
    check_pass "tests/ directory exists"
else
    check_fail "tests/ directory not found"
fi

if [ -f "setup.py" ]; then
    check_pass "setup.py exists"
else
    check_fail "setup.py not found"
fi

if [ -f "pytest.ini" ]; then
    check_pass "pytest.ini exists"
else
    check_fail "pytest.ini not found"
fi

# 4. 의존성 파일 확인
info "의존성 파일 확인 중..."

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt not found"
fi

if [ -f "requirements-dev.txt" ]; then
    check_pass "requirements-dev.txt exists"
else
    check_fail "requirements-dev.txt not found"
fi

# 5. Python 패키지 설치 확인
info "Python 패키지 설치 확인 중..."

# pytest
if python -c "import pytest" 2>/dev/null; then
    PYTEST_VERSION=$(python -c "import pytest; print(pytest.__version__)")
    check_pass "pytest $PYTEST_VERSION installed"
else
    check_fail "pytest not installed"
    echo "  → Run: pip install -r requirements-dev.txt"
fi

# pandas
if python -c "import pandas" 2>/dev/null; then
    PANDAS_VERSION=$(python -c "import pandas; print(pandas.__version__)")
    check_pass "pandas $PANDAS_VERSION installed"
else
    check_fail "pandas not installed"
    echo "  → Run: pip install -r requirements.txt"
fi

# httpx
if python -c "import httpx" 2>/dev/null; then
    HTTPX_VERSION=$(python -c "import httpx; print(httpx.__version__)")
    check_pass "httpx $HTTPX_VERSION installed"
else
    check_fail "httpx not installed"
    echo "  → Run: pip install -r requirements.txt"
fi

# pytest-asyncio
if python -c "import pytest_asyncio" 2>/dev/null; then
    check_pass "pytest-asyncio installed"
else
    check_fail "pytest-asyncio not installed"
    echo "  → Run: pip install -r requirements-dev.txt"
fi

# pytest-xdist (병렬 테스트용)
if python -c "import xdist" 2>/dev/null; then
    check_pass "pytest-xdist installed (parallel testing)"
else
    check_warn "pytest-xdist not installed (optional for parallel tests)"
    echo "  → Run: pip install pytest-xdist"
fi

# respx (HTTP mocking)
if python -c "import respx" 2>/dev/null; then
    check_pass "respx installed (HTTP mocking)"
else
    check_warn "respx not installed (optional for HTTP mocking)"
    echo "  → Run: pip install respx"
fi

# 6. KDM SDK 패키지 설치 확인
info "KDM SDK 패키지 설치 확인 중..."

if python -c "import kdm_sdk" 2>/dev/null; then
    check_pass "kdm_sdk package installed"

    # 주요 모듈 임포트 테스트
    if python -c "from kdm_sdk import KDMClient, KDMQuery" 2>/dev/null; then
        check_pass "KDMClient and KDMQuery importable"
    else
        check_fail "Cannot import KDMClient or KDMQuery"
    fi
else
    check_fail "kdm_sdk package not installed"
    echo "  → Run: pip install -e ."
fi

# 7. Docker 설치 확인 (선택사항)
info "Docker 환경 확인 중..."

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    check_pass "Docker $DOCKER_VERSION installed"

    # Docker Compose 확인
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
        check_pass "Docker Compose $COMPOSE_VERSION installed"
    else
        check_warn "Docker Compose not found (optional)"
    fi
else
    check_warn "Docker not installed (optional for containerized tests)"
fi

# 8. 테스트 파일 확인
info "테스트 파일 확인 중..."

TEST_COUNT=$(find tests -name "test_*.py" -o -name "*_test.py" | wc -l)
if [ "$TEST_COUNT" -gt 0 ]; then
    check_pass "$TEST_COUNT test files found"
else
    check_fail "No test files found in tests/"
fi

# 9. Makefile 확인
if [ -f "Makefile" ]; then
    check_pass "Makefile exists (test automation available)"
else
    check_warn "Makefile not found (manual test execution required)"
fi

# 10. MCP 서버 연결 확인 (선택사항)
info "MCP 서버 연결 확인 중..."

MCP_SERVER_URL="${KDM_MCP_SERVER_URL:-http://203.237.1.4:8080}"
if command -v curl &> /dev/null; then
    if curl -s --max-time 5 "$MCP_SERVER_URL" > /dev/null 2>&1; then
        check_pass "MCP Server reachable at $MCP_SERVER_URL"
    else
        check_warn "MCP Server not reachable at $MCP_SERVER_URL"
        echo "  → Integration tests may fail"
    fi
else
    check_warn "curl not installed (cannot verify MCP server connectivity)"
fi

# 결과 요약
echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}✓ Passed:${NC} $PASS_COUNT"
echo -e "${YELLOW}⚠ Warnings:${NC} $WARN_COUNT"
echo -e "${RED}✗ Failed:${NC} $FAIL_COUNT"
echo ""

# 권장 사항
if [ $FAIL_COUNT -gt 0 ]; then
    echo "❌ Environment is NOT ready"
    echo ""
    echo "Recommended actions:"
    echo "  1. Install missing Python packages:"
    echo "     pip install -r requirements-dev.txt"
    echo "     pip install -e ."
    echo "  2. Verify Python version >= 3.10"
    echo "  3. Re-run this script to verify fixes"
    exit 1
elif [ $WARN_COUNT -gt 0 ]; then
    echo "⚠️  Environment is MOSTLY ready (with warnings)"
    echo ""
    echo "Optional improvements:"
    echo "  • Install pytest-xdist for parallel tests: pip install pytest-xdist"
    echo "  • Install Docker for containerized tests"
    echo "  • Check MCP server connectivity for integration tests"
    exit 0
else
    echo "✅ Environment is FULLY ready!"
    echo ""
    echo "You can now run:"
    echo "  • make test              - Run unit tests"
    echo "  • make test-parallel     - Run parallel tests"
    echo "  • make coverage          - Measure coverage"
    echo "  • make docker-test-all   - Test on all Python versions"
    exit 0
fi
