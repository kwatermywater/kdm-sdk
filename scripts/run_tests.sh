#!/bin/bash
# KDM SDK Test Runner Script
# Provides colored output and error handling for test execution

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 에러 메시지 출력
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 함수: 성공 메시지 출력
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 함수: 경고 메시지 출력
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 함수: 정보 메시지 출력
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Python 버전 확인
check_python_version() {
    info "Python 버전 확인 중..."

    if ! command -v python &> /dev/null; then
        error "Python이 설치되지 않았습니다."
    fi

    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        error "Python $REQUIRED_VERSION 이상이 필요합니다. 현재 버전: $PYTHON_VERSION"
    fi

    success "Python $PYTHON_VERSION 확인됨"
}

# 의존성 확인
check_dependencies() {
    info "의존성 확인 중..."

    if ! python -c "import pytest" 2>/dev/null; then
        error "pytest가 설치되지 않았습니다. 'pip install -r requirements-dev.txt' 실행"
    fi

    success "의존성 확인 완료"
}

# 테스트 실행
run_tests() {
    TEST_TYPE=$1

    case $TEST_TYPE in
        unit)
            info "단위 테스트 실행 중..."
            pytest -v -m "unit" || error "단위 테스트 실패"
            ;;
        integration)
            warning "통합 테스트는 MCP 서버가 필요합니다 (http://203.237.1.4:8080)"
            read -p "계속하시겠습니까? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pytest -v -m "integration" || error "통합 테스트 실패"
            else
                info "통합 테스트 건너뜀"
                exit 0
            fi
            ;;
        fast)
            info "빠른 테스트 실행 중 (통합 테스트 및 느린 테스트 제외)..."
            pytest -v -m "not integration and not slow" || error "테스트 실패"
            ;;
        all)
            info "모든 테스트 실행 중..."
            pytest -v || error "테스트 실패"
            ;;
        parallel)
            info "병렬 테스트 실행 중 (pytest-xdist)..."
            pytest -v -n auto -m "not integration" || error "병렬 테스트 실패"
            ;;
        coverage)
            info "커버리지 측정 중..."
            pytest --cov=kdm_sdk --cov-report=html --cov-report=term -m "not integration" || error "커버리지 측정 실패"
            success "커버리지 리포트: htmlcov/index.html"
            ;;
        *)
            error "알 수 없는 테스트 타입: $TEST_TYPE\n사용법: $0 {unit|integration|fast|all|parallel|coverage}"
            ;;
    esac

    success "테스트 완료"
}

# 메인 실행
main() {
    echo ""
    echo "=========================================="
    echo "KDM SDK Test Runner"
    echo "=========================================="
    echo ""

    check_python_version
    check_dependencies

    if [ -z "$1" ]; then
        echo "사용법: $0 {unit|integration|fast|all|parallel|coverage}"
        echo ""
        echo "  unit        - 단위 테스트만 실행"
        echo "  integration - 통합 테스트 실행 (MCP 서버 필요)"
        echo "  fast        - 빠른 테스트 (통합/느린 테스트 제외)"
        echo "  all         - 모든 테스트 실행"
        echo "  parallel    - 병렬 테스트 실행"
        echo "  coverage    - 커버리지 측정"
        exit 1
    fi

    run_tests $1

    echo ""
    echo "=========================================="
    success "완료!"
    echo "=========================================="
}

main $@
