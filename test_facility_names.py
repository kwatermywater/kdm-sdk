#!/usr/bin/env python3
"""
Test script to verify which facility names actually work with KDM MCP server
"""
import asyncio
import sys
sys.path.insert(0, '/home/claudeuser/kdm-sdk/src')

from kdm_sdk.client import KDMClient

async def test_facility_name(client, site_name, facility_type, measurement_item):
    """Test if a facility name works"""
    try:
        result = await client.get_water_data(
            site_name=site_name,
            facility_type=facility_type,
            measurement_items=[measurement_item],
            time_key="d_1",
            days=3
        )

        if result and isinstance(result, dict):
            success = result.get('success', False)
            data_count = len(result.get('data', [])) if result.get('data') else 0
            return {
                'name': site_name,
                'type': facility_type,
                'works': success,
                'data_points': data_count,
                'status': '✅ OK' if success and data_count > 0 else '❌ FAIL'
            }
        else:
            return {
                'name': site_name,
                'type': facility_type,
                'works': False,
                'data_points': 0,
                'status': '❌ FAIL'
            }
    except Exception as e:
        return {
            'name': site_name,
            'type': facility_type,
            'works': False,
            'error': str(e),
            'status': '❌ ERROR'
        }

async def main():
    print("=" * 80)
    print("KDM Facility Name Verification Test")
    print("=" * 80)
    print()

    client = KDMClient()
    await client.connect()

    # Test cases: (site_name, facility_type, measurement_item)
    test_cases = [
        # === 댐 (Dam) ===
        # 의암 variants
        ("의암댐", "dam", "저수율"),
        ("의암수력", "dam", "저수율"),
        ("C15 의암댐", "dam", "저수율"),

        # 팔당 variants
        ("팔당댐", "dam", "저수율"),
        ("팔당수력", "dam", "저수율"),
        ("C122 팔당댐", "dam", "저수율"),

        # 춘천댐 variants
        ("춘천댐", "dam", "저수율"),
        ("C8 춘천댐", "dam", "저수율"),

        # 청평 variants
        ("청평댐", "dam", "저수율"),
        ("C39 청평댐", "dam", "저수율"),

        # Known working dams for comparison
        ("소양강댐", "dam", "저수율"),
        ("충주댐", "dam", "저수율"),
        ("대청댐", "dam", "저수율"),
        ("안동댐", "dam", "저수율"),

        # === 수위관측소 (Water Level Station) ===
        ("춘천", "water_level", "수위"),
        ("춘천시(춘천댐하류)", "water_level", "수위"),
        ("환_춘천댐하", "water_level", "수위"),
        ("의암", "water_level", "수위"),
        ("청평", "water_level", "수위"),
        ("팔당", "water_level", "수위"),

        # === 우량관측소 (Rainfall Station) ===
        ("소양강댐우량", "rainfall", "우량"),
        ("춘천우량", "rainfall", "우량"),
        ("의암우량", "rainfall", "우량"),
        ("청평우량", "rainfall", "우량"),

        # === 기상관측소 (Weather Station) ===
        ("소양강댐기상", "weather", "기온"),
        ("충주댐기상", "weather", "기온"),

        # === 수질관측소 (Water Quality Station) ===
        ("소양강댐수질", "water_quality", "TOC"),
        ("팔당댐수질", "water_quality", "TOC"),
    ]

    results = []
    for site_name, facility_type, measurement in test_cases:
        print(f"Testing: {site_name:25} ({facility_type})... ", end='', flush=True)
        result = await test_facility_name(client, site_name, facility_type, measurement)
        results.append(result)
        print(result['status'])
        if 'error' in result:
            print(f"  Error: {result['error']}")
        elif result['works']:
            print(f"  Data points: {result['data_points']}")
        await asyncio.sleep(0.5)  # Be nice to the server

    await client.disconnect()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    working = [r for r in results if r['works']]
    failed = [r for r in results if not r['works']]

    print(f"✅ Working: {len(working)}")
    for r in working:
        print(f"   - {r['name']} ({r['type']}) - {r['data_points']} data points")

    print()
    print(f"❌ Failed: {len(failed)}")
    for r in failed:
        print(f"   - {r['name']} ({r['type']})")

    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    # Group by facility type
    by_type = {}
    for r in working:
        ftype = r['type']
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append(r['name'])

    type_names = {
        'dam': '댐',
        'water_level': '수위관측소',
        'rainfall': '우량관측소',
        'weather': '기상관측소',
        'water_quality': '수질관측소'
    }

    for ftype, names in sorted(by_type.items()):
        korean_name = type_names.get(ftype, ftype)
        print(f"✅ {korean_name} ({len(names)}개 작동):")
        for name in names:
            print(f"   - {name}")
        print()

    # Show failed by type
    failed_by_type = {}
    for r in failed:
        ftype = r['type']
        if ftype not in failed_by_type:
            failed_by_type[ftype] = []
        failed_by_type[ftype].append(r['name'])

    if failed_by_type:
        print("❌ 작동하지 않는 시설명:")
        for ftype, names in sorted(failed_by_type.items()):
            korean_name = type_names.get(ftype, ftype)
            print(f"   {korean_name}:")
            for name in names:
                print(f"      - {name}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
