import os
from pathlib import Path


def test_project_structure_exists():
    """프로젝트 디렉토리 구조 확인"""
    # Find project root (works in both Docker /app and local /home/claudeuser/kdm-sdk)
    base_path = Path(__file__).parent.parent

    assert base_path.exists()
    assert (base_path / "src" / "kdm_sdk").exists()
    assert (base_path / "tests").exists()
    # examples and README.md may not be mounted in Docker test environment
    # Only check if they exist in local development
    if base_path.name != "app":  # Not in Docker
        assert (base_path / "examples").exists()
        assert (base_path / "README.md").exists()


def test_package_files_exist():
    """필수 패키지 파일 존재 확인"""
    # Find project root
    base_path = Path(__file__).parent.parent

    assert (base_path / "src" / "kdm_sdk" / "__init__.py").exists()
    assert (base_path / "setup.py").exists()
    assert (base_path / "pyproject.toml").exists()


def test_package_importable():
    """패키지 import 가능 확인"""
    import kdm_sdk

    assert kdm_sdk.__version__ is not None
