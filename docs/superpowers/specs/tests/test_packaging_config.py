"""Focused validation for packaging configuration."""

from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyinstaller_spec_defaults_to_onedir_distribution():
    """The default packaged app should be emitted as an onedir distribution."""
    spec_text = (PROJECT_ROOT / "waterdata_toolbox_demo.spec").read_text()

    assert "exclude_binaries=True" in spec_text
    assert "COLLECT(" in spec_text


def test_packaging_docs_describe_onedir_output():
    """The active package metadata should point at the root CLI README, not legacy docs."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["readme"] == "README.md"
    assert "GUI" not in project["description"]
    assert "CLI-only" in project["description"]


def test_root_readme_describes_cli_product():
    """The root README should remain the active CLI-facing product document."""
    readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Water Data ToolBox `.exe`" in readme_text
    assert "create-new-project" in readme_text
    assert "add-data" in readme_text
    assert "GUI code still exists" not in readme_text


def test_legacy_package_doc_moves_to_sandbox():
    """The old package note should live under sandbox once the active package is CLI-only."""
    legacy_doc = PROJECT_ROOT / "sandbox" / "docs" / "waterdata-package-cli-gui.md"

    assert legacy_doc.exists()
    assert not (PROJECT_ROOT / "docs" / "waterdata-package-cli-gui.md").exists()
