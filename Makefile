.PHONY: help install install-dev test test-unit test-integration test-all \
        test-parallel coverage clean format lint type-check docker-build \
        docker-test docker-test-all docker-dev docker-integration

# Python 설정
PYTHON := python3.11
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PYTEST := $(VENV)/bin/pytest

# 기본 타겟
help:
	@echo "KDM SDK - 사용 가능한 명령어:"
	@echo ""
	@echo "환경 설정:"
	@echo "  make install         - 프로덕션 의존성 설치"
	@echo "  make install-dev     - 개발 의존성 설치"
	@echo "  make venv            - 가상환경 생성"
	@echo ""
	@echo "테스트:"
	@echo "  make test            - 단위 테스트 실행 (빠름)"
	@echo "  make test-unit       - 단위 테스트만 실행"
	@echo "  make test-integration- 통합 테스트 실행 (MCP 서버 필요)"
	@echo "  make test-all        - 모든 테스트 실행"
	@echo "  make test-parallel   - 병렬 테스트 실행 (pytest-xdist)"
	@echo "  make coverage        - 커버리지 측정"
	@echo ""
	@echo "코드 품질:"
	@echo "  make format          - 코드 포맷팅 (black)"
	@echo "  make lint            - 코드 린팅 검사"
	@echo "  make type-check      - 타입 체크 (mypy)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    - Docker 이미지 빌드"
	@echo "  make docker-test     - Docker에서 단위 테스트 (Python 3.11)"
	@echo "  make docker-test-all - Docker에서 모든 버전 테스트 (3.10/3.11/3.12)"
	@echo "  make docker-integration - Docker에서 통합 테스트"
	@echo "  make docker-dev      - Docker 개발 환경 시작"
	@echo ""
	@echo "기타:"
	@echo "  make clean           - 빌드 아티팩트 삭제"

# 가상환경 생성
venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip

# 의존성 설치
install: venv
	$(VENV_PYTHON) -m pip install -r requirements.txt
	$(VENV_PYTHON) -m pip install -e .

install-dev: venv
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt
	$(VENV_PYTHON) -m pip install -e .

# 테스트 실행
test: install-dev
	$(VENV_PYTEST) -v -m "not integration and not slow"

test-unit: install-dev
	$(VENV_PYTEST) -v -m unit

test-integration: install-dev
	@echo "경고: MCP 서버가 http://203.237.1.4:8080에서 실행 중이어야 합니다"
	$(VENV_PYTEST) -v -m integration

test-all: install-dev
	$(VENV_PYTEST) -v

test-parallel: install-dev
	$(VENV_PYTEST) -v -n auto -m "not integration"

# 커버리지
coverage: install-dev
	$(VENV_PYTEST) --cov=kdm_sdk --cov-report=html --cov-report=term -m "not integration"
	@echo "커버리지 리포트: htmlcov/index.html"

# 코드 품질
format: install-dev
	$(VENV)/bin/black src tests examples

lint: install-dev
	$(VENV)/bin/black --check src tests examples

type-check: install-dev
	$(VENV)/bin/mypy src

# Docker
docker-build:
	docker compose build

docker-test:
	docker compose up test-py311

docker-test-all:
	docker compose up test-py310 test-py311 test-py312

docker-integration:
	docker compose up integration-test

docker-dev:
	docker compose run --rm dev

docker-parallel:
	docker compose up test-parallel

docker-coverage:
	docker compose up coverage

# 정리
clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf $(VENV)
