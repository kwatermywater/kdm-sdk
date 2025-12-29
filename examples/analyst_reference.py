"""
분석가를 위한 참고 예제

이 파일은 KDM SDK로 데이터를 가져온 후,
pandas/matplotlib로 할 수 있는 일들을 보여주는 참고용 예제입니다.

⚠️ 주의: 이것은 SDK 기능이 아닙니다!
SDK는 데이터를 pandas DataFrame으로 변환하는 것까지만 담당합니다.
이후 분석은 여러분이 이미 알고 있는 pandas/matplotlib 지식을 활용하세요.
"""

import asyncio
from kdm_sdk import KDMQuery
import pandas as pd
import matplotlib.pyplot as plt


async def example_1_basic_analysis():
    """예제 1: 기본 통계 분석"""
    print("\n=== 예제 1: 기본 통계 분석 ===")

    # SDK로 데이터 가져오기
    result = await KDMQuery().dam("소양강댐").measurement("저수율").days(30).get()
    df = result.to_dataframe()

    # 여기서부터는 일반 pandas 사용 (SDK 역할 끝!)
    print("\n기본 통계:")
    print(df["저수율"].describe())

    print("\n평균:", df["저수율"].mean())
    print("중앙값:", df["저수율"].median())
    print("표준편차:", df["저수율"].std())


async def example_2_visualization():
    """예제 2: 시각화 (matplotlib)"""
    print("\n=== 예제 2: 시각화 ===")

    # SDK로 데이터 가져오기
    result = await KDMQuery().dam("소양강댐").measurement("저수율").days(30).get()
    df = result.to_dataframe()

    # 일반 matplotlib 사용
    plt.figure(figsize=(12, 6))
    plt.plot(df["datetime"], df["저수율"], marker="o")
    plt.title("소양강댐 저수율 추이")
    plt.xlabel("날짜")
    plt.ylabel("저수율 (%)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("soyang_chart.png")
    print("차트 저장: soyang_chart.png")


async def example_3_missing_values():
    """예제 3: 결측치 처리 (일반 pandas 기법)"""
    print("\n=== 예제 3: 결측치 처리 ===")

    result = await KDMQuery().dam("소양강댐").measurement("저수율").days(30).get()
    df = result.to_dataframe()

    # 일반 pandas로 결측치 확인
    missing = df["저수율"].isna().sum()
    print(f"결측치 개수: {missing}")

    if missing > 0:
        # 방법 1: 선형 보간
        df["저수율_보간"] = df["저수율"].interpolate()

        # 방법 2: 전진 채우기
        df["저수율_ffill"] = df["저수율"].ffill()

        # 방법 3: 평균으로 채우기
        df["저수율_mean"] = df["저수율"].fillna(df["저수율"].mean())

        print("결측치 처리 완료 (여러 방법으로)")


async def example_4_outliers():
    """예제 4: 이상치 탐지 (일반 통계 기법)"""
    print("\n=== 예제 4: 이상치 탐지 ===")

    result = await KDMQuery().dam("소양강댐").measurement("저수율").days(90).get()
    df = result.to_dataframe()

    # IQR 방법 (일반 통계 기법)
    Q1 = df["저수율"].quantile(0.25)
    Q3 = df["저수율"].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[(df["저수율"] < lower_bound) | (df["저수율"] > upper_bound)]
    print(f"이상치 개수: {len(outliers)}")

    if len(outliers) > 0:
        print("\n이상치 값들:")
        print(outliers[["datetime", "저수율"]])


async def example_5_resampling():
    """예제 5: 시계열 리샘플링 (일반 pandas 기법)"""
    print("\n=== 예제 5: 시계열 리샘플링 ===")

    # 시간 단위 데이터 가져오기
    result = await KDMQuery().dam("소양강댐").measurement("저수율").days(30).get()
    df = result.to_dataframe()

    # datetime을 인덱스로 설정 (pandas 표준)
    df.set_index("datetime", inplace=True)

    # 일일 평균으로 리샘플링
    daily = df.resample("D").mean()
    print("\n일일 평균:")
    print(daily.head())

    # 주간 평균으로 리샘플링
    weekly = df.resample("W").mean()
    print("\n주간 평균:")
    print(weekly)


async def example_6_correlation():
    """예제 6: 상관관계 분석 (pandas/scipy)"""
    print("\n=== 예제 6: 상관관계 분석 ===")

    # 여러 측정 항목 가져오기
    result = (
        await KDMQuery()
        .dam("소양강댐")
        .measurement(["저수율", "유입량", "방류량"])
        .days(30)
        .get()
    )
    df = result.to_dataframe()

    # pandas로 상관계수 계산
    correlation_matrix = df[["저수율", "유입량", "방류량"]].corr()
    print("\n상관계수 행렬:")
    print(correlation_matrix)


async def example_7_comparison():
    """예제 7: 여러 댐 비교 (pandas groupby)"""
    print("\n=== 예제 7: 여러 댐 비교 ===")

    # 배치 쿼리
    query = KDMQuery().facility_type("dam").measurement("저수율").days(7)
    query.add_site("소양강댐")
    query.add_site("충주댐")
    query.add_site("대청댐")

    results = await query.execute_batch()
    df = results.aggregate()

    # pandas groupby로 집계
    summary = df.groupby("site_name")["저수율"].agg(["mean", "min", "max", "std"])
    print("\n댐별 통계:")
    print(summary)

    # 피벗 테이블
    pivot = df.pivot_table(values="저수율", index="datetime", columns="site_name")
    print("\n피벗 테이블 (처음 5행):")
    print(pivot.head())


async def main():
    """모든 예제 실행"""
    print("=" * 60)
    print("KDM SDK 분석 참고 예제")
    print("=" * 60)
    print("\n⚠️  이 예제들은 SDK 기능이 아닙니다!")
    print("SDK는 데이터를 pandas로 변환하는 것까지만 제공합니다.")
    print("이후는 여러분이 이미 알고 있는 pandas 지식을 활용하세요.\n")

    await example_1_basic_analysis()
    await example_2_visualization()
    await example_3_missing_values()
    await example_4_outliers()
    await example_5_resampling()
    await example_6_correlation()
    await example_7_comparison()

    print("\n" + "=" * 60)
    print("✅ 모든 예제 완료!")
    print("=" * 60)
    print("\n이제 여러분만의 분석을 시작하세요! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
