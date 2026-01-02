"""
하류 관측소 분석 예제 (Downstream Station Analysis)

이 예제는 분석가를 위한 end-to-end 워크플로우를 보여줍니다:
1. find_related_stations()로 댐의 하류 관측소 찾기
2. 댐 방류량 + 하류 수위 데이터 조회
3. FacilityPair로 최적 시간차(lag) 분석
4. pandas DataFrame으로 저장

사용법:
    python downstream_analysis.py
"""

import asyncio
import pandas as pd
from kdm_sdk import KDMClient, FacilityPair


async def main():
    async with KDMClient() as client:
        # ============================================================
        # 1단계: 댐의 하류 관측소 자동 탐색
        # ============================================================
        print("=" * 60)
        print("1단계: 소양강댐 하류 관측소 탐색")
        print("=" * 60)

        result = await client.find_related_stations(
            dam_name="소양강댐",
            direction="downstream",
            limit=5
        )

        print(f"\n댐: {result['dam']['site_name']}")
        print("\n하류 관측소:")
        for i, station in enumerate(result["stations"], 1):
            print(f"  {i}. {station['site_name']} (ID: {station['site_id']})")
            print(f"     원본코드: {station.get('original_facility_code', 'N/A')}")

        # 분석할 하류 관측소 선택 (첫 번째)
        downstream_station = result["stations"][0]
        print(f"\n분석 대상: {downstream_station['site_name']}")

        # ============================================================
        # 2단계: 댐 방류량 + 하류 수위 데이터 조회
        # ============================================================
        print("\n" + "=" * 60)
        print("2단계: 데이터 조회 (30일, 시간별)")
        print("=" * 60)

        # 댐 방류량 데이터
        upstream_result = await client.get_water_data(
            site_name="소양강댐",
            facility_type="dam",
            measurement_items=["방류량"],
            days=30,
            time_key="h_1"
        )

        # 하류 수위 데이터
        downstream_result = await client.get_water_data(
            site_name=downstream_station["site_name"],
            facility_type="water_level",
            measurement_items=["수위"],
            days=30,
            time_key="h_1"
        )

        # DataFrame 변환 함수
        def to_dataframe(data: dict) -> pd.DataFrame:
            records = []
            for item in data.get("data", []):
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

        upstream_df = to_dataframe(upstream_result)
        downstream_df = to_dataframe(downstream_result)

        print(f"\n댐 방류량 데이터: {len(upstream_df)}개 레코드")
        print(f"하류 수위 데이터: {len(downstream_df)}개 레코드")

        # ============================================================
        # 3단계: FacilityPair로 시간차(lag) 분석
        # ============================================================
        print("\n" + "=" * 60)
        print("3단계: 최적 시간차(lag) 분석")
        print("=" * 60)

        pair = FacilityPair(
            upstream_name="소양강댐",
            downstream_name=downstream_station["site_name"],
            upstream_type="dam",
            downstream_type="water_level",
            upstream_data=upstream_df,
            downstream_data=downstream_df
        )

        # 최적 시간차 찾기 (0~12시간 범위)
        correlation = pair.find_optimal_lag(max_lag_hours=12)

        print(f"\n최적 시간차: {correlation.lag_hours:.1f}시간")
        print(f"상관계수: {correlation.correlation:.3f}")
        print(f"\n해석: 소양강댐에서 방류하면 약 {correlation.lag_hours:.1f}시간 후")
        print(f"      {downstream_station['site_name']}에서 수위 변화가 관측됩니다.")

        # ============================================================
        # 4단계: 시간차 적용된 DataFrame 생성 및 저장
        # ============================================================
        print("\n" + "=" * 60)
        print("4단계: DataFrame 저장")
        print("=" * 60)

        # 시간차를 적용한 통합 DataFrame
        aligned_df = pair.to_dataframe(lag_hours=correlation.lag_hours)

        print(f"\n통합 DataFrame 크기: {aligned_df.shape}")
        print(f"컬럼: {list(aligned_df.columns)}")
        print("\n미리보기:")
        print(aligned_df.head(10))

        # CSV로 저장
        output_file = "downstream_analysis_result.csv"
        aligned_df.to_csv(output_file, encoding="utf-8-sig")
        print(f"\n저장 완료: {output_file}")

        # ============================================================
        # 5단계: 추가 분석 (선택사항)
        # ============================================================
        print("\n" + "=" * 60)
        print("5단계: 추가 분석 예시")
        print("=" * 60)

        # 기본 통계
        print("\n[기본 통계]")
        print(aligned_df.describe())

        # 상관관계 (시간차 적용 후)
        print("\n[상관관계]")
        corr = aligned_df.corr()
        print(corr)

        # 피크 시간대 분석
        print("\n[시간대별 평균 방류량]")
        if hasattr(aligned_df.index, 'hour'):
            hourly_avg = aligned_df.groupby(aligned_df.index.hour).mean()
            print(hourly_avg)


if __name__ == "__main__":
    asyncio.run(main())
