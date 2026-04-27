# Water Data Sidecar Package

This sidecar package copies the current demo workflow logic into reusable Python modules without changing the existing notebook or `helpers/` module.

## Local package runs

From the repo root, use the `src/` layout directly:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo create-new-project
PYTHONPATH=src python -m waterdata_toolbox_demo add-data --workflow-type discharge
PYTHONPATH=src python -m waterdata_toolbox_demo
```

If you prefer an installed package workflow:

```bash
pip install -e .
python -m waterdata_toolbox_demo create-new-project
python -m waterdata_toolbox_demo add-data --workflow-type gw_daily
python -m waterdata_toolbox_demo
```

## CLI examples

Create New Project:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo create-new-project \
  --bbox -82.859 31.899 -82.013 32.947 \
  --workflow-type discharge \
  --workflow-type gw_daily
```

Adding Data to Project:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo add-data \
  --workflow-type gw_periodic \
  --station-id 410947071344803 \
  --parameter-code 72019 \
  --start-date 1880-01-01 \
  --end-date 2100-01-01 \
  --output-dir outputs/usgs_waterdata_demo
```

## GUI launch

Launch the small desktop GUI by running the module with no arguments:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo
```

## Artifact outputs

- `add-data` writes:
  - one combined USGS-style JSON artifact built from `dataretrieval` results
  - one CSV export
  - one parquet export when available
- The add-data CSV now begins with two raw API metadata lines:
  - `# site_no,Description,Parameter,Statistic,TS_ID,IV_TS_ID`
  - a matching value row where `site_no` uses the raw `monitoring_location_id` such as `USGS-02225500`
- The add-data CSV body is reduced to:
  - `Time`
  - `Daily values`
  - `Approval status`
  - `Qualifier`
- `create-new-project` writes one combined USGS-style JSON artifact per workflow run.
- The JSON artifacts now wrap nested `FeatureCollection` blocks reconstructed from `dataretrieval` frames instead of flattening rows into a simple records array.

## Windows app build

Build the packaged Windows app on Windows, not macOS. From a Windows environment with the project checked out:

```bash
pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

The default build now emits an `onedir` app for faster startup instead of a single self-extracting `.exe`. Launch the packaged app from:

```text
dist/waterdata_toolbox_demo/waterdata_toolbox_demo.exe
```

The tradeoff is that distribution is now a folder-based app rather than one standalone file. The shared app entrypoint still uses CLI mode when arguments are present and opens the GUI when launched without arguments.
