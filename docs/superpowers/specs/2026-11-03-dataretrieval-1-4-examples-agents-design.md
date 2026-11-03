# dataretrieval 1.4, packaging, CI, examples and AGENTS.md

Design spec, 2026-11-03. Decisions are Anthony Aufdenkampe's (maintainer) unless marked
*builder's call* (settled by the spec's author, open to correction) or *left to the builder*.

## Why

This repository builds the Windows executable the USGS Hydrologic Toolbox calls to retrieve
USGS Water Data. Luka Ludden, who wrote it, has left LimnoTech; Anthony Aufdenkampe now
maintains it. Paul Duda builds and revises the Hydrologic Toolbox on Windows and tests the
executable inside it.

Four things need to happen, and they are coupled enough to share one round:

1. **dataretrieval 1.4.** It requests v1 of the USGS Water Data APIs and changes column
   types. The CLI does not pin dataretrieval at all, and nothing records which version built
   the v0.1.0 release (2026-09-23).
2. **Packaging and CI.** The build cannot be reproduced: `pixi.lock` and `pixi.toml` are
   git-ignored, the only declared pixi platform is `osx-arm64` (the product is a Windows exe),
   there are no pixi tasks and no CI. The LimnoTech packaging audit, run 2026-11-03, reports
   1 pass, 2 fail, 5 warn.
3. **AGENTS.md.** The repo is developed with AI coding agents but has no agent guidance. Its
   sibling repos point at LimnoTech's private `limno-agent-skills` repo for process; this
   repo is open source, so the guidance it needs must be written into it.
4. **Examples.** Commit `55a7d98` (2026-09-23) deleted `sandbox/`. Anthony wants examples
   back, written fresh, explaining both how to use the CLI and how it turns Water Data API
   responses into its outputs.

## Goals

- The CLI runs on dataretrieval `>=1.4` (Water Data API v1) and produces outputs the
  Hydrologic Toolbox accepts, verified by Paul before release.
- Anyone can rebuild the exact environment and exe from the repo: one `pyproject.toml`,
  a committed `pixi.lock`, pixi tasks for every routine command.
- CI tests every push, tests three OSes before `main`, and builds the Windows exe.
- An `AGENTS.md` that stands on its own in a public repo.
- An `examples/` folder with two notebooks and a small set of legacy reference files.

## Non-goals

- New CLI features, new workflows or new Water Data endpoints.
- Restoring the old sandbox as it was (decided: skip it).
- Publishing to PyPI or conda-forge.
- A GUI.

## Anti-goals

The round fails, even if every test passes, if:

- **The Toolbox contract changes without Paul's sign-off.** The contract is: the XML request
  shapes and the `<success>`/`<error>` response strings of `xml-compat`; the CSV layout of each
  workflow (header lines, column names, column order, value formatting, date formatting); and
  the shapefile file names, field names, field types and widths, and `.prj`. Any change to any
  of these is a breaking change, listed in the PR and approved by Paul before release.
- A release is published before Paul has tested its build in the Toolbox.
- The Water Data app key (Part B2) appears anywhere in the repository, a log, a CI output
  or a file the CLI writes, or users are asked to supply a token of their own.
- The repo links to anything private (`limno-agent-skills`, `water-data-engine`) as something
  a reader must follow to work here. Naming them as where a rule came from is fine.

## Constraints

- **Public repository**, MIT licence (`License.md`).
- **The product is a Windows exe** built with PyInstaller from
  `hydrologic_toolbox_data_retrieval_cli.spec`. Development happens on macOS too.
- **Live tests hit public USGS services** unkeyed. Keep request counts small.
- **Stations already used by the README and tests** are the probe and test targets:
  `02225500` (discharge), `324209082430201` (gw_daily), `410947071344803` (gw_periodic), and
  the README's Georgia bounding box `-82.859 31.899 -82.013 32.947`.

---

## Part A — Packaging (`pyproject.toml`)

Follow the LimnoTech packaging pattern, as ras2xugrid (also headed for public) does. Its
`pyproject.toml` is the nearest template; the AGENTS.md written in Part D must carry whatever
the reader needs of the pattern, since the skill itself is private.

1. **Build backend:** `hatchling` + `hatch-vcs`; `dynamic = ["version"]` replaces
   `version = "0.1.0"`; `fallback-version = "0.0.0"`; version file
   `src/hydrologic_toolbox_data_retrieval_cli/_version.py`, git-ignored. Wheel packages
   `["src/hydrologic_toolbox_data_retrieval_cli"]`. The PyInstaller build must see a real
   version, so the build task runs from the editable install, which writes `_version.py`.
   `__init__.py` exposes `__version__` from it.
