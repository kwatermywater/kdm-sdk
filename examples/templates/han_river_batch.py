"""
한강 수계 댐 일괄 모니터링 템플릿

한강 수계의 주요 댐(소양강, 춘천, 의암, 청평, 팔당)의 저수율, 유입량, 방류량을
일괄 조회하여 수계 전체의 물 관리 현황을 파악합니다.

Usage:
    >>> import asyncio
    >>> from kdm_sdk.templates import load_python
    >>>
    >>> async def main():
    >>>     template = load_python("examples/templates/han_river_batch.py")
    >>>     result = await template.execute()
    >>>
    >>>     # Batch result provides multiple dam data
    >>>     dfs = result.to_dataframes()
    >>>     for dam_name, df in dfs.items():
    >>>         print(f"{dam_name}: {len(df)} records")
    >>>
    >>>     # Aggregate all dams into single DataFrame
    >>>     combined = result.aggregate()
    >>>     combined.to_excel('han_river_weekly_report.xlsx')
    >>>
    >>> asyncio.run(main())
"""

from kdm_sdk.templates import TemplateBuilder


def create_template():
    """한강 수계 주간 모니터링 템플릿 생성"""
    han_river_dams = ["소양강댐", "춘천댐", "의암댐", "청평댐", "팔당댐"]

    return (
        TemplateBuilder("한강 수계 주간 모니터링")
        .description("한강 수계 주요 댐의 저수율, 유입량, 방류량 일괄 모니터링")
        .tags(["han_river", "batch", "weekly", "monitoring"])
        .sites(han_river_dams, facility_type="dam")
        .measurements(["저수율", "유입량", "방류량"])
        .days(7)
        .time_key("d_1")
        .build()
    )


# Create template instance
template = create_template()


if __name__ == "__main__":
    import asyncio

    async def main():
        """Example execution"""
        print(f"Template: {template.name}")
        print(f"Description: {template.description}")

        config = template.to_dict()
        print(f"\nMonitoring {len(config['sites'])} dams:")
        for site in config["sites"]:
            print(f"  - {site['site_name']}")

        # Note: Requires KDM MCP server running
        # result = await template.execute()
        # print(f"\nFetched data for {len(result.to_dataframes())} dams")

    asyncio.run(main())
