"""
실시간 홍수 감시 템플릿

댐 방류량, 수위 관측소 데이터, 기상 정보를 종합하여 홍수 위험을 실시간으로
모니터링하는 템플릿입니다. 시간 단위 데이터를 사용하여 급격한 변화를 감지합니다.

Monitoring Components:
  - 댐 방류량: 상류 댐의 실시간 방류 현황
  - 수위: 주요 수위 관측소의 수위 변화
  - 강우량: 유역 내 강우 현황
  - 기상 정보: 기온, 습도 등 기상 조건

Flood Risk Indicators:
  - 댐 방류량 급증 (> 1000 m³/s)
  - 수위 급상승 (홍수위 접근)
  - 집중 호우 (시간당 30mm 이상)
  - 연속 강우 (48시간 누적 150mm 이상)

Usage:
    >>> import asyncio
    >>> from kdm_sdk.templates import load_python
    >>>
    >>> async def main():
    >>>     template = load_python("examples/templates/real_time_flood_watch.py")
    >>>
    >>>     # Execute with default 48-hour window
    >>>     result = await template.execute()
    >>>     dfs = result.to_dataframes()
    >>>
    >>>     # Analyze dam discharge
    >>>     dam_data = dfs.get('소양강댐')
    >>>     if dam_data is not None and '방류량' in dam_data.columns:
    >>>         current_discharge = dam_data['방류량'].iloc[-1]
    >>>         max_discharge = dam_data['방류량'].max()
    >>>
    >>>         print(f"Current discharge: {current_discharge:.1f} m³/s")
    >>>         print(f"Max discharge (48h): {max_discharge:.1f} m³/s")
    >>>
    >>>         if max_discharge > 1000:
    >>>             print("⚠️  WARNING: High discharge detected!")
    >>>
    >>>     # Check water level
    >>>     wl_data = dfs.get('춘천')
    >>>     if wl_data is not None and '수위' in wl_data.columns:
    >>>         current_level = wl_data['수위'].iloc[-1]
    >>>         level_change = wl_data['수위'].iloc[-1] - wl_data['수위'].iloc[-24]
    >>>
    >>>         print(f"\\nCurrent water level: {current_level:.2f}m")
    >>>         print(f"24h change: {level_change:+.2f}m")
    >>>
    >>>         if level_change > 1.0:
    >>>             print("⚠️  WARNING: Rapid water level rise!")
    >>>
    >>>     # Check rainfall
    >>>     rain_data = dfs.get('춘천_rainfall')
    >>>     if rain_data is not None and '강수량' in rain_data.columns:
    >>>         total_rain = rain_data['강수량'].sum()
    >>>         max_hourly = rain_data['강수량'].max()
    >>>
    >>>         print(f"\\nTotal rainfall (48h): {total_rain:.1f}mm")
    >>>         print(f"Max hourly rainfall: {max_hourly:.1f}mm")
    >>>
    >>>         if max_hourly > 30:
    >>>             print("⚠️  WARNING: Heavy rainfall detected!")
    >>>
    >>>     # Export for alert system
    >>>     combined = result.aggregate()
    >>>     combined.to_csv('flood_watch_latest.csv')
    >>>
    >>> asyncio.run(main())

Real-time Monitoring Setup:
    >>> # Run every hour via cron job or scheduler
    >>> import schedule
    >>> import time
    >>>
    >>> async def hourly_check():
    >>>     template = load_python("examples/templates/real_time_flood_watch.py")
    >>>     result = await template.execute(days=2)  # Last 48 hours
    >>>
    >>>     # Your flood detection logic here
    >>>     dfs = result.to_dataframes()
    >>>     # ... analyze and send alerts if needed ...
    >>>
    >>> def scheduled_job():
    >>>     asyncio.run(hourly_check())
    >>>
    >>> # Schedule to run every hour
    >>> schedule.every().hour.do(scheduled_job)
    >>>
    >>> while True:
    >>>     schedule.run_pending()
    >>>     time.sleep(60)
"""

from kdm_sdk.templates import TemplateBuilder


def create_template():
    """실시간 홍수 감시 템플릿 생성"""
    return (
        TemplateBuilder("실시간 홍수 감시")
        .description("댐, 수위, 강우 데이터를 시간 단위로 수집하여 홍수 위험 모니터링")
        .tags(["flood", "real-time", "monitoring", "hourly", "alert"])
        .site("소양강댐", facility_type="dam")
        .site("춘천", facility_type="water_level")
        .site("춘천", facility_type="rainfall")
        .measurements(
            [
                "방류량",  # Dam discharge
                "저수위",  # Dam water level
                "수위",  # River water level
                "강수량",  # Rainfall
            ]
        )
        .days(2)
        .time_key("h_1")
        .build()
    )


# Create template instance for direct import
template = create_template()


if __name__ == "__main__":
    import asyncio

    async def main():
        """Example execution with flood monitoring analysis"""
        print(f"Template: {template.name}")
        print(f"Description: {template.description}")
        print(f"Tags: {', '.join(template.tags)}")

        config = template.to_dict()
        print(f"\nMonitoring Sites ({len(config['sites'])}):")
        for i, site in enumerate(config["sites"], 1):
            print(f"  {i}. {site['site_name']} ({site['facility_type']})")

        print(f"\nMeasurements: {', '.join(config['measurements'])}")
        print(f"Period: {config['period']['days']} days (48 hours)")
        print(f"Time Key: {config['time_key']} (hourly data)")

        # Display flood risk thresholds
        print("\n" + "=" * 60)
        print("=== Flood Risk Thresholds (Reference) ===")
        print("=" * 60)
        thresholds = {
            "Dam Discharge": {
                "Normal": "< 500 m³/s",
                "Attention": "500-1000 m³/s",
                "Warning": "1000-2000 m³/s",
                "Alert": "> 2000 m³/s",
            },
            "Hourly Rainfall": {
                "Normal": "< 10 mm/h",
                "Attention": "10-30 mm/h",
                "Warning": "30-50 mm/h",
                "Alert": "> 50 mm/h",
            },
            "Water Level Rise": {
                "Normal": "< 0.5m / 24h",
                "Attention": "0.5-1.0m / 24h",
                "Warning": "1.0-2.0m / 24h",
                "Alert": "> 2.0m / 24h",
            },
        }

        for category, levels in thresholds.items():
            print(f"\n{category}:")
            for level, threshold in levels.items():
                print(f"  {level:12s}: {threshold}")

        print("\n" + "=" * 60)
        print("NOTE: To execute this template, ensure KDM MCP server is running:")
        print("  result = await template.execute()")
        print("  dfs = result.to_dataframes()")
        print("=" * 60)

        print("\n=== Use Cases ===")
        use_cases = [
            "1. 실시간 홍수 조기 경보 시스템",
            "2. 댐 방류 영향 분석 (하류 수위 예측)",
            "3. 집중호우 감지 및 대응",
            "4. 수계 통합 관리 모니터링",
            "5. 재난 대응 의사결정 지원",
        ]
        for use_case in use_cases:
            print(f"  {use_case}")

    asyncio.run(main())