2. **Metadata:** `license = "MIT"`, `license-files = ["License.md"]`, no `License ::`
   classifier. `authors`: LimnoTech and Luka Ludden. `maintainers`: Anthony Aufdenkampe
   (`aaufdenkampe@limno.com`). `[project.urls]` for Homepage, Repository, Issues. Keywords and
   classifiers in ras2xugrid's style (Hydrology, GIS; `Operating System :: Microsoft ::
   Windows` alongside OS Independent is the builder's choice).
3. **Dependencies, declared twice.** PyPI names in `[project.dependencies]`; conda names in
   `[tool.pixi.feature.core.dependencies]`. `dataretrieval>=1.4` in both. Current runtime
   imports are `dataretrieval`, `pandas`, `geopandas` (lazily in `station_discovery.py`,
   directly in `exports.py`), `pyproj` and `pyshp` (imported as `shapefile`). Add
   `tests/test_dependency_parity.py` that fails when the two lists differ in names or floors.
   Copy ras2xugrid's test if it is self-contained; otherwise write one.
4. **pyarrow exemption, to be measured.** The family rule "pandas implies pyarrow" fails this
   repo's audit. pyarrow may add a large amount to the PyInstaller bundle, and the Toolbox only
   receives CSVs and shapefiles. Build the exe with and without pyarrow, record both bundle
   sizes and startup times (`--help` wall time, best of five, on the Windows runner), and
   bring both numbers to the group 1 gate for Anthony to decide. The builder's recommendation
   goes with them: include pyarrow if it adds under about 30 MB to the zipped bundle and under
   0.5 s to startup, otherwise exempt the repo and record the measurement and reason in
   AGENTS.md. If dataretrieval or geopandas
   already pull pyarrow in transitively, it is in either way; declare it.
5. **Pixi workspace:** channels `["conda-forge", "nodefaults"]`; platforms
   `["linux-64", "osx-arm64", "win-64"]`, all three exercised by CI. Python pinned in `core`
   (*builder's call:* `3.12.*`, the newest PyInstaller and the stack support comfortably;
   `requires-python = ">=3.11"` stays as the package's support range).
   Features: `core`; `dev` (pytest, ruff, pyrefly; no Jupyter); `jupyter` (jupyterlab,
   jupytext, matplotlib-base, ipykernel); `build` (pyinstaller). Environments:
   `default` = core + dev + jupyter; `ci` = core + dev; `build` = core + build. One
   solve group, so the exe is built from the versions the tests ran on.
6. **Tasks:** `test` (offline), `test-live` (`-m live`), `lint`, `format`, `typecheck`,
   `build-exe` (the PyInstaller command from the README, in the `build` environment), and a
   task that runs the CLI module (`python -m hydrologic_toolbox_data_retrieval_cli`) so
   macOS users can run it without the exe.
7. **Tool config:** `[tool.ruff]` line-length 100, `extend-exclude = ["examples"]`, select
   `E, F, I, UP, B`. `[tool.pytest.ini_options]`: `testpaths = ["tests"]`,
   `addopts = "-ra -m 'not live'"`, the existing `live` marker. `[tool.pyrefly]` on the
   package. `[tool.jupytext] formats = "ipynb,py:percent"`.
8. **Lint baseline.** Ruff will likely flag existing code. A reformat is its own commit
   containing nothing else. A lint fix that could change behaviour is out of scope: suppress it
   with a `# noqa` and a reason instead.
9. **Commit `pixi.lock`.** Remove `pixi.lock`, `pixi.toml` and the stale `sandbox/...` lines
   from `.gitignore`. Also remove `*.spec`, which ignores the tracked PyInstaller spec. Add
   `_version.py` and `_app_key.py` (Part B2). Check that `.pixi/` and `build/` stay ignored. The `dist/*` exclusion with
   `!dist/outputs/` stays as it is.
