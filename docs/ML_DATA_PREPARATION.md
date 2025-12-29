# ML 모델용 데이터 준비 가이드

> KDM SDK로 수집한 데이터를 LSTM, XGBoost 등 ML 모델에 사용하기 위한 전처리 가이드

## 목차

1. [개요](#개요)
2. [기본 워크플로우](#기본-워크플로우)
3. [LSTM용 시계열 데이터 준비](#lstm용-시계열-데이터-준비)
4. [XGBoost용 테이블 데이터 준비](#xgboost용-테이블-데이터-준비)
5. [실전 예제](#실전-예제)
6. [팁과 권장사항](#팁과-권장사항)

---

## 개요

### KDM SDK의 역할

KDM SDK는 **데이터를 pandas DataFrame으로 변환하는 것까지만** 담당합니다.

```python
from kdm_sdk import KDMQuery

# SDK의 역할: 데이터 수집 + pandas 변환
result = await KDMQuery() \
    .site('소양강댐', facility_type='dam') \
    .measurements(['저수율', '유입량']) \
    .days(90) \
    .execute()

df = result.to_dataframe()  # ← SDK 역할 끝!

# 이후는 분석가가 pandas/sklearn/numpy로 자유롭게 처리
```

### 왜 이 방식인가?

1. **유연성**: 분석가마다 선호하는 전처리 방법이 다름
2. **표준 도구**: 이미 익숙한 pandas/sklearn 사용
3. **확장성**: 새로운 ML 기법에도 대응 가능

---

## 기본 워크플로우

```
┌─────────────┐
│ 1. 데이터   │  KDM SDK로 수집
│    수집     │  → pandas DataFrame
└──────┬──────┘
       ↓
┌─────────────┐
│ 2. 기본     │  pandas로 전처리
│    전처리   │  (결측치, 정렬, 타입 변환)
└──────┬──────┘
       ↓
┌─────────────┐
│ 3. 특성     │  pandas/numpy로 특성 생성
│    엔지니어링│  (lag, rolling, 시간 특성)
└──────┬──────┘
       ↓
┌─────────────┐
│ 4. ML 형식  │  모델별 형식으로 변환
│    변환     │  (LSTM: 3D, XGBoost: 2D)
└──────┬──────┘
       ↓
┌─────────────┐
│ 5. 저장 및  │  .npy, .csv 등으로 저장
│    학습     │  → ML 모델 학습
└─────────────┘
```

---

## LSTM용 시계열 데이터 준비

### 개요

LSTM(Long Short-Term Memory)은 시계열 데이터를 학습하는 딥러닝 모델입니다.

**입력 형식**: 3D 배열 `(samples, timesteps, features)`

### Step 1: 데이터 수집

```python
import asyncio
import pandas as pd
import numpy as np
from kdm_sdk import KDMQuery

async def collect_data():
    result = await KDMQuery() \
        .site('소양강댐', facility_type='dam') \
        .measurements(['저수율', '유입량', '방류량']) \
        .days(365) \
        .execute()

    return result.to_dataframe()

df = asyncio.run(collect_data())
print(f"수집된 데이터: {df.shape}")
```

### Step 2: 기본 전처리

```python
# 날짜를 datetime으로 변환
df['datetime'] = pd.to_datetime(df['datetime'])

# 날짜 기준 정렬 (오래된 것 → 최신)
df = df.sort_values('datetime')

# 날짜를 인덱스로 설정
df.set_index('datetime', inplace=True)

# 숫자형 컬럼만 선택 (unit 컬럼 제외)
numeric_cols = df.select_dtypes(include=[np.number]).columns
df_numeric = df[numeric_cols].copy()

print(f"숫자형 데이터: {df_numeric.shape}")
print(f"컬럼: {list(df_numeric.columns)}")
```

### Step 3: 결측치 처리

```python
# 결측치 확인
missing = df_numeric.isnull().sum()
print(f"결측치: {missing.sum()} 개")

if missing.sum() > 0:
    # Forward fill + Backward fill
    df_numeric = df_numeric.fillna(method='ffill').fillna(method='bfill')

    # 또는 선형 보간
    # df_numeric = df_numeric.interpolate(method='linear')

    print("✅ 결측치 처리 완료")
```

### Step 4: 정규화 (0-1)

```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(df_numeric)

print(f"정규화 완료: {data_scaled.shape}")
print(f"범위: [{data_scaled.min():.2f}, {data_scaled.max():.2f}]")

# ⚠️ 중요: scaler 저장 (예측 시 역변환에 필요)
import joblib
joblib.dump(scaler, 'scaler.pkl')
```

### Step 5: 시퀀스 생성

```python
def create_sequences(data, seq_length):
    """
    시계열 데이터를 LSTM 입력 형태로 변환

    Args:
        data: numpy array (n_samples, n_features)
        seq_length: 시퀀스 길이 (윈도우 크기)

    Returns:
        X: (n_samples, seq_length, n_features)
        y: (n_samples, n_features)
    """
    X, y = [], []

    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])  # 과거 seq_length개
        y.append(data[i+seq_length])    # 다음 1개

    return np.array(X), np.array(y)

# 7일 윈도우로 다음날 예측
seq_length = 7
X, y = create_sequences(data_scaled, seq_length)

print(f"✅ 시퀀스 생성 완료:")
print(f"   X shape: {X.shape}  (samples, timesteps, features)")
print(f"   y shape: {y.shape}  (samples, features)")
```

### Step 6: Train/Test 분할

```python
# 시계열은 순서가 중요하므로 shuffle=False
train_size = int(len(X) * 0.8)

X_train = X[:train_size]
X_test = X[train_size:]
y_train = y[:train_size]
y_test = y[train_size:]

print(f"Train: {X_train.shape[0]} samples")
print(f"Test:  {X_test.shape[0]} samples")
```

### Step 7: 데이터 저장

```python
# NumPy 파일로 저장
np.save('lstm_X_train.npy', X_train)
np.save('lstm_X_test.npy', X_test)
np.save('lstm_y_train.npy', y_train)
np.save('lstm_y_test.npy', y_test)

print("✅ LSTM 데이터 저장 완료")
```

### Step 8: LSTM 모델 학습

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# 모델 구성
n_features = X_train.shape[2]  # 특성 개수

model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(seq_length, n_features)),
    Dropout(0.2),
    LSTM(50, return_sequences=False),
    Dropout(0.2),
    Dense(n_features)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# 학습
history = model.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_data=(X_test, y_test),
    verbose=1
)

# 예측
predictions = model.predict(X_test)

# 역정규화 (원래 스케일로)
predictions_original = scaler.inverse_transform(predictions)
y_test_original = scaler.inverse_transform(y_test)

print(f"✅ 모델 학습 완료")
```

---

## XGBoost용 테이블 데이터 준비

### 개요

XGBoost는 테이블 형태의 데이터를 학습하는 그래디언트 부스팅 모델입니다.

**입력 형식**: 2D 배열 `(samples, features)`

### Step 1: 데이터 수집 (동일)

```python
import asyncio
from kdm_sdk import KDMQuery

async def collect_data():
    result = await KDMQuery() \
        .site('소양강댐', facility_type='dam') \
        .measurements(['저수율', '유입량', '방류량']) \
        .days(365) \
        .execute()

    return result.to_dataframe()

df = asyncio.run(collect_data())
```

### Step 2: 기본 전처리

```python
# 날짜 변환 및 정렬
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime')

# 숫자형 컬럼만 선택
numeric_cols = df.select_dtypes(include=[np.number]).columns
df = df[['datetime'] + list(numeric_cols)].copy()

print(f"기본 데이터: {df.shape}")
```

### Step 3: 시간 특성 추출

```python
# 날짜에서 시간 특성 추출
df['year'] = df['datetime'].dt.year
df['month'] = df['datetime'].dt.month
df['day'] = df['datetime'].dt.day
df['dayofweek'] = df['datetime'].dt.dayofweek  # 0=월요일, 6=일요일
df['dayofyear'] = df['datetime'].dt.dayofyear
df['quarter'] = df['datetime'].dt.quarter
df['week'] = df['datetime'].dt.isocalendar().week

# 순환 특성 (월, 요일은 순환적)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
df['day_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
df['day_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)

print(f"✅ 시간 특성 추가: {df.shape[1]} 개 컬럼")
```

### Step 4: Lag 특성 생성

```python
# 과거 값 특성 (Lag features)
for col in ['저수율', '유입량', '방류량']:
    if col in df.columns:
        # 1일 전
        df[f'{col}_lag1'] = df[col].shift(1)

        # 7일 전
        df[f'{col}_lag7'] = df[col].shift(7)

        # 14일 전
        df[f'{col}_lag14'] = df[col].shift(14)

        # 30일 전
        df[f'{col}_lag30'] = df[col].shift(30)

print(f"✅ Lag 특성 추가: {df.shape[1]} 개 컬럼")
```

### Step 5: Rolling 특성 생성

```python
# 이동평균 및 통계 특성
for col in ['저수율', '유입량', '방류량']:
    if col in df.columns:
        # 7일 이동평균
        df[f'{col}_rolling_mean_7'] = df[col].rolling(7).mean()

        # 7일 이동 표준편차
        df[f'{col}_rolling_std_7'] = df[col].rolling(7).std()

        # 30일 이동평균
        df[f'{col}_rolling_mean_30'] = df[col].rolling(30).mean()

        # 7일 최대값
        df[f'{col}_rolling_max_7'] = df[col].rolling(7).max()

        # 7일 최소값
        df[f'{col}_rolling_min_7'] = df[col].rolling(7).min()

print(f"✅ Rolling 특성 추가: {df.shape[1]} 개 컬럼")
```

### Step 6: 변화율 특성

```python
# 전일 대비 변화량 및 변화율
for col in ['저수율', '유입량', '방류량']:
    if col in df.columns:
        # 변화량
        df[f'{col}_diff'] = df[col].diff()

        # 변화율 (%)
        df[f'{col}_pct_change'] = df[col].pct_change() * 100

print(f"✅ 변화율 특성 추가: {df.shape[1]} 개 컬럼")
```

### Step 7: 타겟 변수 설정

```python
# 예: 내일 저수율 예측
df['target'] = df['저수율'].shift(-1)  # 다음날 저수율

# 또는 3일 후 예측
# df['target'] = df['저수율'].shift(-3)

# 또는 7일 평균 예측
# df['target'] = df['저수율'].shift(-1).rolling(7).mean()

print(f"✅ 타겟 변수 설정: target")
```

### Step 8: 결측치 제거

```python
# Lag와 Rolling으로 생긴 결측치 제거
df_clean = df.dropna()

print(f"결측치 제거 후: {df_clean.shape}")
print(f"제거된 행: {len(df) - len(df_clean)} 개")
```

### Step 9: Feature/Target 분리

```python
# datetime과 target 제외한 모든 컬럼이 feature
feature_cols = [col for col in df_clean.columns
                if col not in ['datetime', 'target']]

X = df_clean[feature_cols]
y = df_clean['target']

print(f"Features: {X.shape}")
print(f"Target:   {y.shape}")
print(f"\n특성 목록 (처음 10개):")
print(feature_cols[:10])
```

### Step 10: Train/Test 분할

```python
from sklearn.model_selection import train_test_split

# 시계열은 순서 유지 (shuffle=False)
train_size = int(len(X) * 0.8)

X_train = X[:train_size]
X_test = X[train_size:]
y_train = y[:train_size]
y_test = y[train_size:]

print(f"Train: {X_train.shape[0]} samples")
print(f"Test:  {X_test.shape[0]} samples")
```

### Step 11: 데이터 저장

```python
# CSV로 저장
X_train.to_csv('xgb_X_train.csv', index=False)
X_test.to_csv('xgb_X_test.csv', index=False)
y_train.to_csv('xgb_y_train.csv', index=False)
y_test.to_csv('xgb_y_test.csv', index=False)

# 전체 데이터 (특성 엔지니어링 완료)
df_clean.to_csv('ml_ready_data.csv', index=False)

print("✅ XGBoost 데이터 저장 완료")
```

### Step 12: XGBoost 모델 학습

```python
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score

# DMatrix 생성 (XGBoost 최적화된 데이터 구조)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

# 파라미터 설정
params = {
    'objective': 'reg:squarederror',  # 회귀
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'subsample': 0.8,
    'colsample_bytree': 0.8
}

# 모델 학습
model = xgb.train(
    params,
    dtrain,
    num_boost_round=100,
    evals=[(dtrain, 'train'), (dtest, 'test')],
    early_stopping_rounds=10,
    verbose_eval=10
)

# 예측
y_pred = model.predict(dtest)

# 평가
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"\n✅ 모델 평가:")
print(f"   RMSE: {rmse:.2f}")
print(f"   R²:   {r2:.3f}")

# 특성 중요도
importance = model.get_score(importance_type='gain')
print(f"\n상위 10개 중요 특성:")
for feat, score in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {feat}: {score:.2f}")
```

---

## 실전 예제

### 예제 1: 댐 저수율 7일 후 예측 (LSTM)

```python
import asyncio
import pandas as pd
import numpy as np
from kdm_sdk import KDMQuery
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

async def train_lstm_model():
    # 1년치 데이터 수집
    result = await KDMQuery() \
        .site('소양강댐', facility_type='dam') \
        .measurements(['저수율', '유입량', '방류량']) \
        .days(365) \
        .execute()

    df = result.to_dataframe()

    # 전처리
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').set_index('datetime')
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df = df[numeric_cols].fillna(method='ffill')

    # 정규화
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(df)

    # 시퀀스 생성 (30일로 7일 후 예측)
    seq_length = 30
    prediction_horizon = 7

    X, y = [], []
    for i in range(len(data_scaled) - seq_length - prediction_horizon):
        X.append(data_scaled[i:i+seq_length])
        y.append(data_scaled[i+seq_length+prediction_horizon, 0])  # 저수율만

    X = np.array(X)
    y = np.array(y)

    # Train/Test 분할
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # 모델
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(seq_length, data_scaled.shape[1])),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse')
    model.fit(X_train, y_train, epochs=50, batch_size=32,
              validation_data=(X_test, y_test), verbose=1)

    return model, scaler

# 실행
model, scaler = asyncio.run(train_lstm_model())
print("✅ LSTM 모델 학습 완료")
```

### 예제 2: 다중 댐 비교 분석 (XGBoost)

```python
import asyncio
import pandas as pd
from kdm_sdk import KDMQuery

async def prepare_multi_dam_data():
    dams = ['소양강댐', '충주댐', '대청댐']
    all_data = []

    for dam in dams:
        result = await KDMQuery() \
            .site(dam, facility_type='dam') \
            .measurements(['저수율', '유입량']) \
            .days(180) \
            .execute()

        df = result.to_dataframe()
        df['dam'] = dam  # 댐 구분
        all_data.append(df)

    # 통합
    df_all = pd.concat(all_data, ignore_index=True)

    # One-hot encoding (댐 구분)
    df_all = pd.get_dummies(df_all, columns=['dam'], prefix='dam')

    # 나머지 특성 엔지니어링...
    # (위의 XGBoost 예제와 동일)

    return df_all

df = asyncio.run(prepare_multi_dam_data())
print(f"다중 댐 데이터: {df.shape}")
```

---

## 팁과 권장사항

### 1. 데이터 수집

**✅ DO**
- 충분한 기간 수집 (최소 1년, 권장 2-3년)
- 모델에 필요한 모든 변수 수집
- 주기적으로 업데이트

**❌ DON'T**
- 너무 짧은 기간 (ML 학습 불충분)
- 불필요한 변수까지 수집 (성능 저하)

### 2. 전처리

**✅ DO**
- 결측치 확인 및 처리 (forward fill, interpolation)
- 이상치 탐지 및 처리 (IQR, Z-score)
- 데이터 타입 확인 (날짜는 datetime)

**❌ DON'T**
- 결측치를 0으로 채우기 (왜곡 가능)
- 이상치를 무조건 제거 (정보 손실)

### 3. 특성 엔지니어링

**✅ DO**
- 도메인 지식 활용 (댐 관리 전문가 의견)
- 시간 특성 추가 (계절성 반영)
- Lag 특성 추가 (과거 의존성)
- Rolling 특성 추가 (추세 파악)

**❌ DON'T**
- 너무 많은 특성 (과적합 위험)
- 타겟 누수 (target leakage) 주의

### 4. 정규화/스케일링

**LSTM**
- MinMaxScaler (0-1) 권장
- StandardScaler도 가능

**XGBoost**
- Tree 기반이므로 스케일링 선택적
- 하지만 하는 것을 권장

**⚠️ 중요**: Scaler를 학습 후 저장! (예측 시 필요)

### 5. Train/Test 분할

**시계열 데이터**
```python
# ✅ 순서 유지
train_size = int(len(data) * 0.8)
train = data[:train_size]
test = data[train_size:]

# ❌ 셔플 금지!
# train, test = train_test_split(data, shuffle=True)  # 절대 안됨!
```

**교차 검증**
```python
# 시계열용 교차 검증
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    # 학습 및 평가
```

### 6. 모델 평가

**회귀 지표**
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² (결정계수)
- MAPE (Mean Absolute Percentage Error)

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

rmse = np.sqrt(mean_squared_error(y_true, y_pred))
mae = mean_absolute_error(y_true, y_pred)
r2 = r2_score(y_true, y_pred)
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

print(f"RMSE: {rmse:.2f}")
print(f"MAE:  {mae:.2f}")
print(f"R²:   {r2:.3f}")
print(f"MAPE: {mape:.2f}%")
```

### 7. 과적합 방지

**LSTM**
- Dropout 사용 (0.2-0.5)
- Early stopping
- Validation set 활용

**XGBoost**
- max_depth 제한 (3-10)
- learning_rate 낮추기 (0.01-0.1)
- subsample, colsample_bytree (0.5-0.9)
- early_stopping_rounds

### 8. 데이터 저장

```python
# LSTM (NumPy)
np.save('data.npy', array)

# XGBoost (CSV)
df.to_csv('data.csv', index=False)

# Scaler 저장
import joblib
joblib.dump(scaler, 'scaler.pkl')

# 모델 저장
model.save('lstm_model.h5')  # Keras
model.save_model('xgb_model.json')  # XGBoost
```

---

## 참고 자료

### 라이브러리 문서
- **pandas**: https://pandas.pydata.org/docs/
- **scikit-learn**: https://scikit-learn.org/stable/
- **TensorFlow/Keras**: https://www.tensorflow.org/guide
- **XGBoost**: https://xgboost.readthedocs.io/

### 시계열 예측 가이드
- Time Series Forecasting with LSTM
- XGBoost for Time Series Regression
- Feature Engineering for Time Series

### KDM SDK 문서
- API 개요: `docs/API_OVERVIEW.md`
- Query API: `docs/QUERY_API.md`
- 분석가 가이드: `docs/ANALYST_QUICKSTART.md`

---

## 전체 워크플로우 체크리스트

### 데이터 수집
- [ ] KDM SDK로 필요한 기간 데이터 수집
- [ ] pandas DataFrame으로 변환
- [ ] 기본 정보 확인 (shape, dtypes, head)

### 전처리
- [ ] 날짜 변환 및 정렬
- [ ] 결측치 확인 및 처리
- [ ] 이상치 확인 및 처리
- [ ] 데이터 타입 확인

### 특성 엔지니어링
- [ ] 시간 특성 추출 (month, dayofweek 등)
- [ ] Lag 특성 생성 (lag1, lag7 등)
- [ ] Rolling 특성 생성 (이동평균 등)
- [ ] 도메인 특성 추가 (필요시)

### 모델별 변환
- [ ] LSTM: 정규화 + 시퀀스 생성 (3D)
- [ ] XGBoost: 타겟 설정 + 결측치 제거 (2D)

### 분할 및 저장
- [ ] Train/Test 분할 (순서 유지!)
- [ ] 데이터 저장 (.npy, .csv)
- [ ] Scaler 저장 (중요!)

### 모델 학습
- [ ] 모델 구성 및 파라미터 설정
- [ ] 학습 (validation 포함)
- [ ] 평가 (RMSE, R² 등)
- [ ] 모델 저장

---

**마지막 업데이트**: 2025-12-26
**버전**: 1.0
