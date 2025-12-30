# KDM SDK

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/kwatermywater/kdm-sdk)

> 🚀 **베타 오픈** - K-water Data Model (KDM) 데이터를 쉽게 조회할 수 있는 Python SDK입니다.

K-water Data Model (KDM)은 [water.or.kr/kdm](https://water.or.kr/kdm) 기반의 수자원 데이터 서비스입니다. 이 SDK를 통해 댐 수문 데이터, 하천 수위, 강우량 등의 수자원 데이터를 간편하게 조회하고 분석할 수 있습니다.

[English Documentation](README.en.md)

## 주요 기능

- **직관적인 Query API** - 메서드 체이닝으로 간단한 쿼리 작성
- **배치 쿼리** - 여러 시설의 데이터를 병렬로 조회하여 성능 향상
- **상하류 연관 분석** - 댐 방류량과 하류 수위의 상관관계 분석
- **🆕 관측소 자동 탐색** - 댐의 상하류 관측소 자동 검색 (Basin 매칭 + 지리 기반 검색)
- **🆕 원본 시설코드 제공** - K-water, 환경부 등 원천 기관의 시설코드로 외부 시스템 연동
- **템플릿 시스템** - YAML 또는 Python으로 재사용 가능한 쿼리 템플릿 작성
- **pandas 통합** - 조회 결과를 DataFrame으로 즉시 변환
- **간편한 내보내기** - Excel, CSV, Parquet, JSON으로 한 줄에 저장
- **자동 폴백** - 시간 단위 데이터가 없으면 자동으로 일/월 단위 조회
- **비동기 지원** - async/await 패턴으로 효율적인 데이터 조회
- **타입 힌트** - 전체 코드에 타입 어노테이션으로 IDE 지원 강화

## SDK의 역할

### ✅ SDK가 하는 일
- **데이터 조회**: KDM 수자원 데이터를 쉽게 조회
- **데이터 변환**: pandas DataFrame으로 자동 변환
- **데이터 저장**: Excel, CSV, Parquet, JSON으로 한글 인코딩 지원하여 저장

### ❌ SDK가 하지 않는 일
- **시각화**: matplotlib, seaborn, plotly 등 사용
- **통계 분석**: pandas, scipy, numpy 등 사용
- **데이터 정제**: pandas 메서드 사용

**철학**: 이 SDK는 KDM 데이터를 pandas로 가져오는 것까지만 담당합니다. 그 이후는 여러분의 데이터 분석 능력을 활용하세요!

`examples/analyst_reference.py`에서 데이터를 가져온 후 할 수 있는 분석 예제를 확인하세요.

## 설치

```bash
# PyPI에서 설치 (권장) ⭐
pip install kdm-sdk

# 데이터 분석가용 (분석 도구 포함)
pip install kdm-sdk[analyst]

# 개발자용 (개발 도구 포함)
pip install kdm-sdk[dev]

# 또는 GitHub에서 최신 버전 설치
pip install git+https://github.com/kwatermywater/kdm-sdk.git
```

`[analyst]` 옵션에는 다음이 포함됩니다: pandas, jupyter, matplotlib, seaborn, plotly, openpyxl, pyarrow, scipy, statsmodels

## 요구사항

- Python 3.10 이상
- KDM MCP Server (운영 서버: `http://203.237.1.4:8080`)
- pandas 2.0+

## 처음 사용하시나요?

> 📚 **[데이터 가이드 바로가기](docs/DATA_GUIDE.md)** - 수자원 데이터가 처음이신 분들을 위한 친절한 설명서

**가이드 내용:**
- 시설 유형 (댐, 수위관측소, 우량관측소 등)
- 시간 단위 (시간별, 일별, 월별) 및 조회 기간 📅
- 측정 항목 (저수율, 유입량, 방류량 등) 📊
- 시설 검색 방법
- 용어 설명 (저수위, CMS, TOC 등)
- 초보자용 예제

**빠른 팁:**
```python
# 💡 어떤 댐이 있는지 모를 때
results = await client.search_facilities(query="댐", limit=10)

# 💡 측정 항목이 뭐가 있는지 모를 때
items = await client.list_measurements(site_name="소양강댐")

# 💡 시간 단위를 모를 때 (자동 선택)
result = await KDMQuery().site("소양강댐").measurements(["저수율"]) \
    .days(7).time_key("auto").execute()
```

## 빠른 시작

### 기본 쿼리 (Fluent API)

```python
import asyncio
from kdm_sdk import KDMQuery

async def main():
    # 댐 저수율 데이터 조회
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량"]) \
        .days(7) \
        .execute()

    # pandas DataFrame으로 변환
    df = result.to_dataframe()
    print(df.head())

asyncio.run(main())
```

### 배치 쿼리 (여러 시설 동시 조회)

```python
from kdm_sdk import KDMQuery

async def batch_query():
    query = KDMQuery()

    # 여러 댐 추가
    for dam in ["소양강댐", "충주댐", "팔당댐"]:
        query.site(dam, facility_type="dam") \
             .measurements(["저수율"]) \
             .days(7) \
             .add()

    # 병렬 실행
    results = await query.execute_batch(parallel=True)

    # 단일 DataFrame으로 통합
    combined_df = results.aggregate()
    print(combined_df.groupby("site_name")["저수율"].mean())

asyncio.run(batch_query())
```

### 상하류 상관관계 분석

```python
from kdm_sdk import FacilityPair

async def correlation_analysis():
    # 댐 방류가 하류 수위에 미치는 영향 분석
    from kdm_sdk import KDMClient
    import pandas as pd

    async with KDMClient() as client:
        # 상류 데이터 조회 (댐)
        upstream_result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["방류량"],
            days=30,
            time_key="h_1"
        )

        # 하류 데이터 조회 (수위관측소)
        downstream_result = await client.get_water_data(
            site_name="춘천시(춘천댐하류)",
            facility_type="water_level",
            measurement_items=["수위"],
            days=30,
            time_key="h_1"
        )

        # DataFrame 변환
        def to_df(data):
            records = []
            for item in data:
                record = {"datetime": item.get("datetime")}
                if "values" in item:
                    for key, val in item["values"].items():
                        record[key] = val.get("value")
                records.append(record)
            df = pd.DataFrame(records)
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"])
                df.set_index("datetime", inplace=True)
            return df

        upstream_df = to_df(upstream_result.get("data", []))
        downstream_df = to_df(downstream_result.get("data", []))

        # FacilityPair 생성
        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name="춘천시(춘천댐하류)",
            upstream_type="dam",
            downstream_type="water_level",
            upstream_data=upstream_df,
            downstream_data=downstream_df
        )

        # 최적 시간차 찾기
        correlation = pair.find_optimal_lag(max_lag_hours=12)
        print(f"최적 시간차: {correlation.lag_hours:.1f}시간")
        print(f"상관계수: {correlation.correlation:.3f}")

asyncio.run(correlation_analysis())
```

### 템플릿 기반 쿼리

```python
from kdm_sdk.templates import TemplateBuilder

async def template_query():
    # 재사용 가능한 템플릿 생성
    template = TemplateBuilder("주간 댐 모니터링") \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율", "유입량", "방류량"]) \
        .days(7) \
        .time_key("h_1") \
        .build()

    # 템플릿 실행
    result = await template.execute()
    df = result.to_dataframe()

    # 템플릿 저장하여 재사용
    template.save_yaml("templates/weekly_monitoring.yaml")

asyncio.run(template_query())
```

### 관측소 자동 탐색 (신규 기능)

```python
from kdm_sdk import KDMClient

async def find_stations():
    async with KDMClient() as client:
        # 댐의 하류 수위관측소 자동 검색
        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            station_type="water_level"
        )

        # 댐 정보 (원본 시설코드 포함)
        dam = result['dam']
        print(f"댐: {dam['site_name']}")
        print(f"원본코드: {dam['original_facility_code']}")  # K-water 코드

        # 관련 관측소 목록
        for station in result['stations']:
            print(f"- {station['site_name']}: {station['original_facility_code']}")
            print(f"  매칭방식: {station['match_type']}")  # basin or geographic
            print(f"  거리: {station['distance_km']:.1f} km")

asyncio.run(find_stations())
```

## 문서

- **[📚 데이터 가이드](docs/DATA_GUIDE.md)** ⭐ **필독** - 시설 유형, 측정 항목, 용어 설명, 초보자 필수
- **[예제 모음](examples/)** - 다양한 사용 사례 예제 코드

## 프로젝트 구조

```
kdm-sdk/
├── src/
│   └── kdm_sdk/
│       ├── __init__.py           # 패키지 exports
│       ├── client.py             # MCP 클라이언트
│       ├── query.py              # Fluent query API
│       ├── results.py            # 결과 래퍼
│       ├── facilities.py         # FacilityPair
│       └── templates/            # 템플릿 시스템
│           ├── builder.py        # TemplateBuilder
│           ├── base.py           # Template 기본 클래스
│           └── loaders.py        # YAML/Python 로더
├── tests/                        # 테스트 스위트
├── examples/                     # 사용 예제
│   ├── basic_usage.py           # KDMClient 예제
│   ├── query_usage.py           # Query API 예제
│   ├── facility_pair_usage.py   # FacilityPair 예제
│   └── templates/               # 템플릿 예제
├── docs/                         # 문서
└── README.md                     # 이 파일
```

## 예제

[examples/](examples/) 디렉토리에서 전체 예제를 확인하세요:

- **[basic_usage.py](examples/basic_usage.py)** - KDMClient 기본 사용법
- **[query_usage.py](examples/query_usage.py)** - Fluent Query API 예제
- **[facility_pair_usage.py](examples/facility_pair_usage.py)** - 상하류 분석
- **[templates/](examples/templates/)** - 템플릿 예제 (YAML 및 Python)

## 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 스위트 실행
pytest tests/test_query.py -v

# 커버리지 측정
pytest --cov=kdm_sdk --cov-report=html

# 단위 테스트만 실행
pytest -m unit

# 통합 테스트 실행 (MCP 서버 필요)
pytest -m integration
```

## 주요 사용 사례

### 1. 여러 댐 모니터링

```python
query = KDMQuery()
for dam in ["소양강댐", "충주댐", "팔당댐", "대청댐"]:
    query.site(dam).measurements(["저수율"]).days(30).add()

results = await query.execute_batch(parallel=True)
df = results.aggregate()
```

### 2. 전년 대비 비교

```python
result = await KDMQuery() \
    .site("장흥댐") \
    .measurements(["저수율"]) \
    .date_range("2024-06-01", "2024-06-30") \
    .compare_with_previous_year() \
    .execute()
```

### 3. 하류 수위 예측

```python
from kdm_sdk import KDMClient, FacilityPair
import pandas as pd

async with KDMClient() as client:
    # 상류 데이터 (댐)
    upstream_result = await client.get_water_data(
        site_name="소양강댐",
        facility_type="dam",
        measurement_items=["방류량"],
        days=365,
        time_key="h_1"
    )

    # 하류 데이터 (댐)
    downstream_result = await client.get_water_data(
        site_name="의암댐",
        facility_type="dam",
        measurement_items=["수위"],
        days=365,
        time_key="h_1"
    )

    # DataFrame 변환
    def to_df(data):
        records = []
        for item in data:
            record = {"datetime": item.get("datetime")}
            if "values" in item:
                for key, val in item["values"].items():
                    record[key] = val.get("value")
            records.append(record)
        df = pd.DataFrame(records)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
        return df

    upstream_df = to_df(upstream_result.get("data", []))
    downstream_df = to_df(downstream_result.get("data", []))

    # FacilityPair 생성
    pair = FacilityPair(
        upstream_name="소양강댐",
        downstream_name="의암댐",
        upstream_data=upstream_df,
        downstream_data=downstream_df
    )

    # 시간차를 고려하여 DataFrame 생성 (물이 이동하는데 5.5시간 소요)
    df = pair.to_dataframe(lag_hours=5.5)

    # 머신러닝 모델 학습에 사용
    X = df[["소양강댐_방류량"]]
    y = df["의암댐_수위"]
```

## 개발

### 테스트 주도 개발 (TDD)

이 프로젝트는 TDD 방법론으로 개발되었습니다:

1. **Red** - 실패하는 테스트 먼저 작성
2. **Green** - 테스트를 통과하는 최소한의 코드 구현
3. **Refactor** - 코드 품질 개선

### 테스트 실행

```bash
# 개발 의존성 설치
pip install -r requirements-dev.txt

# 테스트 실행
pytest -v

# 코드 포맷팅
black src tests

# 타입 체크
mypy src
```

## 기여하기

기여를 환영합니다! PR 제출 전 모든 테스트가 통과하는지 확인해주세요.

1. 저장소 포크
2. 기능 브랜치 생성
3. 새 기능에 대한 테스트 추가
4. 모든 테스트 통과 확인: `pytest`
5. 코드 포맷팅: `black src tests`
6. Pull Request 제출

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 지원

문의사항 및 이슈:
- 저장소에 이슈 생성
- 데이터 가이드는 [DATA_GUIDE.md](docs/DATA_GUIDE.md) 참조
- 사용 패턴은 [예제](examples/) 확인

## 변경 이력

버전 히스토리는 [CHANGELOG.md](CHANGELOG.md)를 참조하세요.

## 감사의 글

- K-water의 한국 댐 관리 시스템을 위해 개발되었습니다
- 데이터 접근을 위해 MCP (Model Context Protocol) 사용
- 테스트 주도 개발(TDD) 방법론으로 개발되었습니다

---

## 베타 오픈 안내

⚠️ **현재 베타 버전입니다.**

이 SDK는 베타 테스트 단계에 있습니다. 프로덕션 환경에서 사용하기 전에 충분한 테스트를 진행해주세요.

**알려진 제한사항:**
- 일부 측정 항목은 데이터 가용성에 따라 조회되지 않을 수 있습니다
- MCP 서버 응답 시간은 네트워크 상태에 따라 달라질 수 있습니다

**피드백:**
- GitHub Issues를 통해 버그 리포트 및 기능 제안을 부탁드립니다
- 베타 테스터분들의 피드백이 SDK 개선에 큰 도움이 됩니다

**문의:** GitHub Issues 또는 K-water 담당자에게 연락해주세요.