10. **`--version` flag** (*builder's call*): add `--version` to the CLI, printing the
    hatch-vcs version. It adds to the CLI surface without touching the XML/CSV/shapefile
    contract, and lets Paul confirm which build he is testing.

## Part B — dataretrieval 1.4

**Probe first, then change code.** water-data-engine moved to 1.4 in its PR #82 (merged
2026-11-01) with a probe script and log of what v1 returns. Do the same here, under
`examples/sandbox/dataretrieval_1_4/`: `probe.py`, its captured output `probe.out`, and
`log.md` recording findings with dates. Probe every dataretrieval call the CLI makes
(`get_monitoring_locations`, `get_time_series_metadata`, `get_daily`,
`get_field_measurements`), for the stations and bbox under Constraints, and on both 1.3.x and
1.4, so the log shows the difference column by column.

What water-data-engine found, to check here, not to assume:

- `construction_date` is the string the service sends, at day, month or year precision
  (`19450206`, `191904`, `1850`); 1.4 leaves it unparsed. The CLI writes it into the periodic
  CSV header (`timeseries.py`) and maps it to the shapefile field `construction_dt`
  (`exports.py`). Previously parsed as a datetime, it became a 254-wide `C` field
  (`_infer_shapefile_field_spec`). Check what each output contained before and after.
- Time-series metadata: `begin`/`end` are now UTC (`+00:00`); `begin_utc`, `end_utc`,
  `hydrologic_unit_code` and `state_name` are gone; `statistics_begin` is new. The CLI reads
  the HUC from monitoring locations (`timeseries.py`), which still carry it, but confirm no
  path reads these fields from metadata.
- Numeric `value` columns are always `float64`, and an unparseable value becomes missing with
  a warning. The committed reference CSV (`dist/outputs/add_data_discharge/`, generated
  2026-05-27) already writes `1740.0`, so the CSV text is expected not to change; confirm it.
- The CLI filters a pandas "Could not infer format" warning around every dataretrieval call
  (`timeseries.py`, `station_discovery.py`). If 1.4 no longer triggers it, remove the filters.
  If it still does, keep them. Either way, 1.4's new unparseable-value warning must not be
  swallowed: route it to the `--debug` stream.
- v0 shape: water-data-engine refuses to run if dataretrieval is configured for v0
  (`api_version = "v0"`). Do the same, raising the CLI's normal `<error>` response.
  water-data-engine detects v0 by the *shape* of the returned time-series metadata (a
  `begin_utc` column present) rather than by reading dataretrieval's configuration; see
  `src/water_data_engine/sources/usgs/waterdata.py` around its `begin_utc` check. Do the same,
  per call, where the CLI reads time-series metadata, so every entry point (`xml-compat`
  included) gets it.

