# KDM 데이터 가이드

> 💡 처음 사용하시는 분들을 위한 수자원 데이터 설명서

## 목차

1. [시설 유형 (facility_type)](#시설-유형-facility_type)
2. [시간 단위 (time_key)](#시간-단위-time_key)
3. [측정 항목 (measurement_items)](#측정-항목-measurement_items)
4. [API 기간 제한](#api-기간-제한)
5. [시설 검색 방법](#시설-검색-방법)
6. [용어 설명](#용어-설명)

---

## 시설 유형 (facility_type)

KDM에서 제공하는 5가지 시설 유형:

| 유형 | 코드 | 설명 | 예시 |
|------|------|------|------|
| **댐** | `dam` | 다목적댐, 용수댐, 발전댐 등 | 소양강댐, 충주댐, 팔당댐 |
| **수위관측소** | `water_level` | 하천 수위 측정 시설 | 춘천, 의암, 청평 |
| **우량관측소** | `rainfall` | 강수량 측정 시설 | 소양강댐우량, 춘천우량 |
| **기상관측소** | `weather` | 기온, 습도, 풍속 등 측정 | 소양강댐기상 |
| **수질관측소** | `water_quality` | 수질 측정 시설 | 소양강댐수질 |

### 사용 예제

```python
# 댐 데이터 조회
result = await KDMQuery() \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율"]) \
    .execute()

# 하천 수위 조회
result = await KDMQuery() \
    .site("춘천", facility_type="water_level") \
    .measurements(["수위"]) \
    .execute()
```

---

## 시간 단위 (time_key)

데이터는 다양한 시간 단위로 제공됩니다:

| 시간 단위 | 코드 | 설명 | 권장 기간 |
|-----------|------|------|----------|
| **10분** | `min_10` | 10분 간격 데이터 | 최대 7일 |
| **시간** | `h_1` | 1시간 간격 데이터 | 최대 30일 |
| **일** | `d_1` | 1일 간격 데이터 | 최대 365일 |
| **월** | `mt_1` | 1개월 간격 데이터 | 제한 없음 |
| **자동** | `auto` | 자동 선택 (h_1 → d_1 → mt_1 순) | - |

### 시간 단위 자동 선택

`time_key="auto"`로 설정하면 SDK가 자동으로 최적의 시간 단위를 선택합니다:

```python
result = await KDMQuery() \
    .site("소양강댐", facility_type="dam") \
    .measurements(["저수율"]) \
    .days(7) \
    .time_key("auto")  # 시간별 → 일별 → 월별 순서로 시도
    .execute()
```

---

## 측정 항목 (measurement_items)

### 댐 주요 측정 항목

#### 기본 현황
- `저수위` (m, EL.m) - 댐의 현재 수위
- `저수량` (백만㎥) - 댐에 저장된 물의 양
- `저수율` (%) - 총 저수 용량 대비 현재 저수량 비율
- `공용량` (백만㎥) - 사용 가능한 물의 양
- `유입량` (㎥/s, CMS) - 댐으로 들어오는 물의 양
- `총방류량` (㎥/s, CMS) - 댐에서 나가는 전체 물의 양

#### 방류 상세
- `댐_발전방류량` (㎥/s) - 발전용 방류
- `댐_여수로방류량` (㎥/s) - 여수로를 통한 방류 (홍수 조절)
- `댐_하천유지용수방류량` (㎥/s) - 하천 환경 유지용 방류

#### 예년 비교 (전년 동기 대비)
- `예년_저수량` (백만㎥)
- `예년_저수위` (m)
- `예년_유입량` (㎥/s)
- `예년_총방류량` (㎥/s)
- `예년_우량` (mm)

### 수위관측소 주요 측정 항목

- `수위` (m, EL.m) - 하천 수위
- `우량` (mm) - 강수량

### 강우 측정 항목

- `우량` (mm) - 시간당 강수량
- `누가우량` (mm) - 누적 강수량
- `1시간최다강수량` (mm) - 1시간 최대 강수량
- `예년_우량` (mm) - 전년 동기 강수량
- `예년_누가우량` (mm) - 전년 동기 누적 강수량

### 기상 측정 항목

- `기온` (℃) - 대기 온도
- `수온` (℃) - 수체 온도
- `상대습도` (%) - 공기 중 수증기 포화도
- `풍속` (m/s) - 바람 속도
- `순간최대풍속` (m/s) - 최대 순간 풍속
- `일사량` (MJ/㎡) - 태양 복사 에너지
- `적설량` (cm) - 눈이 쌓인 깊이
- `대형증발량` (mm) - 증발량 (대형 증발접시)
- `소형증발량` (mm) - 증발량 (소형 증발접시)

### 수질 측정 항목

- `총유기탄소(TOC)` (mg/L) - 유기물 오염도 지표 ⭐ **권장**
- `생물화학적산소요구량(BOD)` (mg/L) - 유기물 오염도 지표
- `화학적산소요구량(COD)` (mg/L) - 유기물 오염도 지표
- `수소이온농도(pH)` - 산성/알칼리성 정도 (0~14)
- `용존산소(DO)` (mg/L) - 물속 산소량
- `총인(T-P)` (mg/L) - 부영양화 지표
- `클로로필a` (mg/㎥) - 녹조 발생 지표
- `탁도` (NTU) - 물의 혼탁한 정도
- `전기전도도` (μS/cm) - 용존 이온 농도
- `부유물질(SS)` (mg/L) - 물속 떠다니는 물질

> 💡 **수질 데이터 권장 우선순위**: TOC > BOD > COD

---

## API 기간 제한

K-water API는 시간 단위별로 조회 가능한 최대 기간이 다릅니다:

| 시간 단위 | 권장 최대 기간 | 설명 |
|-----------|----------------|------|
| `min_10` (10분) | **7일** | 단기 정밀 분석용 |
| `h_1` (시간) | **30일** | 일반적인 분석용 |
| `d_1` (일) | **365일** | 장기 추세 분석용 |
| `mt_1` (월) | **제한 없음** | 연도별 비교 분석용 |

### ⚠️ 기간 초과 시 동작

기간을 초과하여 조회하면:
1. 일부 데이터만 반환되거나
2. 오류가 발생할 수 있습니다

**권장사항**:
- 시간별 데이터는 30일 이내로 조회
- 30일 이상이 필요한 경우 `time_key="d_1"` (일별) 사용
- 1년 이상이 필요한 경우 `time_key="mt_1"` (월별) 사용

### 자동 폴백 기능

SDK는 `time_key="auto"`를 사용하면 자동으로 시간 단위를 조정합니다:

```python
# 90일 조회 시 자동으로 일별 데이터로 전환
result = await KDMQuery() \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(90) \
    .time_key("auto")  # h_1 실패 → d_1 성공
    .execute()
```

---

## 시설 검색 방법

### 1. 정확한 시설명 모를 때

SDK의 `search_facilities()` 메서드로 시설을 검색하세요:

```python
from kdm_sdk import KDMClient

async def search_dams():
    client = KDMClient()
    await client.connect()

    # "소양"으로 시작하는 모든 시설 검색
    results = await client.search_facilities(query="소양", limit=10)

    for facility in results:
        print(f"{facility['site_name']} ({facility['facility_type']})")

    await client.disconnect()

# 출력 예시:
# 소양강댐 (dam)
# 소양강댐우량 (rainfall)
# 소양강댐기상 (weather)
```

### 2. 시설별 측정 항목 확인

특정 시설에서 어떤 항목을 제공하는지 확인:

```python
async def list_measurements():
    client = KDMClient()
    await client.connect()

    # 소양강댐에서 측정 가능한 모든 항목 조회
    result = await client.list_measurements(
        site_name="소양강댐",
        facility_type="dam"
    )

    print(f"시설명: {result['site']['site_name']}")
    print(f"총 {result['total_count']}개 항목 제공:")

    for item in result['measurements']:
        print(f"  - {item['measurement_item']} ({item['unit']})")
        print(f"    시간 단위: {', '.join(item['time_keys'])}")

    await client.disconnect()

# 출력 예시:
# 시설명: 소양강댐
# 총 45개 항목 제공:
#   - 저수위 (m)
#     시간 단위: h_1, d_1, mt_1
#   - 저수율 (%)
#     시간 단위: h_1, d_1, mt_1
#   - 유입량 (㎥/s)
#     시간 단위: h_1, d_1, mt_1
```

### 3. 주요 댐 목록

자주 사용되는 주요 댐:

| 댐 이름 | 위치 | 유역 | 특징 |
|---------|------|------|------|
| 소양강댐 | 강원 춘천 | 한강 | 국내 최대 다목적댐 |
| 충주댐 | 충북 충주 | 한강 | 다목적댐, 발전 |
| 팔당댐 | 경기 양평 | 한강 | 수도권 용수 공급 |
| 대청댐 | 대전/충북 | 금강 | 금강 최대 다목적댐 |
| 안동댐 | 경북 안동 | 낙동강 | 낙동강 유역 |
| 임하댐 | 경북 안동 | 낙동강 | 낙동강 유역 |
| 합천댐 | 경남 합천 | 낙동강 | 낙동강 유역 |
| 주암댐 | 전남 순천 | 섬진강 | 광주 용수 공급 |

---

## 용어 설명

### 수문 기본 용어

| 용어 | 설명 | 단위 |
|------|------|------|
| **저수위** | 댐 또는 저수지의 수면 높이 (해발 기준) | m (EL.m) |
| **저수량** | 댐에 저장된 물의 총량 | 백만㎥ |
| **저수율** | 총 저수 용량 대비 현재 저수량의 비율 (100% = 만수) | % |
| **공용량** | 실제로 사용할 수 있는 물의 양 (저수량 - 사수용량) | 백만㎥ |
| **유입량** | 단위 시간당 댐으로 유입되는 물의 양 | ㎥/s (CMS) |
| **방류량** | 단위 시간당 댐에서 방류하는 물의 양 | ㎥/s (CMS) |

### 단위 설명

| 단위 | 의미 | 사용 예 |
|------|------|---------|
| **m (EL.m)** | 미터 (해발 고도) | 저수위, 수위 |
| **백만㎥** | 100만 세제곱미터 | 저수량, 공용량 |
| **%** | 퍼센트 | 저수율 |
| **㎥/s (CMS)** | 초당 세제곱미터 (Cubic Meter per Second) | 유입량, 방류량 |
| **mm** | 밀리미터 | 강수량, 증발량 |
| **℃** | 섭씨 온도 | 기온, 수온 |
| **m/s** | 초당 미터 | 풍속 |
| **mg/L** | 리터당 밀리그램 | 수질 농도 |
| **NTU** | Nephelometric Turbidity Unit (탁도 단위) | 탁도 |

### 수질 용어

| 용어 | 설명 | 기준 |
|------|------|------|
| **TOC** | 총유기탄소 - 물속 유기물 양 (권장 지표) | 낮을수록 양호 |
| **BOD** | 생물화학적 산소요구량 - 미생물이 유기물 분해 시 필요한 산소량 | 낮을수록 양호 |
| **COD** | 화학적 산소요구량 - 화학적으로 유기물 분해 시 필요한 산소량 | 낮을수록 양호 |
| **pH** | 수소이온농도 - 산성/알칼리성 (pH 7 = 중성) | 6.5~8.5 적정 |
| **DO** | 용존산소 - 물속 녹아있는 산소량 | 높을수록 양호 |
| **T-P** | 총인 - 부영양화 원인 물질 | 낮을수록 양호 |
| **클로로필a** | 식물성 플랑크톤 농도 (녹조 지표) | 낮을수록 양호 |

---

## 예제 모음

### 초보자용 기본 예제

#### 1. 댐 저수율 조회
```python
import asyncio
from kdm_sdk import KDMQuery

async def check_reservoir_level():
    """댐 저수율 확인 - 가장 기본적인 예제"""
    result = await KDMQuery() \
        .site("소양강댐", facility_type="dam") \
        .measurements(["저수율"]) \
        .days(7) \
        .execute()

    if result.success:
        df = result.to_dataframe()
        print(f"현재 저수율: {df['저수율'].iloc[-1]:.1f}%")
        print(f"7일 평균: {df['저수율'].mean():.1f}%")

asyncio.run(check_reservoir_level())
```

#### 2. 강수량 확인
```python
async def check_rainfall():
    """강수량 확인"""
    result = await KDMQuery() \
        .site("소양강댐우량", facility_type="rainfall") \
        .measurements(["우량", "누가우량"]) \
        .days(3) \
        .execute()

    if result.success:
        df = result.to_dataframe()
        print(f"최근 3일 총 강수량: {df['우량'].sum():.1f}mm")

asyncio.run(check_rainfall())
```

#### 3. 측정 가능한 항목 확인
```python
from kdm_sdk import KDMClient

async def what_can_i_measure():
    """소양강댐에서 측정 가능한 모든 항목 보기"""
    client = KDMClient()
    await client.connect()

    result = await client.list_measurements(
        site_name="소양강댐",
        facility_type="dam"
    )

    print(f"📊 {result['site']['site_name']} 측정 항목:")
    for item in result['measurements'][:10]:  # 처음 10개만
        print(f"  • {item['measurement_item']} ({item['unit']})")

    await client.disconnect()

asyncio.run(what_can_i_measure())
```

---

## 자주 묻는 질문 (FAQ)

### Q1. "측정 항목을 정확히 입력했는데 데이터가 없다고 나와요"

**A**: 다음을 확인하세요:
1. 시설명이 정확한지 (`list_measurements()`로 확인)
2. 해당 시설에서 그 항목을 제공하는지 확인
3. `time_key`를 `"auto"`로 설정하여 자동 폴백 시도

```python
# 자동 폴백 사용
result = await KDMQuery() \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(7) \
    .time_key("auto")  # 자동으로 최적 시간 단위 선택
    .execute()
```

### Q2. "1년치 시간별 데이터를 조회하고 싶어요"

**A**: 시간별 데이터는 최대 30일 권장입니다. 1년치가 필요하면 일별 데이터를 사용하세요:

```python
# ❌ 잘못된 예제 - 365일 시간별 데이터
result = await KDMQuery() \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(365) \
    .time_key("h_1")  # 실패할 수 있음
    .execute()

# ✅ 올바른 예제 - 365일 일별 데이터
result = await KDMQuery() \
    .site("소양강댐") \
    .measurements(["저수율"]) \
    .days(365) \
    .time_key("d_1")  # 일별 데이터
    .execute()
```

### Q3. "어떤 댐이 있는지 모르겠어요"

**A**: `search_facilities()`로 검색하세요:

```python
results = await client.search_facilities(query="댐", limit=50)
for r in results:
    if r['facility_type'] == 'dam':
        print(r['site_name'])
```

### Q4. "데이터가 너무 많아서 Excel로 보고 싶어요"

**A**: `to_excel()` 메서드를 사용하세요:

```python
result = await query.execute()
result.to_excel("soyang_data.xlsx")  # 자동으로 한글 인코딩
```

---

## 다음 단계

이제 기본을 이해하셨다면:

1. **[빠른 시작 가이드](../README.md#빠른-시작)** - 실전 예제
2. **[Query API 문서](QUERY_API.md)** - 전체 API 레퍼런스
3. **[예제 모음](../examples/)** - 다양한 사용 사례
4. **[FacilityPair 가이드](FACILITY_PAIR_QUICKSTART.md)** - 상하류 분석

문의사항이 있으시면 [GitHub Issues](https://github.com/kwatermywater/kdm-sdk/issues)에 등록해주세요!
