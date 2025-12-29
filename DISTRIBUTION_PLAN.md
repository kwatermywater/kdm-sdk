# KDM SDK 배포 계획

> KDM SDK를 내부/외부 사용자에게 배포하기 위한 전략 및 실행 계획

---

## 📋 목차

1. [배포 전략](#배포-전략)
2. [배포 준비](#배포-준비)
3. [패키징](#패키징)
4. [배포 채널](#배포-채널)
5. [버전 관리](#버전-관리)
6. [문서화](#문서화)
7. [지원 및 유지보수](#지원-및-유지보수)

---

## 배포 전략

### 타겟 사용자

#### 1차 타겟 (내부)
- **K-water 데이터 분석가**
- **K-water 데이터 과학자**
- **K-water 연구원**

#### 2차 타겟 (외부 - 향후)
- 수자원 관련 연구기관
- 대학 연구실
- 관련 정부 기관

### 배포 단계

```
Phase 1: 내부 베타 (1-2개월)
  ↓
Phase 2: 내부 정식 배포 (3-6개월)
  ↓
Phase 3: 외부 제한 배포 (선택적)
  ↓
Phase 4: 공개 배포 (검토 후 결정)
```

---

## 배포 준비

### ✅ 완료된 작업

1. **코드 정리**
   - [x] 불필요한 파일 삭제 (INSTALL.md, run_tests.sh)
   - [x] 디렉토리 통합 (단일 프로젝트)
   - [x] .gitignore 업데이트

2. **기능 완성**
   - [x] 데이터 내보내기 (Excel, CSV, Parquet, JSON)
   - [x] pandas 통합
   - [x] 배치 쿼리
   - [x] 템플릿 시스템
   - [x] 분석가용 의존성 관리

3. **문서화**
   - [x] README.md
   - [x] ANALYST_QUICKSTART.md
   - [x] Jupyter 퀵스타트 노트북
   - [x] 예제 코드

4. **패키징 설정**
   - [x] setup.py (extras_require)
   - [x] MANIFEST.in
   - [x] requirements.txt
   - [x] requirements-dev.txt

### 🔲 추가 필요 작업

1. **테스트 강화**
   - [ ] 내보내기 기능 테스트 추가 (`tests/test_export.py`)
   - [ ] 통합 테스트 확장
   - [ ] 테스트 커버리지 90% 이상 확보

2. **문서 보완**
   - [ ] API 레퍼런스 자동 생성 (Sphinx)
   - [ ] FAQ 섹션 추가
   - [ ] 트러블슈팅 가이드 확장

3. **품질 보증**
   - [ ] 코드 리뷰
   - [ ] 보안 검토 (의존성 취약점 스캔)
   - [ ] 성능 벤치마크

---

## 패키징

### Python 패키지 빌드

#### 1. 로컬 개발 설치
```bash
cd /home/claudeuser/kdm-sdk
pip install -e .[dev]
```

#### 2. 배포 패키지 빌드
```bash
# 빌드 도구 설치
pip install build twine

# 패키지 빌드
python -m build

# 결과물:
# - dist/kdm_sdk-0.1.0-py3-none-any.whl  (wheel)
# - dist/kdm-sdk-0.1.0.tar.gz            (source)
```

#### 3. 패키지 검증
```bash
# 패키지 구조 확인
tar -tzf dist/kdm-sdk-0.1.0.tar.gz

# 메타데이터 확인
unzip -l dist/kdm_sdk-0.1.0-py3-none-any.whl

# twine으로 검증
twine check dist/*
```

---

## 배포 채널

### Option 1: 내부 Git Repository (권장 - Phase 1)

**장점**:
- 빠른 배포
- 접근 제어 용이
- 버전 관리 통합

**설치 방법**:
```bash
# Git 저장소에서 직접 설치
pip install git+https://github.com/kwater/kdm-sdk.git

# 특정 버전
pip install git+https://github.com/kwater/kdm-sdk.git@v0.1.0

# 분석가용
pip install git+https://github.com/kwater/kdm-sdk.git#egg=kdm-sdk[analyst]
```

**배포 프로세스**:
1. GitHub/GitLab에 Private Repository 생성
2. 코드 푸시
3. 릴리스 태그 생성 (v0.1.0)
4. 사용자에게 설치 가이드 공유

### Option 2: 내부 PyPI 서버 (권장 - Phase 2)

**장점**:
- 표준 pip 설치
- 의존성 관리 자동화
- 오프라인 설치 가능

**설정 방법**:
```bash
# devpi 서버 설치 (내부 PyPI)
pip install devpi-server devpi-client

# 서버 시작
devpi-server --start --host 0.0.0.0 --port 3141

# 인덱스 생성
devpi use http://internal-pypi.kwater.or.kr:3141
devpi login <username>
devpi index -c kdm-sdk

# 패키지 업로드
devpi upload dist/*
```

**사용자 설치**:
```bash
pip install kdm-sdk[analyst] \
  --index-url http://internal-pypi.kwater.or.kr:3141/kdm-sdk
```

### Option 3: 파일 공유 (임시 - Phase 1)

**방법**:
```bash
# wheel 파일 생성
python -m build

# 공유 폴더에 복사
cp dist/kdm_sdk-0.1.0-py3-none-any.whl /shared/kdm-sdk/

# 사용자 설치
pip install /shared/kdm-sdk/kdm_sdk-0.1.0-py3-none-any.whl[analyst]
```

### Option 4: Public PyPI (Phase 4 - 외부 공개 시)

**프로세스**:
```bash
# PyPI 계정 생성 (pypi.org)
# .pypirc 설정

# 업로드
twine upload dist/*

# 사용자 설치 (전세계 어디서나)
pip install kdm-sdk[analyst]
```

---

## 버전 관리

### 버전 체계 (Semantic Versioning)

```
MAJOR.MINOR.PATCH  (예: 1.2.3)

MAJOR: 하위 호환 불가 변경
MINOR: 하위 호환 가능 기능 추가
PATCH: 하위 호환 가능 버그 수정
```

### 현재 버전: `0.1.0`

**의미**: 초기 베타 릴리스

### 버전 업데이트 예시

| 변경 내용 | 버전 |
|-----------|------|
| 초기 릴리스 | `0.1.0` |
| 버그 수정 | `0.1.1` |
| 새 내보내기 형식 추가 | `0.2.0` |
| API 변경 (호환 불가) | `1.0.0` |

### 릴리스 프로세스

1. **코드 변경 및 테스트**
2. **CHANGELOG.md 업데이트**
   ```markdown
   ## [0.2.0] - 2025-01-15
   ### Added
   - Parquet 내보내기 지원
   - 새 템플릿 예제 추가

   ### Fixed
   - Excel 한글 인코딩 이슈 수정
   ```

3. **setup.py 버전 업데이트**
   ```python
   version="0.2.0"
   ```

4. **Git 태그 생성**
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

5. **패키지 빌드 및 배포**
   ```bash
   python -m build
   # 배포 채널에 따라 업로드
   ```

---

## 문서화

### 문서 구조

```
docs/
├── ANALYST_QUICKSTART.md    # 분석가 시작 가이드
├── API_OVERVIEW.md           # API 전체 개요
├── QUERY_API.md              # Query API 상세
├── TEMPLATES_API.md          # Template 시스템
└── TROUBLESHOOTING.md        # 문제 해결 (추가 필요)
```

### 문서 호스팅 옵션

#### Option 1: GitHub Pages (권장)
```bash
# docs를 GitHub Pages로 배포
# Settings → Pages → Source: main branch / docs folder
```

접속: `https://kwater.github.io/kdm-sdk/`

#### Option 2: MkDocs (고급)
```bash
# MkDocs 설치
pip install mkdocs mkdocs-material

# mkdocs.yml 생성
# 문서 빌드
mkdocs build

# GitHub Pages로 배포
mkdocs gh-deploy
```

#### Option 3: 내부 Confluence/Wiki
- 문서를 Confluence에 수동 업로드
- 버전별 문서 관리

---

## 지원 및 유지보수

### 사용자 지원 채널

1. **GitHub Issues** (권장)
   - 버그 리포트
   - 기능 요청
   - Q&A

2. **내부 채팅** (Slack/Teams)
   - `#kdm-sdk-support` 채널 생성
   - 빠른 질문 응답

3. **이메일**
   - kdm-sdk-support@kwater.or.kr

### 유지보수 계획

#### 정기 업데이트 주기
- **패치**: 매월 (버그 수정)
- **마이너**: 분기별 (새 기능)
- **메이저**: 연 1회 (대규모 변경)

#### 지원 버전 정책
- **최신 버전**: 완전 지원
- **이전 버전**: 보안 패치만 (6개월)
- **구 버전**: 지원 종료 (1년 후)

---

## 배포 체크리스트

### Phase 1: 내부 베타 (현재)

- [x] 코드 정리 완료
- [x] 핵심 기능 구현
- [x] 기본 문서 작성
- [x] 패키징 설정
- [ ] 테스트 커버리지 90% 이상
- [ ] 내부 Git Repository 설정
- [ ] 베타 테스터 5-10명 모집
- [ ] 피드백 수집

### Phase 2: 내부 정식 배포

- [ ] 베타 피드백 반영
- [ ] 문서 완성도 향상
- [ ] 내부 PyPI 서버 구축
- [ ] 설치 가이드 배포
- [ ] 교육 세션 실시 (선택)

### Phase 3: 외부 제한 배포 (선택)

- [ ] 법무/보안 검토
- [ ] 라이선스 확정
- [ ] 외부 파트너 선정
- [ ] 제한적 접근 권한 부여

### Phase 4: 공개 배포 (검토 후)

- [ ] 경영진 승인
- [ ] Public PyPI 등록
- [ ] 공식 발표
- [ ] 오픈소스 커뮤니티 관리

---

## 즉시 실행 가능한 단계

### 1주차: 테스트 및 품질 보증
```bash
# 테스트 실행
cd /home/claudeuser/kdm-sdk
pytest tests/ -v --cov=kdm_sdk --cov-report=html

# 코드 품질 검사
black src/ tests/
mypy src/

# 의존성 취약점 스캔
pip install safety
safety check
```

### 2주차: 내부 Git Repository 설정
1. GitHub/GitLab Private Repo 생성
2. 코드 푸시
3. v0.1.0 태그 생성
4. 릴리스 노트 작성

### 3주차: 베타 테스터 배포
1. 5-10명 베타 테스터 모집
2. 설치 가이드 공유
3. 피드백 채널 오픈

### 4주차: 피드백 수집 및 개선
1. 버그 수정
2. 문서 보완
3. v0.1.1 패치 릴리스

---

## 예상 타임라인

```
Week 1-2:  테스트 및 품질 보증
Week 3-4:  내부 Git Repository 설정 및 베타 배포
Week 5-8:  베타 피드백 수집 및 개선
Week 9-10: v0.2.0 정식 릴리스 (내부)
Week 11+:  지속적 유지보수 및 개선
```

---

## 배포 명령어 요약

```bash
# 1. 로컬 테스트
cd /home/claudeuser/kdm-sdk
pip install -e .[dev]
pytest tests/

# 2. 패키지 빌드
python -m build

# 3. Git 태그 및 푸시
git tag -a v0.1.0 -m "Initial beta release"
git push origin v0.1.0

# 4. 사용자 설치 (Git)
pip install git+https://github.com/kwater/kdm-sdk.git@v0.1.0#egg=kdm-sdk[analyst]

# 5. 사용자 설치 (내부 PyPI)
pip install kdm-sdk[analyst] --index-url http://internal-pypi.kwater.or.kr:3141/kdm-sdk
```

---

## 연락처

**SDK 관리자**: [담당자명]
**이메일**: kdm-sdk-support@kwater.or.kr
**GitHub**: https://github.com/kwater/kdm-sdk

---

**마지막 업데이트**: 2025-12-26
**문서 버전**: 1.0
