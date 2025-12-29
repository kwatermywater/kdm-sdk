"""
수질 측정소 다항목 분석 템플릿

주요 수질 측정소에서 pH, DO, BOD, COD, SS, T-N, T-P 등 다양한 수질 지표를
일괄 조회하여 수질 상태를 종합 분석합니다.

Water Quality Parameters:
  - pH: 수소이온농도 (수질의 산성/알카리성)
  - DO: 용존산소량 (Dissolved Oxygen, 수중 생물 생존 지표)
  - BOD: 생물학적산소요구량 (Biochemical Oxygen Demand, 유기물 오염도)
  - COD: 화학적산소요구량 (Chemical Oxygen Demand)
  - SS: 부유물질량 (Suspended Solids)
  - T-N: 총질소 (Total Nitrogen, 부영양화 지표)
  - T-P: 총인 (Total Phosphorus, 부영양화 지표)

Usage:
    >>> import asyncio
    >>> from kdm_sdk.templates import load_python
    >>>
    >>> async def main():
    >>>     template = load_python("examples/templates/water_quality_analysis.py")
    >>>
    >>>     # Execute with default parameters (30 days)
    >>>     result = await template.execute()
    >>>     df = result.to_dataframe()
    >>>
    >>>     # Analyze water quality trends
    >>>     print("\\n=== Water Quality Summary ===")
    >>>     for param in ['pH', 'DO', 'BOD', 'COD']:
    >>>         if param in df.columns:
    >>>             print(f"{param}: mean={df[param].mean():.2f}, std={df[param].std():.2f}")
    >>>
    >>>     # Check for water quality violations
    >>>     if 'BOD' in df.columns:
    >>>         violations = df[df['BOD'] > 3.0]  # BOD standard for Grade 1b
    >>>         if len(violations) > 0:
    >>>             print(f"\\nBOD violations: {len(violations)} days exceeded 3.0 mg/L")
    >>>
    >>>     # Export for detailed analysis
    >>>     df.to_excel('water_quality_analysis.xlsx')
    >>>
    >>>     # Use with different parameters
    >>>     result_90d = await template.execute(days=90)
    >>>     result_90d.to_dataframe().to_csv('water_quality_90days.csv')
    >>>
    >>> asyncio.run(main())

Advanced Usage - Multi-site Comparison:
    >>> # Modify template to compare multiple sites
    >>> template_config = template.to_dict()
    >>> template_config['sites'].append({
    >>>     'site_name': '잠실수중보',
    >>>     'facility_type': 'water_quality'
    >>> })
    >>>
    >>> from kdm_sdk.templates import Template
    >>> multi_site_template = Template(template_config)
    >>> result = await multi_site_template.execute()
    >>> combined = result.aggregate()  # Combine all sites
"""

from kdm_sdk.templates import TemplateBuilder


def create_template():
    """수질 분석 템플릿 생성"""
    # Common water quality parameters
    water_quality_params = [
        "pH",  # 수소이온농도
        "DO",  # 용존산소량
        "BOD",  # 생물학적산소요구량
        "COD",  # 화학적산소요구량
        "SS",  # 부유물질량
        "T-N",  # 총질소
        "T-P",  # 총인
        "전기전도도",  # Electric Conductivity
        "총대장균군",  # Total Coliform
    ]

    return (
        TemplateBuilder("한강 수질 측정소 다항목 분석")
        .description("팔당댐 하류 주요 수질 측정소의 다항목 수질 지표 시계열 분석")
        .tags(["water_quality", "multi-parameter", "time_series", "environmental"])
        .site("팔당댐", facility_type="water_quality")
        .measurements(water_quality_params)
        .days(30)
        .time_key("d_1")
        .build()
    )


# Create template instance for direct import
template = create_template()


if __name__ == "__main__":
    import asyncio

    async def main():
        """Example execution with water quality analysis"""
        print(f"Template: {template.name}")
        print(f"Description: {template.description}")
        print(f"Tags: {', '.join(template.tags)}")

        config = template.to_dict()
        print(f"\nMeasurement Parameters ({len(config['measurements'])}):")
        for i, param in enumerate(config["measurements"], 1):
            print(f"  {i}. {param}")

        print(f"\nPeriod: {config['period']['days']} days")
        print(f"Time Key: {config['time_key']}")

        print("\n" + "=" * 60)
        print("NOTE: To execute this template, ensure KDM MCP server is running:")
        print("  result = await template.execute()")
        print("  df = result.to_dataframe()")
        print("=" * 60)

        # Example of water quality standards (Korean environmental standards)
        print("\n=== Korean Water Quality Standards (Reference) ===")
        standards = {
            "Grade 1a": {"BOD": "≤ 1 mg/L", "DO": "≥ 7.5 mg/L", "T-P": "≤ 0.01 mg/L"},
            "Grade 1b": {"BOD": "≤ 2 mg/L", "DO": "≥ 5.0 mg/L", "T-P": "≤ 0.02 mg/L"},
            "Grade 2": {"BOD": "≤ 3 mg/L", "DO": "≥ 5.0 mg/L", "T-P": "≤ 0.03 mg/L"},
            "Grade 3": {"BOD": "≤ 5 mg/L", "DO": "≥ 5.0 mg/L", "T-P": "≤ 0.05 mg/L"},
        }
        for grade, params in standards.items():
            print(f"{grade}: {params}")

    asyncio.run(main())
