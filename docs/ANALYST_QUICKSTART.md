# 분석가 퀵스타트 가이드

> KDM SDK를 사용하여 수자원 데이터를 조회하고 분석하는 방법을 5분 안에 배워봅시다.

## 목차

1. [설치하기](#설치하기)
2. [환경 설정](#환경-설정)
3. [첫 번째 쿼리](#첫-번째-쿼리)
4. [데이터 내보내기](#데이터-내보내기)
5. [일반적인 워크플로우](#일반적인-워크플로우)
6. [문제 해결](#문제-해결)
7. [다음 단계](#다음-단계)

---

## 설치하기

### 요구사항

- Python 3.10 이상
- pip (Python 패키지 관리자)

### 설치 명령어

터미널(Windows: 명령 프롬프트, Mac/Linux: 터미널)을 열고 다음 명령어를 실행하세요:

```bash
pip install kdm-sdk[analyst]
```

**`[analyst]`를 꼭 포함하세요!** 데이터 분석에 필요한 추가 패키지들이 함께 설치됩니다:
- pandas: 데이터 분석
- matplotlib, seaborn: 시각화
- openpyxl: Excel 내보내기
- pyarrow: Parquet 내보내기
- scipy, statsmodels: 통계 분석

### 설치 확인

```bash
python -c "import kdm_sdk; print('KDM SDK 버전:', kdm_sdk.__version__)"
```

성공하면 버전 정보가 출력됩니다.

---

## 환경 설정

### KDM MCP 서버 연결 설정

KDM SDK는 KDM MCP 서버에 연결하여 데이터를 가져옵니다. 환경 변수로 서버 주소를 설정하세요:

**Linux/Mac:**
```bash
export KDM_MCP_SERVER_URL=http://kdm-mcp:8001/sse
```

**Windows (PowerShell):**
```powershell
$env:KDM_MCP_SERVER_URL="http://kdm-mcp:8001/sse"
```

**Windows (명령 프롬프트):**
```cmd
set KDM_MCP_SERVER_URL=http://kdm-mcp:8001/sse
```

> **참고**: K-water 내부 네트워크에서는 기본 설정으로 자동 연결됩니다.

---

## 첫 번째 쿼리

### Python 스크립트로 시작하기

`first_query.py` 파일을 만들고 다음 코드를 작성하세요:

```python
# first_query.py
import asyncio
from kdm_sdk import KDMQuery

async def main():
    # 쿼리 생성
    query = KDMQuery()

    # 소양강댐의 저수율을 최근 7일간 조회
    result = await query.dam('소양강댐').measurement('저수율').days(7).get()

    # 결과 확인
    if result.success:
        print(f"✅ 조회 성공!")
        print(f"시설명: {result.site_name}")
        print(f"데이터 개수: {len(result)} 개")

        # 데이터프레임으로 변환
        df = result.to_dataframe()
        print(f"\n📊 데이터 미리보기:")
        print(df.head())

        # Excel로 내보내기
        result.to_excel('soyang_storage.xlsx')
        print(f"\n✅ Excel 파일 생성: soyang_storage.xlsx")
    else:
        print(f"❌ 조회 실패: {result.message}")

# 실행
if __name__ == "__main__":
    asyncio.run(main())
```

**실행:**
```bash
python first_query.py
```

### Jupyter Notebook으로 시작하기

Jupyter Notebook을 선호한다면:

```bash
jupyter notebook examples/notebooks/quickstart.ipynb
```

인터랙티브하게 코드를 실행하며 배울 수 있습니다!

---

## 데이터 내보내기

### Excel로 내보내기

```python
# 단일 쿼리 결과
result.to_excel('data.xlsx', sheet_name='소양강댐')

# 배치 쿼리 결과 (여러 댐)
batch_results.to_excel('all_dams.xlsx', sheet_name='댐 비교')
```

**결과**: Excel 파일이 생성되며, 한글이 깨지지 않습니다.

### CSV로 내보내기

```python
# UTF-8-sig 인코딩 자동 적용 (Excel에서 한글 정상 표시)
result.to_csv('data.csv')

# 옵션 지정
result.to_csv('data.csv', index=False, encoding='utf-8-sig')
```

### Parquet로 내보내기 (대용량 데이터)

```python
# 효율적인 컬럼형 저장 포맷
result.to_parquet('data.parquet')

# 압축 옵션
result.to_parquet('data.parquet', compression='snappy')
```

**장점**: CSV보다 빠르고 용량이 작으며, 데이터 타입이 보존됩니다.

### JSON으로 내보내기

```python
# 한글 자동 처리
result.to_json('data.json', indent=2)
```

---

## 일반적인 워크플로우

### 1. 조회 → 분석 → 시각화 → 내보내기

```python
import asyncio
from kdm_sdk import KDMQuery
import matplotlib.pyplot as plt

async def analyze_dam():
    # 1. 데이터 조회
    query = KDMQuery()
    result = await query.dam('소양강댐').measurement('저수율').days(30).get()

    # 2. DataFrame 변환
    df = result.to_dataframe()

    # 3. 분석
    avg = df['저수율'].mean()
    max_val = df['저수율'].max()
    min_val = df['저수율'].min()

    print(f"평균: {avg:.2f}%, 최고: {max_val:.2f}%, 최저: {min_val:.2f}%")

    # 4. 시각화
    plt.figure(figsize=(12, 6))
    plt.plot(df['datetime'], df['저수율'], marker='o')
    plt.title('소양강댐 저수율 추이 (30일)')
    plt.xlabel('날짜')
    plt.ylabel('저수율 (%)')
    plt.grid(True)
    plt.savefig('soyang_chart.png')
    print("✅ 차트 저장: soyang_chart.png")

    # 5. 내보내기
    result.to_excel('soyang_analysis.xlsx')
    print("✅ Excel 저장: soyang_analysis.xlsx")

asyncio.run(analyze_dam())
```

### 2. 배치 비교 (여러 댐 동시 조회)

```python
async def compare_dams():
    # 배치 쿼리 설정
    query = KDMQuery()
    query.facility_type('dam')
    query.measurement('저수율')
    query.days(7)

    # 여러 댐 추가
    query.add_site('소양강댐')
    query.add_site('충주댐')
    query.add_site('대청댐')

    # 일괄 실행
    results = await query.execute_batch()

    # 통합 DataFrame
    df = results.aggregate()

    # 댐별 평균 계산
    avg_by_dam = df.groupby('site_name')['저수율'].mean()
    print(avg_by_dam)

    # Excel로 내보내기
    results.to_excel('dam_comparison.xlsx')

asyncio.run(compare_dams())
```

### 3. 상관관계 분석 (상하류 관계)

```python
from kdm_sdk import FacilityPair

async def analyze_correlation():
    # 상하류 관계 설정
    pair = FacilityPair(
        upstream_site='소양강댐',
        downstream_site='의암댐',
        upstream_type='dam',
        downstream_type='water_level'
    )

    # 데이터 조회 및 상관관계 분석
    result = await pair.analyze_correlation(
        upstream_measurement='방류량',
        downstream_measurement='수위',
        days=30
    )

    print(f"상관계수: {result.pearson_r:.3f}")
    print(f"최적 시차: {result.optimal_lag}시간")

    # 결과를 DataFrame으로
    df = result.to_dataframe()
    df.to_excel('correlation_analysis.xlsx')

asyncio.run(analyze_correlation())
```

### 4. 리포트 생성 (월간 요약)

```python
async def monthly_report():
    # 주요 댐 목록
    dams = ['소양강댐', '충주댐', '대청댐', '안동댐', '임하댐']

    # 배치 쿼리
    query = KDMQuery()
    query.facility_type('dam')
    query.measurement(['저수율', '유입량', '방류량'])
    query.days(30)

    for dam in dams:
        query.add_site(dam)

    results = await query.execute_batch()

    # 전체 데이터를 Excel의 여러 시트로 저장
    with pd.ExcelWriter('monthly_report.xlsx') as writer:
        # 요약 시트
        summary_df = results.aggregate()
        summary = summary_df.groupby('site_name').agg({
            '저수율': ['mean', 'min', 'max'],
            '유입량': 'mean',
            '방류량': 'mean'
        })
        summary.to_excel(writer, sheet_name='요약')

        # 각 댐별 상세 시트
        for site_name, result in results:
            if result.success:
                df = result.to_dataframe()
                df.to_excel(writer, sheet_name=site_name[:31], index=False)

    print("✅ 월간 리포트 생성: monthly_report.xlsx")

asyncio.run(monthly_report())
```

---

## 문제 해결

### Q1: "ModuleNotFoundError: No module named 'kdm_sdk'" 에러

**해결**: KDM SDK를 설치하세요.
```bash
pip install kdm-sdk[analyst]
```

### Q2: Excel 파일에서 한글이 깨져요

**해결**: `to_csv()` 사용 시 기본적으로 UTF-8-sig 인코딩을 사용하므로 문제가 없어야 합니다.
만약 문제가 있다면:
```python
result.to_csv('data.csv', encoding='utf-8-sig')
```

### Q3: "openpyxl is not installed" 에러

**해결**: Excel 내보내기를 위한 패키지를 설치하세요.
```bash
pip install openpyxl
# 또는
pip install kdm-sdk[analyst]  # 모든 분석 패키지 포함
```

### Q4: "KDM MCP server connection failed" 에러

**해결**:
1. 환경 변수가 올바르게 설정되었는지 확인
2. KDM MCP 서버가 실행 중인지 확인
3. 네트워크 연결 확인

```python
# 환경 변수 확인
import os
print(os.environ.get('KDM_MCP_SERVER_URL'))
```

### Q5: pandas/matplotlib에서 한글 폰트가 안 나와요

**해결**:
```python
import matplotlib.pyplot as plt

# 한글 폰트 설정 (Mac)
plt.rcParams['font.family'] = 'AppleGothic'

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False
```

### Q6: Jupyter Notebook에서 async/await를 사용하면 에러가 나요

**해결**: Jupyter에서는 직접 await를 사용할 수 있습니다 (asyncio.run() 불필요).
```python
# Jupyter에서는 이렇게
result = await query.dam('소양강댐').days(7).get()

# 일반 Python 스크립트에서는 이렇게
result = asyncio.run(query.dam('소양강댐').days(7).get())
```

### Q7: 데이터가 없다고 나와요 (empty result)

**확인사항**:
1. 시설명이 정확한가요? (예: "소양강댐", "충주댐")
2. 측정 항목이 해당 시설에 있나요?
3. 날짜 범위가 적절한가요? (과거 데이터는 제한적일 수 있음)

```python
# 사용 가능한 측정 항목 확인
from kdm_sdk import KDMClient

client = KDMClient()
measurements = await client.list_measurements('소양강댐', 'dam')
print(measurements)
```

---

## 다음 단계

### 더 배우기

1. **전체 API 문서**: `docs/API_OVERVIEW.md`
   - 모든 메서드와 파라미터 상세 설명

2. **쿼리 API 가이드**: `docs/QUERY_API.md`
   - Fluent API 심화 활용법

3. **템플릿 가이드**: `docs/TEMPLATES_API.md`
   - 반복 작업 자동화

4. **레시피 북**: `docs/RECIPE_BOOK.md` (작성 예정)
   - 50+ 복사-붙여넣기 가능한 코드 예제

### 예제 둘러보기

- `examples/basic_usage.py` - 기본 사용법
- `examples/query_usage.py` - 고급 쿼리
- `examples/facility_pair_usage.py` - 상관관계 분석
- `examples/notebooks/` - Jupyter 노트북 예제

### 고급 주제

1. **시각화 모듈** (추가 예정)
   - 원클릭 차트 생성
   - 대시보드 데이터 준비

2. **분석 헬퍼** (추가 예정)
   - 이상치 탐지
   - 결측치 처리
   - 시계열 리샘플링

3. **BI 도구 연동** (추가 예정)
   - Tableau 연동
   - Power BI 연동

---

## 도움말

### 커뮤니티

- **GitHub Issues**: 버그 리포트, 기능 요청
- **문서**: 전체 문서는 `docs/` 디렉토리에서 확인

### 자주 사용하는 패턴

**패턴 1: 빠른 조회 + 내보내기**
```python
result = await KDMQuery().dam('소양강댐').measurement('저수율').days(7).get()
result.to_excel('output.xlsx')
```

**패턴 2: 여러 댐 비교**
```python
query = KDMQuery().facility_type('dam').measurement('저수율').days(30)
for dam in ['소양강댐', '충주댐', '대청댐']:
    query.add_site(dam)
results = await query.execute_batch()
results.to_excel('comparison.xlsx')
```

**패턴 3: 월간 평균 계산**
```python
result = await KDMQuery().dam('소양강댐').measurement('저수율').days(30).get()
df = result.to_dataframe()
monthly_avg = df['저수율'].mean()
print(f"월간 평균 저수율: {monthly_avg:.2f}%")
```

---

## 체크리스트

시작하기 전에 확인하세요:

- [ ] Python 3.10 이상 설치됨
- [ ] `pip install kdm-sdk[analyst]` 실행함
- [ ] KDM_MCP_SERVER_URL 환경 변수 설정함 (선택)
- [ ] 첫 번째 쿼리를 성공적으로 실행함
- [ ] DataFrame으로 변환할 수 있음
- [ ] Excel/CSV로 내보낼 수 있음

모두 체크했다면 준비 완료입니다! 🎉

---

**Happy Analyzing!** 🚀

문의사항이나 제안사항이 있으시면 언제든지 GitHub Issues에 남겨주세요.
