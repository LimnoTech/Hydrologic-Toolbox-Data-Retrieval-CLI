# Hydrologic-Toolbox-Data-Retrieval-CLI Rename Design

## Goal

Rename the active CLI package from the `waterdata_toolbox_demo` / `waterdata-toolbox-demo` branding to `Hydrologic-Toolbox-Data-Retrieval-CLI`, and update the README to include the Hydrologic Toolbox and USGS Water Data API websites.

## Scope

- Rename the published package name to `hydrologic-toolbox-data-retrieval-cli`.
- Rename the Python module path to `hydrologic_toolbox_data_retrieval_cli`.
- Rename CLI-facing help and executable references to `hydrologic-toolbox-data-retrieval-cli`.
- Rename the PyInstaller spec and output references accordingly.
- Update active tests to import and execute the new module path.
- Update README references and add website links for:
  - Hydrologic Toolbox
  - USGS Water Data APIs overview
  - USGS Water Data API hub

## Non-Goals

- No backward-compatibility alias for the old module or CLI name.
- No behavior change to workflow logic, XML compatibility rules, or export formats.
- No cleanup of historical design/plan docs beyond the active README and package surface.

## File Strategy

- `README.md`: rewrite branding, command examples, and website section.
- `pyproject.toml`: rename package metadata and script entrypoint.
- `waterdata_toolbox_demo.spec`: rename to `hydrologic_toolbox_data_retrieval_cli.spec` and update module references.
- `src/waterdata_toolbox_demo/`: rename directory to `src/hydrologic_toolbox_data_retrieval_cli/` and update internal imports/docstrings.
- `tests/test_cli_signature.py` and `tests/test_xml_compat.py`: update imports, subprocess module target, and expected help text.

## Risks

- The clean break will invalidate any existing scripts still importing `waterdata_toolbox_demo` or calling `waterdata-toolbox-demo`.
- A partial rename could leave stale module references in the spec or tests, so verification must include a repo-wide search plus targeted pytest runs.
