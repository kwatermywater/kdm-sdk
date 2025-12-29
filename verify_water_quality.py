#!/usr/bin/env python3
"""
Verify water quality data retrieval with detailed output
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def verify_water_quality():
    client = KDMClient()
    await client.connect()

    print("=" * 80)
    print("수질 데이터 실제 조회 테스트")
    print("=" * 80)
    print()

    # Test different water quality stations
    stations = [
        "소양강댐1",
        "팔당댐",
        "청평"
    ]

    for station in stations:
        print(f"시설: {station}")
        print("-" * 80)

        try:
            result = await client.get_water_data(
                site_name=station,
                facility_type="water_quality",
                measurement_items=["TOC"],
                time_key="mt_1",
                days=365  # 1년치
            )

            if result and result.get('success'):
                data = result.get('data', [])
                print(f"✅ 성공! {len(data)}개 데이터 포인트")

                if data:
                    print(f"\n실제 데이터 구조 확인:")
                    print(f"  첫 번째 항목: {data[0]}")
                    print(f"\n실제 데이터 샘플 (최근 3개):")
                    for item in data[-3:]:
                        # Try different possible field names
                        date = item.get('tm') or item.get('time') or item.get('date') or item.get('measureDate', 'N/A')
                        value = item.get('value') or item.get('val') or item.get('TOC', 'N/A')
                        print(f"  {item}")
                else:
                    print("  데이터는 있으나 비어있음")
            else:
                print(f"❌ 실패 또는 데이터 없음")
                print(f"  응답: {result}")

        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")

        print()
        await asyncio.sleep(0.5)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_water_quality())
