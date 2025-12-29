# Scripts

이 디렉토리에는 KDM SDK 개발에 유용한 스크립트들이 있습니다.

## Git 인증 스크립트

### setup_git_auth.sh
GitHub Personal Access Token을 사용하여 Git 인증을 설정합니다.

**사용법:**
```bash
# 1. .env 파일에 GitHub 토큰 설정
# 2. 스크립트 실행
source scripts/setup_git_auth.sh
```

**필요한 설정:**
- `.env` 파일에 `GITHUB_TOKEN` 설정 필요
- GitHub 토큰 발급: https://github.com/settings/tokens
- 필요한 권한: `repo` (전체 저장소 제어)

### git_push.sh
GitHub에 코드를 푸시하는 간편 스크립트입니다.

**사용법:**
```bash
# main 브랜치에 푸시
./scripts/git_push.sh

# 특정 브랜치에 푸시
./scripts/git_push.sh feature-branch
```

**필요한 설정:**
- `.env` 파일에 `GITHUB_TOKEN` 설정 필요

## 환경 변수 설정

### .env 파일 생성
```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

### 필수 환경 변수
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `KDM_MCP_SERVER_URL`: KDM MCP 서버 URL (기본값: http://203.237.1.4:8080/sse)
- `PYPI_TOKEN`: PyPI 배포용 토큰 (선택사항)

## 보안 주의사항

⚠️ **중요**: `.env` 파일은 절대 Git에 커밋하지 마세요!

- `.env` 파일에는 민감한 토큰 정보가 포함되어 있습니다
- `.gitignore`에 이미 `.env`가 추가되어 있습니다
- 토큰을 공유하거나 공개 저장소에 업로드하지 마세요
- 토큰이 노출된 경우 즉시 GitHub에서 해당 토큰을 삭제하세요

## GitHub Personal Access Token 발급 방법

1. GitHub 로그인 후 https://github.com/settings/tokens 접속
2. "Generate new token" → "Generate new token (classic)" 선택
3. 토큰 이름 입력 (예: "KDM SDK Development")
4. 만료 기간 설정 (권장: 90일)
5. **필수 권한 선택:**
   - ✅ `repo` (전체 저장소 제어)
6. "Generate token" 클릭
7. 생성된 토큰을 복사하여 `.env` 파일에 저장

⚠️ **주의**: 토큰은 생성 직후 한 번만 표시됩니다. 반드시 안전한 곳에 저장하세요!