**How the probe gets two versions** (*builder's call*): the locked environments hold one
version at a time, so the probe runs 1.3.x in a throwaway environment outside the manifest
(for example `pixi exec --spec "dataretrieval==1.3.*" ...`), and 1.4 in `default`.
dataretrieval 1.4.0 is on conda-forge (`noarch`, published 2026-10-03, checked with
`pixi search` on 2026-11-03), so the conda half of the dual declaration can carry `>=1.4`.

**Proof of compatibility before Paul sees it:**

1. Offline tests updated from the probe's v1 responses (fixtures, not live calls), with exact
   expected strings for every header line and file name (assert exact values, never shape).
2. A regeneration of every file under `dist/outputs/` with the new build, diffed against the
   committed versions. Each folder's command is the matching row of the README's Commands
   table (same workflow, station, bbox, dates and output folder), run through the module
   rather than the exe; write them into a small script under
   `examples/sandbox/dataretrieval_1_4/` so the regeneration is repeatable. Every difference
   is either fixed or explained in the PR as data changing at the source (new daily values
   since 2026-05-27, a re-approved value) versus format changing. Format changes are contract
   changes (Anti-goals). The comparison rule (*builder's call*): header lines, column names
   and order, file names, and shapefile field names, types and widths must match exactly;
   values are compared only on dates present in both files, and the record count is reported,
   not required to match. Commit the regenerated outputs once Paul has signed off, so they
   become the new reference.
3. `pixi run test-live` passes against v1.

**Hand-off to Paul:** a Windows build from CI (Part C), and `docs/toolbox-test-checklist.md`
listing each request to run in the Toolbox (station discovery for each `DataType`, add-data
for each workflow, a multi-function bundle, one deliberately invalid request) and what each
should produce. Any expected difference from v0.1.0's outputs is listed there too.
Release `v0.2.0` only after he reports back.

**Sequence of the hand-off** (*builder's call*): at the round-end gate the agent hands over a
PR title and description; Anthony opens the PR as a **draft** into `main`, whose
`pull_request` run builds the exe artifact Paul downloads. Paul's result is recorded as a PR
comment (by Paul or by Anthony relaying it). Fixes from his testing, and the commit of the
regenerated `dist/outputs/`, are follow-up commits on the same branch after that comment,
each one a short gate of its own. Anthony then marks the PR ready, merges, and pushes the
`v0.2.0` tag; tagging is a human action, like pushing.

## Part B2 — Water Data app key

Today the CLI sends every request unkeyed: it reads no token, and its only environment
variables are its two debug switches. dataretrieval 1.4.0 would pick up a user's own key
from `API_USGS_PAT` or `~/.dataretrieval/config.toml`, but **users are not to provide a
token** (decided). Instead LimnoTech will obtain an "app" key from the api.waterdata
development team (Anthony is arranging it, 2026-11-03), and the exe carries it.

- **Never in the repository.** The key lives in a GitHub Actions secret
  (`WATERDATA_APP_KEY`). The `build-exe` job writes it into a generated, git-ignored module
  (`src/hydrologic_toolbox_data_retrieval_cli/_app_key.py`) before PyInstaller runs, so it is
  bundled into the exe. A local or source build without the secret writes no module and the
  CLI runs unkeyed. The module is never committed, printed, logged or written to an output.
- **How the CLI applies it.** Every dataretrieval call runs inside one
  `dataretrieval.configure(api_key=...)` block opened by the CLI's entry point, so it covers
  `create-new-project`, `add-data` and `xml-compat` alike. A `configure` block takes
  precedence over `API_USGS_PAT` and the config file (dataretrieval 1.4.0's
  `_configuration_core.py`), so a stray user key does not change what the exe sends
  (*builder's call*; consistent with users not providing tokens). With no embedded key, the
  CLI opens no block and dataretrieval's own defaults apply.
- **Visible without being revealed.** `--debug` reports `Water Data app key: embedded` or
  `none`, never the value. `--version` output may carry the same flag (*left to the
  builder*).
- **CI.** The secret is available to `build-exe` on pushes, PRs from this repository,
  `workflow_dispatch` and tags; PRs from forks get no secrets and build unkeyed, which is
  fine. A `live` job, if added, uses the same secret. The smoke test asserts the key state:
  on a `v*` tag the build must report `embedded`, and fails otherwise, so a release cannot
  ship unkeyed by accident; elsewhere either state passes, and the job log says which.
- **Tests.** Offline tests cover both states: with a fake key, every dataretrieval call is
  made inside a `configure` block carrying it (asserted with an exact value); with none, no
  block is opened. No test reads the real secret.
- **The key is extractable from the exe.** Anything bundled in a client-side program can be
  read by someone who unpacks it. That is normal for an app key that identifies an
  application for rate limits, but it is the USGS team's call: confirm with them, when the
  key is issued, that an embedded key is the intended use, and how to rotate it. Record
  their answer in AGENTS.md.
- **Sequencing.** The round's code works with or without the key. The key must be in the
  secret before `v0.2.0` is tagged; the tag-build assertion enforces it. Paul's test builds
  should carry it, so he tests what will ship.

## Part C — CI (`.github/workflows/ci.yaml`)

Adapt ras2xugrid's workflow; drop everything about checking out water-data-engine.

- **`test` job.** `push` (any branch, `paths-ignore` markdown): Ubuntu only. `pull_request`
  into `main` and `workflow_dispatch`: Ubuntu, macOS and Windows. `setup-pixi` with
  `environments: ci` (plural; the singular is silently ignored), `locked: true`,
  `cache: true`; `fetch-depth: 0` for hatch-vcs. Steps: tests (with `PYTHONFAULTHANDLER=1`),
  lint, format check. Offline tests only.
- **`typecheck` job** on `default`, Ubuntu only.
- **`build-exe` job**, Windows, on PRs into `main`, `workflow_dispatch` and `v*` tags. Runs
  the `build-exe` task. Smoke-tests the built exe: `--help` exits 0; `--version` prints
  exactly the version in the build's `_version.py` (on a non-tag commit that is hatch-vcs's
  `X.Y.Z.devN+gSHA` form, on a `v*` tag the tag's version); an `xml-compat` call with a malformed request prints exactly one
  `<error>...</error>` on stdout (offline). Uploads the zipped
  `dist\hydrologic_toolbox_data_retrieval_cli\` folder as a workflow artifact, which is what
  Paul downloads for testing.
- **On a `v*` tag**, the same job attaches the zip to a **draft** GitHub Release
  (`contents: write`). Anthony publishes it after Paul's sign-off. This path cannot be
  exercised before the first real tag; the release step is kept small so that review of the
  YAML is enough, and the hand-back says it is untested.
- Push and PR runs follow ras2xugrid's policy, including its `concurrency` block: a commit on
  a PR branch gets Ubuntu twice (once per event), which ras2xugrid accepts for the simplicity.
- A `live` job is *left to the builder*: if added, `workflow_dispatch` only, never on push,
  so CI does not depend on USGS uptime.

Read the CI log for the collected test count; green with zero collected tests is a failure.

## Part D — `AGENTS.md` and `CLAUDE.md`

`CLAUDE.md` is one line, `@AGENTS.md` (Claude Code discovers `CLAUDE.md`, not `AGENTS.md`;
the stub is load-bearing). `AGENTS.md` follows the shape of the sibling repos' files: a
pointer to README for *what the project is*, then how to work here. Aim near ras2xugrid's
length for the local part. Because this repo is public, the process rules are **written into
the file**, not linked. Name LimnoTech's internal guide once as their origin, and never as
something a reader must follow to work here.

Sections:

1. **Critical guardrails.**
   - Agents commit on a branch; never push, merge, publish a release or work on `main`.
     Commit messages carry no AI co-author trailer (a PR description may credit the assistant).
   - A new branch never tracks `main`: branch from local `main` or use `--no-track` from a
     remote ref; check `git branch -vv` before every hand-back. The reason in one sentence:
     VS Code's Push/Sync and GitHub Desktop push to the upstream, so the branch lands on
     `main` with no PR.
   - **The Toolbox contract** (as defined under Anti-goals) changes only with Paul Duda's
     sign-off; such a change is a breaking change in the PR.
   - Multi-step work pauses at each task-group gate. Every review finding, Minor included,
     is fixed before the hand-back.
   - Dependencies are declared twice (Part A.3); the parity test enforces it.
   - The pyarrow ruling from Part A.4, with its measurement.
2. **How a round runs.** Condensed from `agent-workflow.md`, in this repo's terms:
   brainstorm → spec → plan → execute → review → hand back; specs and plans under
   `docs/superpowers/specs|plans/`; task-groups and the gate; an integration branch for a
   multi-group round, one merge to `main` per round; closing worktrees before hand-back
   (ignored files die with them); one subagent per unit of judgment, named model tier,
   review on spec + quality from a diff file; the fix loop and scoped re-review; the ledger
   (`progress.md` in a git-ignored workspace); rule, don't stall, and the four things that
   stop you (irreversible, security-sensitive, publishing, a broken plan); report failure
   plainly; hand over a PR title and description at each gate, written for GitHub with no
   hard wraps; recommend clearing the session at each gate.
3. **Rules the work itself taught**, kept with one-line reasons: assert exact output
   strings; when a defect class recurs, fix the contract that permits it; never judge success
   through a pipe; test what CI has; green by skipping is worse than red; bisect a CI-only
   failure mechanically; stage after each verified step; doc claims are re-measured, and
   every number has a command behind it; prefer claims that cannot rot; land a reformat
   alone; write commands for the shell they run in (zsh `$VAR:path`; PowerShell
   `$LASTEXITCODE`; PowerShell's `--%` for inline XML, already in the README); draft upstream
   issues under `docs/upstream/` for a human to file.
4. **Finishing a round:** `pixi update` as its own commit (never `pixi upgrade`, which
   rewrote deliberate pins in a probe), `pixi upgrade --dry-run` listed in the PR, full
   verification, a final whole-branch review, every ruling listed with its cost if wrong.
   Include the lock/update/upgrade table.
5. **Verification:** exact task names, the `live` marker, and how notebooks are executed
   headlessly.
6. **Notebooks:** edit the jupytext `.py`, not the `.ipynb`; sync with
   `pixi run jupytext --sync <file>.py`; execute before committing; written for water data
   scientists fluent in pandas and geopandas, with markdown saying what each table and
   figure shows.
7. **Sandbox convention:** `examples/sandbox/<topic>/` holds probes and one-off
   investigations (script, captured output, dated `log.md`), committed as evidence. Not
   imported by `src/` or `tests/`.
8. **Gotchas**, with provenance (*learned here* / *learned in a sibling repo, not yet
   verified here*): the dataretrieval 1.4 changes as measured by Part B's probe; PowerShell
   inline XML; anything Part A turns up about PyInstaller.

## Part E — Examples

```text
examples/
  README.md                       what each notebook is for, how to run it
  1_using_the_cli.py / .ipynb
  2_inside_the_cli.py / .ipynb
  reference_data/
    README.md                     provenance and why kept
    legacy_nwis_rdb/
      dv.txt                      02225500 daily discharge, legacy NWIS, retrieved 2026-04-07
      site.txt
      NWIS_gw_periodic_324937083433001.txt
    api_waterdata_v0/
      monitoring_locations_items.json
      monitoring_locations_items.csv
  sandbox/
    dataretrieval_1_4/            Part B's probe
```

Notebooks are jupytext pairs; both files are committed, the `.ipynb` executed with outputs.
Both need network access and are run by hand, not by CI. File names are *left to the
builder* within this shape.

**`1_using_the_cli`** — for someone calling the exe, or wiring the Toolbox's XML calls. Runs
the CLI through `python -m hydrologic_toolbox_data_retrieval_cli` via `subprocess` (works on
every OS; note the equivalent exe command for Windows). Covers `create-new-project` (one
workflow, then several), `add-data` for each workflow, and `xml-compat` with a station
request, an add-data request, a bundle and an invalid request, showing the exact stdout.
Opens what was written: the shapefile with geopandas (attribute table and a simple map),
the CSV's header lines and first rows. Output goes to a git-ignored folder under `examples/`.

**`2_inside_the_cli`** — for someone maintaining the CLI or checking its outputs. Calls
`dataretrieval.waterdata` directly and shows the raw frames for the four calls the CLI
makes, then walks through how the package turns them into outputs by calling the package's
own functions (never copies of them): selecting the matching metadata and monitoring-location
rows; the CSV header metadata and body; the NWIS crosswalk and shapefile field specs; bbox
reprojection in `xml_compat`. Ends with a side-by-side of a legacy RDB file from
`reference_data/` and the CLI's CSV for the same station, mapping columns across. Where it
needs a private helper (a leading-underscore function), that is acceptable in this notebook,
which documents internals; if it would need many, that is a signal to the builder to note it
in the hand-back, not to refactor `src/` in this round.

**`reference_data/`** — restored with `git show 55a7d98^:sandbox/example_data/<path>` from
the deleted sandbox (added in `1621ba9`, 2026-04-28, and `d4add41`, 2026-04-29). Kept
because legacy NWIS is being retired and these show what the Toolbox received before this
CLI. The README states that, the retrieval dates from each file's header, and the source
commits. **Not** restored: `dv_items.json` (9.9 MB) and `dv_items.csv`, re-fetchable;
helpers, GUI, checkpoints, old notebooks.

## Housekeeping

- Delete `docs/superpowers/specs/tests/` (three files). They import
  `waterdata_toolbox_demo`, the package's name before the rename, so they cannot run.
  `testpaths` would exclude them anyway.
- README: replace `pip install -e ".[build]"` with the pixi tasks; add a short
  "Development" section (pixi install, tasks, CI); link `examples/` and `AGENTS.md`;
  credit Luka Ludden as original author and name the maintainer.
- A `CHANGELOG.md` with a `0.2.0` entry (*builder's call*), whose contract changes, if any,
  match the PR's.

## Task-groups (suggested order)

Each group ends at a gate for Anthony's review. *Left to the builder* to regroup if the plan
shows a better seam.

1. **Packaging + CI + housekeeping** (Parts A, C, Housekeeping), still on whatever
   dataretrieval the lock resolves *before* raising the floor, so CI is proven green on the
   existing behaviour first. (`dataretrieval` unpinned would resolve 1.4; pin `<1.4`
   temporarily in this group, removed in group 3.)
2. **AGENTS.md + CLAUDE.md** (Part D, except the 1.4 gotcha, which group 3 adds).
3. **dataretrieval 1.4** (Part B): probe, code, tests, regenerated outputs, checklist; and
   the app key plumbing (Part B2), which needs no key to build or test.
4. **Examples** (Part E), written against the 1.4 code.
5. **Round end:** `pixi update`, final review, PR, Windows build to Paul.

## Left to the builder

Notebook titles and section order; whether to add a `live` CI job; classifier details; how to
structure the parity test; the exact checklist wording; any small refactor needed to make a
function callable from notebook 2, if it is behaviour-neutral and tested.
