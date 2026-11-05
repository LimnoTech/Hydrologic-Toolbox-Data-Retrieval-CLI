# dataretrieval 1.4 round: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the CLI to dataretrieval `>=1.4` (Water Data API v1) behind a reproducible pixi
build, three-OS CI and a Windows exe artifact, with an `AGENTS.md`, an optional embedded Water Data
app key, and two example notebooks, without changing the Toolbox contract unless Paul Duda signs
off.

**Architecture:** One `pyproject.toml` (hatchling + hatch-vcs, pixi features `core`/`dev`/
`jupyter`/`build`, one solve group) with a committed `pixi.lock`. Every dataretrieval call goes
through one new module, `waterdata_calls.py`, which owns warning handling and the v0-shape guard.
A second new module, `app_key.py`, opens the single `dataretrieval.configure(...)` block at the CLI
entry point. Everything else in `src/` changes only where the probe shows v1 data differs.

**Tech Stack:** Python 3.12 (pixi), dataretrieval 1.4, pandas, geopandas, pyproj, pyshp,
PyInstaller, pytest, ruff, pyrefly, jupytext, GitHub Actions with `prefix-dev/setup-pixi`.

**Spec:** `docs/superpowers/specs/2026-11-03-dataretrieval-1-4-examples-agents-design.md`
(approved 2026-11-05 at `8885be2`). Executors read the spec and this plan. Where they disagree,
the spec wins, except at the rulings listed under "Rulings this plan makes", which the plan's
reviewer approves together with the plan.

## Global Constraints

- Repo: `/Users/aaufdenkampe/Documents/git_Limno/Hydrologic-Toolbox-Data-Retrieval-CLI`. Public,
  MIT (`License.md`).
- **Toolbox contract:** the XML request shapes and the `<success>`/`<error>` response strings of
  `xml-compat`; each workflow's CSV layout (header lines, column names, column order, value
  formatting, date formatting); the shapefile file names, field names, field types and widths, and
  `.prj`. Any change to any of these is **breaking**: list it in the PR and `CHANGELOG.md`, and do not
  release until Paul Duda signs off.
- Agents commit on a branch; never push, merge, tag, publish a release, or work on `main`. Commit
  messages carry **no** AI co-author trailer, wrap at 72 characters and say *why*.
- New branches come from a **local** ref (no upstream). Run `git branch -vv` before every
  hand-back. A round branch must show no `[origin/...]`.
- Never change the checkout of `../../git_USGS_doi/dataretrieval-python`. Read other versions
  with `git -C <that repo> show <tag>:<path>`.
- Never link `limno-agent-skills` or `water-data-engine` from this repo as something a reader must
  follow. Naming them as where a rule came from, and saying they are private and LimnoTech's, is
  fine.
- The Water Data app key never appears in the repo, a log, CI output or a CLI output file. Users
  are never asked for a token. All of Part B2 works without the key.
- Probe and test targets: `02225500` (discharge), `324209082430201` (gw_daily),
  `410947071344803` (gw_periodic), bbox `-82.859 31.899 -82.013 32.947`. Keep live request counts
  small.
- dataretrieval floor: `>=1.4` in both dependency lists from group 3 on. Groups 1 and 2 pin
  `<1.4` in both.
- Python `3.12.*` in pixi `core`; `requires-python = ">=3.11"`.
- Ruff: `line-length = 88`, `extend-exclude = ["examples"]`, select
  `F, E, W, I, UP, B, Q, SIM, TID, C90, PLW1514` with `preview = true` and
  `explicit-preview-rules = true`, ignore `SIM105`, `SIM117` (dataretrieval's `main`, read
  2026-11-05).
- Assert exact values in tests (strings, file names, header lines), never shape.
- Ledger: `.agent-workspace/progress.md` in the primary checkout. Its first line names this plan.
- Never judge success through a pipe. Redirect to a file, `echo "EXIT=$?" >> file`, then read it.

## Review Focus

These are the inputs most likely to hurt a user that no test exercises unless this plan adds one.
Each line names the task that owns its test.

1. **`construction_date` at day, month or year precision** (`19890921`, `191904`, `1850`) must
   not change the periodic CSV header text or the shapefile `constructi` field from what v0.1.0
   wrote. Under 1.3 the reference wrote `1989-09-21`, width 10. Owner: Task 3.4.
2. **A v0-shaped metadata frame** (a `begin_utc` column) arriving through `xml-compat` must print
   exactly one `<error>...</error>` on stdout and exit 1. It must not print a traceback. The
   direct commands report it on stderr and exit 1. Owner: Task 3.3.
3. **The app key never leaks.** With a fake key embedded, `--debug`, `--debug-log`, `--version`,
   stdout and every written file contain no trace of it. Owner: Task 3.5.
4. **A dataretrieval warning other than the known date-format one** (1.4's
   `... could not be parsed as numbers ...`) must reach the `--debug` stream in `xml-compat` and
   stderr elsewhere. It must never reach stdout or be silently dropped. Owner: Task 3.3.
5. **An exe built without git metadata, or from a source ZIP,** must still answer `--version`
   (`0.0.0`) rather than crash at import. Owner: Task 1.2.

---

## Rulings this plan makes

Each ruling is the planner's decision, open to correction at plan review. Execution records each
one in the ledger with what it costs if wrong.

- **R1. Where the plan is committed.** On `docs/dataretrieval-1-4-spec`, beside the spec. The
  integration branch is cut from that tip at the start of group 1. *If wrong:* one cherry-pick.
- **R2. Branch names.** The integration branch is `round/dataretrieval-1-4`. Group branches are
  `dr14/g1-packaging-ci`, `dr14/g2-agents`, `dr14/g3-dataretrieval-1-4`, `dr14/g4-examples` and
  `dr14/g5-round-end`. They cannot sit under `round/dataretrieval-1-4/`, because git cannot hold a
  branch and a sub-path of it at once. Each group branches from local `round/dataretrieval-1-4`
  after Anthony has merged the previous group into it. *If wrong:* renames only.
- **R3. No worktrees.** Each group consumes the previous group's output (task names, the pyarrow
  ruling, the 1.4 code), so no two groups can run in parallel. Work happens in the primary
  checkout, and the ledger lives there.
- **R4. `configure` takes a `Configuration` object.** The spec writes
  `dataretrieval.configure(api_key=...)`. dataretrieval 1.4.0's signature is
  `configure(*configurations: BaseConfiguration)` (`dataretrieval/configuration.py:143` at
  `v1.4.0`), so the call is `dataretrieval.configure(dataretrieval.Configuration(api_key=key))`.
  The spec's intent is unchanged. *If wrong:* none; the spec's spelling raises a `TypeError`.
- **R5. `--version` prints the bare version.** It prints the version alone, e.g. `0.2.0` or
  `0.1.1.dev5+g1a2b3c4`, so the CI smoke test can compare it exactly with `_version.py`. The key
  state is reported only by `xml-compat --debug` (`Water Data app key: embedded` or `none`), and
  that is what the tag-build assertion reads. *If wrong:* adding a suffix later is a one-line
  change plus its test.
- **R6. Debug for direct commands.** `--debug` exists only on `xml-compat`. On `add-data` and
  `create-new-project`, a dataretrieval warning that is not filtered goes to stderr through
  Python's normal warning display. No new flags are added (non-goal: no new CLI features beyond
  `--version`). *If wrong:* a `--debug` flag on the other subcommands is a small follow-up.
- **R7. The v0 guard is a narrow `<error>`.** `xml-compat` turns only the new
  `WaterDataApiVersionError` into `<error>...</error>`. Other runtime exceptions keep today's
  behaviour, which is a traceback and a non-zero exit. Widening that is a contract change outside
  this round. *If wrong:* the README already claims "Failures return `<error>`". The gap is noted
  in the hand-back and in a `docs/upstream/`-style issue draft for Anthony to decide on.
- **R8. pyarrow on Windows needs Anthony's push.** Agents cannot run the Windows runner. Group 1
  adds a `workflow_dispatch` input `measure_pyarrow`. When it is set, `build-exe` builds a second
  bundle with `--exclude-module pyarrow` and writes both sizes and both `--help` timings to the job
  summary. The gate-1 hand-back carries macOS numbers, marked as indicative, and asks Anthony to
  push and dispatch. The ruling and its numbers go into the `pyproject.toml` comment and, in
  group 2, into AGENTS.md. If `pixi tree -i pyarrow` shows that pyarrow arrives transitively, the
  measurement is moot: declare pyarrow and record why.
- **R9. One `probe.out`, both versions through `pixi exec`.** The 1.3 run and the 1.4 run are
  written to `probe.out` one after the other, each section headed by `dataretrieval.__version__`.
  Both runs use throwaway `pixi exec --spec "dataretrieval==<v>.*"` environments, so the probe
  needs no manifest change, and the floor raise (Task 3.2) lands as its own commit right after.
- **R10. Ledger location.** `.agent-workspace/progress.md`. It is ignored through
  `.git/info/exclude` from the first step, so it is ignored on every branch, and through
  `.gitignore` from Task 1.2 on, so the convention is recorded in the repo.

## File structure

| Path | Group | Responsibility |
| --- | --- | --- |
| `pyproject.toml` | 1, 3 | Build, metadata, both dependency lists, pixi workspace and tasks, tool config |
| `pixi.lock` | 1, 3, 5 | Committed lock (generated; never hand-edited) |
| `.gitignore` | 1 | Lock and spec no longer ignored; `_version.py`, `_app_key.py`, `.agent-workspace/`, `examples/outputs/` ignored |
| `hydrologic_toolbox_data_retrieval_cli.spec` | 1, 3 | PyInstaller spec; adds `_version` and `_app_key` hidden imports and reads `HTDR_PYINSTALLER_EXCLUDES` |
| `src/.../__init__.py` | 1 | `__version__` from `_version.py`, falling back to `"0.0.0"` |
| `src/.../cli.py` | 1, 3 | `--version`; v0 error handling; key state in debug |
| `src/.../app.py` | 3 | Entry point opens the app-key configuration block |
| `src/.../waterdata_calls.py` (new) | 3 | `call_waterdata(...)`, warning routing, `check_time_series_metadata_shape(...)` |
| `src/.../app_key.py` (new) | 3 | `embedded_app_key()`, `app_key_state()`, `water_data_configuration(key)` |
| `src/.../timeseries.py`, `station_discovery.py` | 3 | Call through `waterdata_calls`; drop their private wrappers |
| `src/.../exports.py` | 3 | Only if the probe shows a contract-preserving fix is needed (Task 3.4) |
| `src/.../xml_compat.py` | 3 | Converts `WaterDataApiVersionError` into `<error>` |
| `scripts/write_app_key.py` (new) | 3 | Writes the git-ignored `_app_key.py` from `WATERDATA_APP_KEY`; prints only the state |
| `scripts/measure_bundle.py` (new) | 1 | Zips a PyInstaller folder, reports MB and best-of-five `--help` seconds |
| `tests/test_dependency_parity.py` (new) | 1 | Names and floors agree across the two lists |
| `tests/test_version.py` (new) | 1 | `--version` behaviour |
| `tests/test_waterdata_calls.py` (new) | 3 | Warning routing and the v0 guard |
| `tests/test_app_key.py` (new) | 3 | Both key states, no leaks, the writer script |
| `tests/fixtures/waterdata_v1/` (new) | 3 | Frames captured by the probe, as small CSV/JSON |
| `tests/test_v1_outputs.py` (new) | 3 | Exact header lines and file names from v1 fixtures |
| `.github/workflows/ci.yaml` (new) | 1, 3 | `test`, `typecheck`, `build-exe` jobs |
| `README.md`, `CHANGELOG.md` (new) | 1, 3 | Development section, credits, 0.2.0 entry |
| `AGENTS.md`, `CLAUDE.md` (new) | 2, 3 | Agent guidance; group 3 adds the 1.4 gotchas |
| `examples/sandbox/dataretrieval_1_4/` (new) | 3 | `probe.py`, `probe.out`, `log.md`, `regenerate_outputs.py`, `compare_outputs.py` |
| `docs/toolbox-test-checklist.md` (new) | 3 | Paul's test list |
| `examples/` notebooks, `reference_data/`, `README.md` (new) | 4 | Part E |

`src/...` means `src/hydrologic_toolbox_data_retrieval_cli/`.

---

## Gate procedure (every group ends with this)

- [ ] Run the full verification for the group (each task lists it) and record the exit codes in
  the ledger.
- [ ] Final review of the group's diff (`git diff round/dataretrieval-1-4...HEAD > .agent-workspace/g<N>.diff`)
  on two axes, spec and quality. Then one fix wave and a scoped re-review. **Fix every finding,
  Minor ones included**, before handing back.
- [ ] `git branch -vv`. The group branch shows no upstream.
- [ ] `git status --short --ignored -- .agent-workspace examples dist` shows nothing stranded.
- [ ] Hand back:
  - a summary that carries the evidence;
  - every ruling made during the group, each with what it costs if wrong;
  - a PR title on its own line, then a description in a `~~~markdown` fence, written for GitHub
    reviewers with no hard wraps. It targets `round/dataretrieval-1-4`, except in group 5, which
    targets `main`;
  - a recommendation to `/clear`, with a continuation prompt that names the repo, this plan, the
    ledger, the branch just handed back and the next group.
- [ ] Stop. Anthony merges the group into `round/dataretrieval-1-4` before the next group
  branches.

---

## Group 1: Packaging, CI and housekeeping

Branch: `dr14/g1-packaging-ci` from local `round/dataretrieval-1-4`. dataretrieval is pinned
`<1.4` in both lists for this group.

### Task 1.1: Round setup and housekeeping deletions

**Files:**

- Create: `.agent-workspace/progress.md` (ignored)
- Delete: `docs/superpowers/specs/tests/test_cli_repo_boundary.py`, `test_packaging_config.py`, `test_usgs_waterdata_demo.py`

- [ ] **Step 1:** `git switch docs/dataretrieval-1-4-spec`, then
  `git switch -c round/dataretrieval-1-4`, then `git switch -c dr14/g1-packaging-ci`. Run
  `git branch -vv`: neither new branch shows `[origin/...]`.
- [ ] **Step 2:** `echo '/.agent-workspace/' >> .git/info/exclude`. Create the ledger with the
  first line `Ledger for docs/superpowers/plans/2026-11-05-dataretrieval-1-4-round.md`, then the
  preflight scan required by the workflow. Grep that every symbol this plan names exists or is
  created by a named task: `_INFER_FORMAT_WARNING_PATTERN`,
  `_call_waterdata_with_filtered_datetime_warning`,
  `_call_station_discovery_with_filtered_datetime_warning`, `_infer_shapefile_field_spec`,
  `_STATION_SHAPEFILE_CROSSWALK`, `handle_xml_request`, `_error_xml`, `build_parser`, `main`.
  Record R1–R10.
- [ ] **Step 3:** `git rm -r docs/superpowers/specs/tests/`. Commit:
  `Remove spec tests that import the pre-rename package`.

### Task 1.2: pyproject.toml, lock, .gitignore, `__version__` and `--version`

**Files:**

- Modify: `pyproject.toml` (full rewrite to the pattern), `.gitignore`, `src/.../__init__.py`, `src/.../cli.py`, `hydrologic_toolbox_data_retrieval_cli.spec`
- Create: `pixi.lock`, `tests/test_dependency_parity.py`, `tests/test_version.py`

**Interfaces:**

- Produces: pixi tasks `test`, `test-live`, `lint`, `format`, `typecheck`, `build-exe`, `cli`;
  environments `default`, `ci`, `build`; `hydrologic_toolbox_data_retrieval_cli.__version__: str`;
  top-level `--version` flag.

- [ ] **Step 1: Write `tests/test_dependency_parity.py`.** Copy ras2xugrid's
  `tests/test_dependency_parity.py` (it is self-contained) and adapt it:
  - `FEATURE_TO_EXTRA = {"core": None, "jupyter": "jupyter"}`, with `dev` and `build` excluded and
    a comment saying why.
  - `CONDA_ONLY = {"python"}`, plus `sqlite` only if core declares it.
  - `CONDA_TO_PYPI = {"matplotlib-base": "matplotlib"}`. pyshp is `pyshp` on both sides; confirm
    with `pixi search pyshp`.
  - Add `test_bounds_match`, which the spec requires ("names or floors"). It needs a helper,
    `bounds(spec: str) -> tuple[str | None, str | None]`, that extracts the `>=X` and `<Y` versions
    from a PEP 508 or conda specifier. For every package in both lists of a feature/extra pair,
    the PyPI and conda bounds must be equal. On failure, the message gives the package and both
    raw specifiers. Add a unit test for the helper:
    `bounds(">=1.3,<1.4") == ("1.3", "1.4")`, `bounds("*") == (None, None)`,
    `bounds(">=1.4") == ("1.4", None)`.
- [ ] **Step 2: Write `tests/test_version.py`.**
  - `test_version_flag_prints_package_version`: run `[sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", "--version"]`. Assert `returncode == 0` and `stdout == f"{hydrologic_toolbox_data_retrieval_cli.__version__}\n"`.
  - `test_version_falls_back_without_version_module`: monkeypatch `sys.modules["hydrologic_toolbox_data_retrieval_cli._version"] = None`, reload the package, and assert `__version__ == "0.0.0"` (Review Focus 5). Restore it with `importlib.reload` in a `finally`.
- [ ] **Step 3: Run both tests and confirm they fail.** Use `pixi run pytest tests/test_dependency_parity.py tests/test_version.py`. The current manifest has no `core` feature, so the expected result is FAIL or ERROR.
- [ ] **Step 4: Rewrite `pyproject.toml`** following ras2xugrid's layout and spec Part A.
  - Build: hatchling + hatch-vcs; `dynamic = ["version"]`; `fallback-version = "0.0.0"`;
    version-file `src/hydrologic_toolbox_data_retrieval_cli/_version.py`; wheel packages
    `["src/hydrologic_toolbox_data_retrieval_cli"]`. Keep `[project.scripts]` unchanged.
  - Metadata: `license = "MIT"`, `license-files = ["License.md"]`. `authors` are LimnoTech, Luka
    Ludden and Anthony Aufdenkampe (`aaufdenkampe@limno.com`); `maintainers` is Anthony
    Aufdenkampe. Add `[project.urls]` for `https://github.com/LimnoTech/Hydrologic-Toolbox-Data-Retrieval-CLI`
    (Homepage, Repository, `/issues`). Keywords: `usgs`, `water-data`, `hydrology`,
    `hydrologic-toolbox`, `dataretrieval`, `shapefile`. Classifiers follow ras2xugrid, with
    Python 3.11 and 3.12, `Operating System :: Microsoft :: Windows`,
    `Operating System :: OS Independent`, `Environment :: Console`, and no `License ::`
    classifier.
  - Dependencies, PyPI side: `dataretrieval>=1.3,<1.4`, `geopandas`, `pandas`, `pyproj`,
    `pyshp`. Add `pyarrow` only per R8. Put the comment
    `# <1.4 is temporary: group 3 of the 1.4 round raises it to >=1.4` on the dataretrieval line.
    Add an extra `jupyter = ["jupyterlab", "jupytext", "matplotlib", "ipykernel"]`. Remove the old
    `build` extra, because PyInstaller lives in the pixi `build` feature only.
  - Pixi: channels `["conda-forge", "nodefaults"]`; platforms `["linux-64", "osx-arm64", "win-64"]`;
    the editable self-install in `[tool.pixi.pypi-dependencies]`.
    - `core`: `python = "3.12.*"`, `dataretrieval = ">=1.3,<1.4"`, `geopandas`, `pandas`,
      `pyproj`, `pyshp`.
    - `dev`: `pytest`, `ruff`, `pyrefly`.
    - `jupyter`: `jupyterlab`, `jupytext`, `matplotlib-base`, `ipykernel`.
    - `build`: `pyinstaller`, with the `build-exe` task defined on this feature
      (`[tool.pixi.feature.build.tasks]`), so it exists only in the `build` environment.
    - Environments: `default = core+dev+jupyter`, `ci = core+dev`, `build = core+build`, all in
      `solve-group = "default"`.
  - Tasks:
    - `test = "pytest"`
    - `test-live = "pytest -m live"`
    - `lint = "ruff check"` and `format = "ruff format"`. These take no paths: the config's
      `extend-exclude` decides scope, so `scripts/` is covered once it exists.
    - `typecheck = "pyrefly check"`
    - `build-exe = "pyinstaller --noconfirm --clean hydrologic_toolbox_data_retrieval_cli.spec"`,
      on the `build` feature. README and CI spell it `pixi run -e build build-exe`.
    - `cli = "python -m hydrologic_toolbox_data_retrieval_cli"`
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-ra -m 'not live'"`, the
    existing `live` marker text. `[tool.pyrefly] project-includes = ["src/hydrologic_toolbox_data_retrieval_cli"]`,
    `python-version = "3.12"`. `[tool.jupytext] formats = "ipynb,py:percent"`. The ruff block
    lands in Task 1.3.
- [ ] **Step 5: Edit `.gitignore`.** Delete the lines `pixi.lock` (twice), `pixi.toml`, the three
  `sandbox/...` lines, `/sandbox/outputs` and `*.spec`. Add `src/hydrologic_toolbox_data_retrieval_cli/_version.py`,
  `src/hydrologic_toolbox_data_retrieval_cli/_app_key.py`, `/.agent-workspace/` and
  `examples/outputs/`. Leave the `dist/*` / `!dist/outputs/` block as it is. Verify:
  `git check-ignore -v .pixi/x build/x src/hydrologic_toolbox_data_retrieval_cli/_version.py src/hydrologic_toolbox_data_retrieval_cli/_app_key.py` matches all four paths, and
  `git check-ignore pixi.lock hydrologic_toolbox_data_retrieval_cli.spec dist/outputs/add_data_discharge/discharge_02225500.csv` prints nothing (exit 1).
- [ ] **Step 6: Implement `__version__` and `--version`.**
  - `__init__.py`: `try: from hydrologic_toolbox_data_retrieval_cli._version import __version__` /
    `except ImportError: __version__ = "0.0.0"`.
  - `cli.build_parser()`: add
    `parser.add_argument("--version", action="version", version=__version__)`. argparse prints
    `version` followed by a newline to stdout and exits 0. Confirm that the
    no-subcommand-with-`--version` path works, because subparsers are `required=True` and argparse
    handles `--version` before that check.
  - Spec file: add `'hydrologic_toolbox_data_retrieval_cli._version'` to `hiddenimports`. Add
    `excludes=[m for m in os.environ.get('HTDR_PYINSTALLER_EXCLUDES', '').split(',') if m]`, with
    `import os` at the top (used by R8).
- [ ] **Step 7: Lock and install.** Run `pixi lock`, `pixi install --all` and
  `pixi install --locked`. Then run `grep '^\s*- pypi:' pixi.lock | sort -u > .agent-workspace/pypi.txt; echo "EXIT=$?" >> .agent-workspace/pypi.txt`.
  Only `./` may appear. Run `pixi tree -e default -i pyarrow` and record the output in the ledger
  for R8. Run `pixi list -e default dataretrieval` and record that it is 1.3.x.
- [ ] **Step 8: Run the tests.** `pixi run test > .agent-workspace/t.txt 2>&1; echo "EXIT=$?" >> .agent-workspace/t.txt`.
  Every offline test passes, including the new ones. Record the collected count.
- [ ] **Step 9: Commit.** Stage `pyproject.toml`, `pixi.lock`, `.gitignore`, the spec file,
  `__init__.py`, `cli.py` and the two tests. Message:
  `Adopt the hatch-vcs + pixi packaging pattern and commit the lock`.

### Task 1.3: Ruff and pyrefly configuration and baseline

**Files:**

- Modify: `pyproject.toml` (`[tool.ruff]`, `[tool.ruff.lint]`), then whatever ruff touches in `src/` and `tests/`

- [ ] **Step 1: Add the ruff config** with exactly the values in Global Constraints. The
  mccabe threshold is ruff's default, so set no `max-complexity`. Run
  `pixi run ruff check --statistics > .agent-workspace/ruff0.txt 2>&1; echo "EXIT=$?" >> .agent-workspace/ruff0.txt`,
  then the same with `--select TC001,BLE001,ARG001,D100,D101,D102,D103,D104` into `ruff_extra.txt`.
  Adopt any extra rule whose count is ≤ 5 and whose fixes are not behaviour-changing. Record the
  counts and the ruling in the ledger.
- [ ] **Step 2: Reformat commit, alone.** `pixi run format`, then run `pixi run test`
  and expect PASS. Commit only the formatter's changes:
  `Reformat with ruff format (line length 88); no other change`.
- [ ] **Step 3: Lint fixes.** Run `pixi run ruff check --fix` for safe fixes only, never
  `--unsafe-fixes`. Read each remaining finding. Fix it if the fix is provably behaviour-neutral;
  otherwise add `# noqa: <code>  <reason>`. Any finding that would change runtime behaviour gets a
  `noqa`. `PLW1514` fixes, which add `encoding="utf-8"`, *do* change behaviour on Windows. List
  each one in the ledger for review; do not apply any blindly. Then check the result:
  `python3 ../limno-agent-skills/skills/packaging/annotation_only.py HEAD`. A non-annotation diff is
  expected only where a fix was deliberate and is listed. `pixi run lint` exits 0, and
  `pixi run ruff format --check` exits 0.
- [ ] **Step 4: Type check.** Run `pixi run typecheck > .agent-workspace/pyrefly.txt 2>&1; echo "EXIT=$?" >> ...`.
  If it fails, run `pixi run pyrefly suppress` and commit the result separately with the count in
  the message. No logic changes are allowed in this step.
- [ ] **Step 5:** `pixi run test` passes. Commit the lint fixes:
  `Apply ruff lint baseline; suppress behaviour-changing findings`.

### Task 1.4: CI workflow and bundle measurement

**Files:**

- Create: `.github/workflows/ci.yaml`, `scripts/measure_bundle.py`, `tests/test_measure_bundle.py`

**Interfaces:**

- Produces: `scripts/measure_bundle.py <bundle_dir> <exe_path> [--label TEXT]`. It prints one
  Markdown table row, `| <label> | <zip MB, 1 dp> | <best-of-5 --help s, 2 dp> |`, exits non-zero
  if the exe's `--help` fails, and writes the zip next to `<bundle_dir>` as
  `<bundle_dir name>.zip`.

- [ ] **Step 1: Write a test for the script's pure parts.** In `tests/test_measure_bundle.py`,
  `test_format_row` asserts `format_row("with pyarrow", 41.26, 1.234) == "| with pyarrow | 41.3 | 1.23 |"`.
  Import the script through `importlib.util.spec_from_file_location`.
- [ ] **Step 2: Implement `scripts/measure_bundle.py`** with
  `format_row(label: str, zip_mb: float, seconds: float) -> str`,
  `zip_bundle(bundle_dir: Path) -> Path` (`shutil.make_archive`), and
  `best_help_time(exe: Path, runs: int = 5) -> float` (`time.perf_counter` around
  `subprocess.run([exe, "--help"], check=True, capture_output=True)`). Run the test and expect
  PASS.
- [ ] **Step 3: Write `ci.yaml`** by adapting ras2xugrid's file.
  - Keep the header comment block, rewritten for this repo, plus `permissions: contents: read`,
    the `concurrency` block and the trigger policy (`push` with `paths-ignore` `**.md` and
    `.gitignore`; `pull_request` into `main`; `workflow_dispatch`). Add `push: tags: ["v*"]`.
    Add a `workflow_dispatch` input `measure_pyarrow` (boolean, default `false`).
  - Drop the `notebook` job and everything about water-data-engine.
  - `test` job: matrix expression as in ras2xugrid. `actions/checkout@v4` with `fetch-depth: 0`.
    `prefix-dev/setup-pixi@v0` with `environments: ci`, `locked: true`, `cache: true`, keeping the
    comment on the plural input. Steps: Tests (`PYTHONFAULTHANDLER: "1"`,
    `pixi run -e ci test`, `exit $LASTEXITCODE`), Lint (`pixi run -e ci lint`), Format
    (`pixi run -e ci ruff format --check`).
  - `typecheck` job: as in ras2xugrid.
  - `build-exe` job: `runs-on: windows-latest`, with
    `if: github.event_name != 'push' || startsWith(github.ref, 'refs/tags/v')`.
    `permissions: contents: write`, set on this job only. `defaults: run: shell: pwsh`. Steps:
    1. Checkout with `fetch-depth: 0`.
    2. setup-pixi with `environments: build`, locked, cache.
    3. `pixi run -e build build-exe`.
    4. Smoke test, in PowerShell:
       - `--help` has exit 0.
       - `--version` output, trimmed, `-ceq` the `__version__` that
         `pixi run -e build python -c "from hydrologic_toolbox_data_retrieval_cli._version import __version__; print(__version__)"` prints.
       - On `refs/tags/v*`, the version also equals the tag name minus `v`.
       - `xml-compat --xml "<function"` gives exit 1, and stdout, trimmed, matches
         `^<error>.*</error>$` with exactly one line.

       Each check throws on failure.
    5. `python scripts/measure_bundle.py dist\hydrologic_toolbox_data_retrieval_cli dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe --label "as built"` run through `pixi run -e build`, appended to `$env:GITHUB_STEP_SUMMARY` under a header row.
    6. If `inputs.measure_pyarrow`: copy the zip aside, rebuild with
       `$env:HTDR_PYINSTALLER_EXCLUDES = "pyarrow"`, measure with `--label "pyarrow excluded"`, and
       restore the first build's zip for upload.
    7. `actions/upload-artifact@v4`, name `hydrologic_toolbox_data_retrieval_cli-${{ github.sha }}`,
       path the zip.
    8. On a `v*` tag: `gh release create "$env:GITHUB_REF_NAME" <zip> --draft --title ... --notes "Draft: publish after Paul Duda has tested this build in the Hydrologic Toolbox."`
       with `GH_TOKEN: ${{ github.token }}`. Add a comment saying this step is untested until the
       first tag.

    Group 3 adds the app-key steps (Task 3.5).
- [ ] **Step 4: Validate locally.** `pixi exec --spec actionlint actionlint .github/workflows/ci.yaml`
  exits 0. Build locally on macOS with `pixi run -e build build-exe`, then run
  `pixi run -e build python scripts/measure_bundle.py ...` with and without
  `HTDR_PYINSTALLER_EXCLUDES=pyarrow`. Record both rows in the ledger, marked
  `macOS arm64, indicative only`. The macOS exe also passes the three smoke checks, run by hand.
- [ ] **Step 5: Commit.** Stage the workflow, the script and its test. Message:
  `Add CI: tests on push, three OSes before main, Windows exe build`.

### Task 1.5: README and CHANGELOG

**Files:**

- Modify: `README.md`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Update `README.md`.**
  - Replace the "Build From Source" body with `pixi install`, `pixi run -e build build-exe`, and a
    note that CI builds the same artifact on every PR into `main`.
  - Add a "Development" section: install pixi, `pixi install`, the task table (`test`,
    `test-live`, `lint`, `format`, `typecheck`, `build-exe`, `cli`), and a sentence on what CI
    runs.
  - Add "Run without the exe (macOS/Linux)": `pixi run cli -- --help`.
  - Add a "Credits" section: Luka Ludden, original author (LimnoTech); maintained by Anthony
    Aufdenkampe (LimnoTech).
  - Add links to `AGENTS.md` and `examples/`. Mark them *(added in this round)* only in the PR,
    not in the README. Both files are dangling until groups 2 and 4; list that in the gate
    hand-back as owned by those groups.
  - Write README commands for the shell they run in, and say which shell that is.
- [ ] **Step 2: Create `CHANGELOG.md`** in Keep a Changelog style, with an `## [Unreleased]`
  section (to become `0.2.0` in group 5) under Added, Changed and Removed. Add a
  `### Breaking (Toolbox contract)` subsection reading `None so far.`; group 3 updates it.
- [ ] **Step 3: Commit.** Message: `Document pixi development workflow; credit original author`.
- [ ] **Step 4: Run the gate procedure.** The hand-back also carries:
  - the pyarrow numbers (macOS), with a request to push `dr14/g1-packaging-ci` and run the
    workflow from the Actions tab with `measure_pyarrow` ticked;
  - the planner's recommendation rule from spec A.4;
  - a note that CI has not run yet.

  **Gate 1 has two parts.** After Anthony reports the Windows numbers and rules, one small commit
  records the ruling in the `pyproject.toml` comment, adding or exempting `pyarrow` in both lists.
  Re-lock if needed. That commit is reviewed by the controller and handed back.

---

## Group 2: AGENTS.md and CLAUDE.md

Branch: `dr14/g2-agents` from local `round/dataretrieval-1-4`, after group 1 is merged into it.

### Task 2.1: Write AGENTS.md and CLAUDE.md

**Files:**

- Create: `AGENTS.md`, `CLAUDE.md`

- [ ] **Step 1: Create `CLAUDE.md`** containing exactly `@AGENTS.md\n`.
- [ ] **Step 2: Write `AGENTS.md`** with spec Part D's eight sections, in that order. Most of the
  content is condensed from `../limno-agent-skills/agent-workflow.md`, read in full in this
  session. Rewrite it in this repo's terms; do not copy the private file's anecdotes about other
  repos unless a one-line reason needs one.
  - Open with a pointer to README for what the project is.
  - Name "LimnoTech's internal agent-workflow guide (private)" **once** as the origin of the
    process rules, with no link.
  - Guardrails: everything in spec D.1, with the pyarrow ruling and its numbers copied from the
    ledger and the commands that produced them. Name the Toolbox contract word for word as in
    Global Constraints, and name Paul Duda.
  - Section 4 carries the lock/update/upgrade table from the workflow guide, minus the
    water-data-engine link.
  - Section 5 lists exact task names: `pixi run test`, `pixi run -e ci test`, `pixi run lint`,
    `pixi run format`, `pixi run typecheck`, `pixi run test-live`,
    `pixi run -e build build-exe`, `pixi run cli -- ...`, and headless notebook execution:
    `pixi run jupyter nbconvert --to notebook --execute --inplace examples/<name>.ipynb`, then
    `pixi run jupytext --sync examples/<name>.py`. Include the no-PyPI-fallback `grep` and its
    PowerShell form.
  - Section 8: gotchas with provenance. `PowerShell --% for inline XML` is *learned here*. Add
    anything group 1 hit with PyInstaller (from the ledger), *learned here*. Leave a
    `### dataretrieval 1.4` heading reading `Filled by the 1.4 round's group 3.` That is the one
    placeholder this plan allows: group 3 owns it by ruling, and the hand-back says so.
  - Aim near ras2xugrid's length for the local part. Hard-wrap at 100 characters, as the sibling
    repos' committed markdown is.
- [ ] **Step 3: Verify by re-measurement, not by reading.** Every task name in AGENTS.md runs:
  execute each `pixi run` line once (all except `test-live` and `build-exe`, which are
  `--help`/dry-checked). Every file path it names exists (`grep -o` the backticked paths and
  `test -e` each one). `grep -n "limno-agent-skills\|water-data-engine" AGENTS.md` shows only
  "named as origin" lines, with no URL.
- [ ] **Step 4: Commit.** Message: `Add AGENTS.md and the CLAUDE.md stub`. Then run the gate
  procedure. The review checks every claim against the repo, not against this brief.

---

## Group 3: dataretrieval 1.4 and the app key

Branch: `dr14/g3-dataretrieval-1-4` from local `round/dataretrieval-1-4`.

### Task 3.1: Probe 1.3 against 1.4

**Files:**

- Create: `examples/sandbox/dataretrieval_1_4/probe.py`, `probe.out`, `log.md`

- [ ] **Step 1: Write `probe.py`.** It is standalone: it imports `dataretrieval.waterdata` and
  pandas only, and never imports the package, so it runs under `pixi exec`. It first prints
  `dataretrieval.__version__`. Then, for each call the CLI makes, it uses the exact kwargs from
  `timeseries.py` and `station_discovery.py`:
  - `get_daily` × 2 stations, date range `2024-01-01/2024-01-10` to keep requests small;
  - `get_field_measurements(410947071344803)`, full range;
  - `get_time_series_metadata` per station, and with the bbox for both `parameter_code="00060"`
    and unfiltered;
  - `get_monitoring_locations` per station, and with the bbox for `ST` and `GW`;
  - `get_field_measurements` with the bbox.

  For each frame it prints the column list, dtypes, row count, the first two rows, and any
  warnings caught (`warnings.catch_warnings(record=True)` with `simplefilter("always")`), giving
  each warning's category and message. For monitoring locations it also prints the
  `construction_date` values and their `len()` histogram. Last, under 1.4 only: a call inside
  `dataretrieval.configure(waterdata.WaterdataConfiguration(api_version="v0"))` for
  `get_time_series_metadata(02225500)`, printing whether `begin_utc` is present, or the exception
  if v0 no longer answers.

  The script saves the frames the tests need as fixtures (Task 3.4) under
  `tests/fixtures/waterdata_v1/` when run with `--save-fixtures`: CSV via
  `to_csv(index=False)`, geometry as WKT, at most 20 rows each.
- [ ] **Step 2: Run it.** In zsh, from the repo root:
  `{ for v in 1.3 1.4; do pixi exec --spec "dataretrieval==${v}.*" --spec geopandas -- python examples/sandbox/dataretrieval_1_4/probe.py; done; } > examples/sandbox/dataretrieval_1_4/probe.out 2>&1; echo "EXIT=$?"`.
  Both versions run in throwaway `pixi exec` environments, so the manifest is untouched. Read
  `probe.out` and confirm that each section's version line shows 1.3.x and then 1.4.x.
- [ ] **Step 3: Write `log.md`** in water-data-engine's log style: why, then a dated
  `## 2026-11-…` section. Check every bullet of spec Part B's "What water-data-engine found",
  column by column, citing `probe.out`, and add anything else the probe shows. For each finding,
  name the CLI output it reaches (which CSV header key, which shapefile field, or none).
- [ ] **Step 4: Commit.** Message: `Probe dataretrieval 1.3 vs 1.4 against the CLI's calls`.

### Task 3.2: Raise the floor to dataretrieval 1.4

**Files:**

- Modify: `pyproject.toml`, `pixi.lock`

- [ ] **Step 1: Edit both lists.** Change `dataretrieval>=1.3,<1.4` to `dataretrieval>=1.4` on the
  PyPI side and `">=1.4"` on the conda side, and delete the temporary comment. Then run
  `pixi update dataretrieval` (not `pixi lock`: see AGENTS.md § lock/update/upgrade) and
  `pixi install --locked`.
- [ ] **Step 2: Verify.** `pixi list -e default dataretrieval` and `pixi list -e ci dataretrieval`
  both show 1.4.x. `pixi run test` passes, including the parity bounds. The existing offline tests
  use fake modules and are expected to pass unchanged; a failure here is fixed in this task and
  recorded in the ledger. Run the no-PyPI-fallback grep.
- [ ] **Step 3: Commit.** Message: `Require dataretrieval 1.4 (Water Data API v1)`. This comes
  before 3.3–3.5 because Task 3.5 calls `dataretrieval.configure`, which 1.3 lacks.

### Task 3.3: `waterdata_calls`: one call path, warning routing, v0 guard

**Files:**

- Create: `src/.../waterdata_calls.py`, `tests/test_waterdata_calls.py`
- Modify: `src/.../timeseries.py`, `src/.../station_discovery.py`, `src/.../xml_compat.py`, `src/.../cli.py`

**Interfaces:**

- Produces:
  - `class WaterDataApiVersionError(ValueError)`.
  - `call_waterdata(function: Callable[..., T], *, debug_logger: Callable[[str], None] | None = None, **kwargs) -> T`.
    It calls `function(**kwargs)` inside `warnings.catch_warnings(record=True)` with
    `simplefilter("always")`. It drops warnings matching `_INFER_FORMAT_WARNING_PATTERN`, but only
    if the probe shows 1.4 still emits them; otherwise the pattern and the filter are deleted. It
    re-emits every other warning: with a `debug_logger`, as
    `debug_logger(f"dataretrieval warning: {category.__name__}: {message}")`; without one, through
    `warnings.warn_explicit` with the original category, filename and line number.
  - `check_time_series_metadata_shape(frame: pd.DataFrame) -> None`. If `"begin_utc"` is in
    `frame.columns`, it raises `WaterDataApiVersionError(_V0_MESSAGE)`.
  - `_V0_MESSAGE = "dataretrieval returned Water Data API v0 time-series metadata (begin_utc is present); this CLI requires v1. Remove api_version=\"v0\" from the dataretrieval configuration."`
- Consumes: nothing new.

- [ ] **Step 1: Write failing tests in `tests/test_waterdata_calls.py`.**
  - `test_call_waterdata_routes_unknown_warning_to_debug_logger`: a fake function warns
    `UserWarning("1 value in column 'value' could not be parsed as numbers and were set to missing. To inspect the raw values, repeat the call with convert_type=False.")`
    and returns `"ok"`. Assert the return is `"ok"` and that the logged messages equal
    `["dataretrieval warning: UserWarning: 1 value in column 'value' could not be parsed as numbers and were set to missing. To inspect the raw values, repeat the call with convert_type=False."]`.
  - `test_call_waterdata_reemits_unknown_warning_without_logger`: use `pytest.warns(UserWarning, match="could not be parsed as numbers")`.
  - `test_call_waterdata_drops_infer_format_warning`: only if kept. The fake warns
    `"Could not infer format, so each element will be parsed individually, falling back to dateutil."`.
    Assert no warning escapes (`warnings.catch_warnings(record=True)`, `len == 0`) and nothing is
    logged.
  - `test_check_shape_raises_on_begin_utc`: `pd.DataFrame({"begin_utc": [], "time_series_id": []})`
    raises `WaterDataApiVersionError`, and `str(exc) == _V0_MESSAGE`.
  - `test_check_shape_accepts_v1`: a frame with the v1 columns from the probe raises nothing.
  - Shared fixture `fake_waterdata(monkeypatch)`: it `monkeypatch.setattr`s the four functions
    (`get_daily`, `get_time_series_metadata`, `get_monitoring_locations`,
    `get_field_measurements`) on the real `dataretrieval.waterdata` module. Every entry point
    resolves that module at call time, so `xml-compat`, `add-data` and `create-new-project` all
    see the fakes with no `src/` change. Put it in `tests/conftest.py`; Tasks 3.4 and 3.5 reuse
    it, parametrized by the frames to return.
  - `test_xml_compat_v0_metadata_returns_single_error_line` (Review Focus 2): with
    `fake_waterdata`, `get_time_series_metadata` returns a frame with `begin_utc`. Call
    `cli.run_cli(["xml-compat", "--xml", <discharge add-data XML with SaveIn=tmp_path>])` with
    `capsys`. Assert the return is `1` and that
    `capsys.readouterr().out == f"<error>{_V0_MESSAGE}</error>\n"`.
  - `test_add_data_v0_metadata_reports_on_stderr`: same fake, `run_cli(["add-data", "discharge", "--output-dir", str(tmp_path)])`
    returns `1`, stdout is `""`, and stderr is `f"error: {_V0_MESSAGE}\n"`.
  - `test_station_discovery_gw_daily_checks_shape`: `_get_station_discovery_frames(bbox, "gw_daily", fake)`
    with v0-shaped metadata raises `WaterDataApiVersionError`. Station discovery reads metadata by
    bbox, so it is an entry point too.
- [ ] **Step 2: Run the tests and confirm they fail.** `pixi run pytest tests/test_waterdata_calls.py -v`
  fails with an ImportError on `waterdata_calls`.
- [ ] **Step 3: Implement.**
  - Create `waterdata_calls.py` per the Interfaces block.
  - `timeseries.py` and `station_discovery.py`: delete `_INFER_FORMAT_WARNING_PATTERN` and both
    private wrappers. Route every `waterdata_module.*` call through `call_waterdata(..., debug_logger=debug_logger)`;
    station discovery passes `None`. Call `check_time_series_metadata_shape` on every frame
    returned by `get_time_series_metadata`.
  - `xml_compat.handle_xml_request`: wrap the request loop in
    `except WaterDataApiVersionError as exc: _debug(...); return _error_xml(str(exc))`.
  - `cli.run_cli`: for `create-new-project` and `add-data`, use
    `except WaterDataApiVersionError as exc: print(f"error: {exc}", file=sys.stderr); return 1`.
  - Update existing tests that patched the deleted wrappers, if any (grep first).
- [ ] **Step 4: Run the tests.** `pixi run test` passes and `pixi run lint` passes.
- [ ] **Step 5: Commit.** Message:
  `Route dataretrieval calls through one module; refuse v0 metadata`.

### Task 3.4: Make v1 outputs match the contract, pinned by fixture tests

**Files:**

- Create: `tests/fixtures/waterdata_v1/*.csv`, `tests/test_v1_outputs.py`
- Modify: `src/.../timeseries.py` and/or `src/.../exports.py`, only as the probe requires

- [ ] **Step 1: Save the fixtures.** `pixi run python examples/sandbox/dataretrieval_1_4/probe.py --save-fixtures`
  (1.4). Commit only the fixture files the tests below read.
- [ ] **Step 2: Write failing tests in `tests/test_v1_outputs.py`.** Each test builds a fake
  `waterdata_module` whose four functions return the fixture frames, read back with the 1.4 dtypes
  the probe recorded (state those dtypes explicitly in the loader). It then runs the package's
  public functions into `tmp_path`.
  - `test_discharge_csv_header_and_name`: `get_usgs_timeseries("02225500", "discharge", tmp_path, ...)`
    writes `tmp_path / "discharge_02225500.csv"`. Its first three lines equal those of
    `dist/outputs/add_data_discharge/discharge_02225500.csv` (lines 1 and 3 exactly; line 2
    exactly, except fields the log shows changed at source, each listed in the test with a
    comment), and the first body row reads `<date>,<value>,Approved,`, with the value formatted as
    in the reference (`1740.0` style).
  - `test_gw_daily_csv_header_and_name`: the same for `gw_daily_324209082430201.csv`.
  - `test_periodic_csv_header_construction_date` (Review Focus 1): line 2's `construction_date`
    field is exactly `1989-09-21`, and line 3 (the body column names) equals the reference's
    line 3.
  - `test_construction_date_precisions`: parametrized over `("19890921", "1989-09-21")`,
    `("191904", <what 1.3 wrote for this value, from probe.out>)` and
    `("1850", <what 1.3 wrote, from probe.out>)`. Assert the periodic header value and the
    shapefile `constructi` field value and width. If 1.3 could not represent month or year
    precision, the expected value comes from a ruling recorded in the log and listed as a
    contract question for Paul.
  - `test_station_shapefile_fields_match_reference`: run `run_create_new_project_section(bbox, ["gw_periodic"], tmp_path, waterdata_module=fake)`.
    The field names and types in its `shapefile.Reader(...).fields` equal those of
    `dist/outputs/create_new_project_periodic_bbox/periodic.shp`, in order. `constructi` is
    `("C", 10)`. Other widths are data-driven (`_infer_shapefile_field_spec`) and not asserted
    against a 20-row fixture; Task 3.6 compares them on full data.
- [ ] **Step 3: Run the tests.** Expect FAIL wherever v1 data change output.
- [ ] **Step 4: Fix at the producer.**
  - **`construction_date`:** normalize the raw string at the point it leaves the monitoring-location
    frame, in one helper `_format_construction_date(value: object) -> object` in `timeseries.py`
    (exported for `exports.py`, or placed in `frame_types.py` if both modules need it). It maps
    8-digit → `YYYY-MM-DD` and handles 6 and 4 digits per the ruling above, and passes anything
    else through unchanged. Apply it in both places, the periodic header and the station frame
    before the shapefile spec is inferred, and nowhere else.
  - Do the same for any other column the log flags.
  - If a difference cannot be removed without inventing data, **do not fix it silently**. Record
    it as breaking: `CHANGELOG.md` → Breaking, and the checklist in Task 3.7.
- [ ] **Step 5: Run the tests.** `pixi run test` passes.
- [ ] **Step 6: Commit.** Message: `Keep v1 outputs in the v0.1.0 layout; pin with fixture tests`.

### Task 3.5: Water Data app key (Part B2)

**Files:**

- Create: `src/.../app_key.py`, `scripts/write_app_key.py`, `tests/test_app_key.py`
- Modify: `src/.../app.py`, `src/.../cli.py`, `hydrologic_toolbox_data_retrieval_cli.spec`, `.github/workflows/ci.yaml`

**Interfaces:**

- Produces, in `app_key.py`:
  - `embedded_app_key() -> str | None`: imports `APP_KEY` from `._app_key`. It returns `None` on
    `ImportError` or when the key is empty or whitespace.
  - `app_key_state(key: str | None) -> Literal["embedded", "none"]`.
  - `water_data_configuration(key: str | None) -> contextlib.AbstractContextManager[None]`: returns
    `contextlib.nullcontext()` when the key is `None`; otherwise
    `dataretrieval.configure(dataretrieval.Configuration(api_key=key))` (R4).
- Produces, in `scripts/write_app_key.py`: `main(env: Mapping[str, str], target: Path) -> str`.
  If `env.get("WATERDATA_APP_KEY", "").strip()` is set, it writes
  `APP_KEY = <repr(key)>\n`, preceded by a do-not-commit comment, to `target` and returns
  `"embedded"`. Otherwise it deletes `target` if it exists and returns `"none"`. The script's
  `__main__` prints only `Water Data app key: <state>`.

- [ ] **Step 1: Write failing tests in `tests/test_app_key.py`.** `FAKE = "fake-key-for-tests-0123"`.
  - `test_no_key_opens_no_configure_block`: monkeypatch `app_key.embedded_app_key` to return
    `None` and spy on `dataretrieval.configure` with a counting wrapper. Run `app.main(["add-data", "discharge", "--output-dir", str(tmp_path)])`
    with the `fake_waterdata` fixture from Task 3.3. Assert
    `spy.calls == 0`.
  - `test_embedded_key_wraps_every_call`: the key is `FAKE`. Each fake waterdata function records
    `dataretrieval.configuration.api_key()` at call time. Run an `xml-compat` bundle that includes
    station discovery and add-data, then `add-data` and `create-new-project`. Assert that every
    recorded value `== FAKE` and that the set of recorded functions equals
    `{"get_daily", "get_time_series_metadata", "get_monitoring_locations", "get_field_measurements"}`.
    Clear `API_USGS_PAT` with `monkeypatch.delenv(..., raising=False)`.
  - `test_configure_block_beats_user_env`: set `API_USGS_PAT="user-key"` and embed `FAKE`; the
    recorded key `== FAKE`.
  - `test_debug_reports_state_not_value` (Review Focus 3): with `FAKE`, run
    `cli.run_cli(["xml-compat", "--debug", "--debug-log", str(log), "--xml", "<function"])`.
    `"[htdr-cli debug] Water Data app key: embedded"` is a line of stderr. `FAKE` is not in stdout,
    stderr or `log.read_text()`. With no key, the line reads `... app key: none`.
  - `test_key_absent_from_outputs`: after the embedded-key `add-data` run, no file under
    `tmp_path` contains `FAKE` (`rglob("*")`, read the bytes).
  - `test_version_output_has_no_key`: `--version` stdout does not contain `FAKE`.
  - `test_write_app_key_embeds_and_removes`: `main({"WATERDATA_APP_KEY": FAKE}, p)` returns
    `"embedded"`, and `runpy.run_path(p)["APP_KEY"] == FAKE`. Then `main({}, p)` returns `"none"`
    and `not p.exists()`. `main({"WATERDATA_APP_KEY": "  "}, p)` also returns `"none"`.
- [ ] **Step 2: Run the tests and confirm they fail** on the missing modules.
- [ ] **Step 3: Implement.**
  - Create `app_key.py` and the script.
  - `app.main` opens `with water_data_configuration(embedded_app_key()):` around the dispatch to
    `run_cli`. The bare-args `--help` path can stay inside it.
  - In `cli.run_cli`'s `xml-compat` branch, right after `_log_process_context`, log
    `Water Data app key: {app_key_state(embedded_app_key())}` when a debug logger exists.
  - Spec file: add `'hydrologic_toolbox_data_retrieval_cli._app_key'` and `'...app_key'`, and
    `'...waterdata_calls'`, to `hiddenimports`. PyInstaller warns but does not fail when
    `_app_key` is absent. Confirm that with a local build and record it as a gotcha.
  - `ci.yaml` `build-exe`, before the build step: `pixi run -e build python scripts/write_app_key.py`
    with `env: WATERDATA_APP_KEY: ${{ secrets.WATERDATA_APP_KEY }}`. Add a smoke check that reads
    the state from `xml-compat --debug --xml "<function"` stderr. On `refs/tags/v*` it must be
    `embedded`, or the step throws; elsewhere it writes the state to the log. Comment that fork PRs
    get no secrets and build unkeyed.
- [ ] **Step 4: Run the tests.** `pixi run test` and `pixi run lint` pass. Build locally twice,
  with and without `WATERDATA_APP_KEY=fake-local`, and check `--debug` reports `embedded` and then
  `none`. Then check that the fake value is absent from the build log:
  `grep -c fake-local build.log`, with the output to a file and the exit code checked. Delete the
  generated `_app_key.py` afterwards (`git status --ignored` confirms).
- [ ] **Step 5: Commit.** Message: `Carry an optional Water Data app key in the exe build`.

### Task 3.6: Regenerate dist/outputs and compare

**Files:**

- Create: `examples/sandbox/dataretrieval_1_4/regenerate_outputs.py`, `compare_outputs.py`, and a `## <date> regeneration` section in `log.md`

**Interfaces:**

- `regenerate_outputs.py <out_root>` runs, through `subprocess` and
  `[sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", ...]`, exactly the six README
  Commands-table rows (same workflow, station, bbox, dates and folder name), into
  `<out_root>/<folder>`. Default `<out_root>` is
  `examples/sandbox/dataretrieval_1_4/regenerated` (git-ignored; add it to `.gitignore`).
- `compare_outputs.py <reference_root> <new_root>` prints one report and exits 1 on any format
  difference. The rule is the spec's:
  - Header lines, column names and order, file names, and shapefile field names, types and widths
    must match exactly.
  - Values are compared only on dates present in both files.
  - Record counts are reported, not required to match.
  - `.prj` text must match exactly.

- [ ] **Step 1: Write a test for the comparator,** `tests/test_compare_outputs.py`, which imports
  the script by path.
  - `test_identical_trees_pass`: copy one `dist/outputs` folder twice into `tmp_path`; exit `0`.
  - `test_header_change_fails`: edit line 2 of the copy; the report contains
    `header line 2 differs` and the exit is `1`.
  - `test_extra_dates_reported_not_failed`: append one body row with a new date; the exit is `0`
    and the report contains `f"records: {n} -> {n + 1}"`, where `n` is the reference's body-row
    count, computed in the test.
- [ ] **Step 2: Implement both scripts.** The tests pass.
- [ ] **Step 3: Run them live** (about 15 requests), with output to a file and the exit code
  checked. Explain every reported difference in `log.md` as either *data changed at source*
  (cite the dates or values) or *format*. A format difference sends execution back to Task 3.4,
  or onto the Breaking list.
- [ ] **Step 4: Run `pixi run test-live`** against v1, to a file, and check the exit code. Update
  live tests only where v1 changed something the log records.
- [ ] **Step 5: Commit** the scripts, the test and the log (not the regenerated outputs; spec B.2
  commits them only after Paul signs off). Message:
  `Add repeatable regeneration and comparison of dist/outputs`.

### Task 3.7: Paul's checklist, the 1.4 gotchas and the changelog

**Files:**

- Create: `docs/toolbox-test-checklist.md`
- Modify: `AGENTS.md` (the `### dataretrieval 1.4` gotcha section, plus the app-key answer slot), `CHANGELOG.md`

- [ ] **Step 1: Write the checklist.**
  - Station discovery: one row per `DataType`, using the README's projected example region. Each
    row gives the exact XML, the expected `<success>` line and the shapefile name.
  - Add-data: one row per workflow, using the probe stations.
  - One multi-function bundle.
  - One invalid request, with the expected `<error>` text exactly as the code produces it (run
    each through `pixi run cli` and paste the real output).
  - How to read `--version` and the key state.
  - Every expected difference from v0.1.0, copied from the log.
  - Write it for Paul: a Windows user, with commands in `cmd` form.
- [ ] **Step 2: Fill the AGENTS.md gotchas.** Add each 1.4 change that the probe measured, as
  *learned here* with the date. Add the PyInstaller `_app_key` hidden-import behaviour. Add a line
  under guardrails: "App key: whether embedding is the intended use, and how to rotate it, is
  pending confirmation from the api.waterdata team (asked 2026-11-03)."
- [ ] **Step 3: Update the CHANGELOG.** Its Breaking section matches the log exactly, or reads
  `None` if there is no format difference.
- [ ] **Step 4: Commit.** Message: `Add Toolbox test checklist; record 1.4 gotchas`. Then run the
  gate procedure. The PR description lists the probe's findings, every contract difference (or
  "none") and the regeneration report summary.

---

## Group 4: Examples

Branch: `dr14/g4-examples` from local `round/dataretrieval-1-4`. Notebooks are written as jupytext
`.py` files, synced, executed headlessly, and committed in pairs, with outputs in the `.ipynb`.
Write for water data scientists fluent in pandas and geopandas. The markdown says what each table
and figure shows.

### Task 4.1: reference_data

**Files:**

- Create: `examples/reference_data/README.md`, `legacy_nwis_rdb/{dv.txt,site.txt,NWIS_gw_periodic_324937083433001.txt}`, `api_waterdata_v0/{monitoring_locations_items.json,monitoring_locations_items.csv}`

- [ ] **Step 1: Restore the files** with
  `git show "55a7d98^:sandbox/example_data/nwis_rdb/dv.txt" > examples/reference_data/legacy_nwis_rdb/dv.txt`
  and likewise for the others (`api.waterdata.usgs.gov/` → `api_waterdata_v0/`). Brace any
  variable in zsh. Then check: `git hash-object` of each restored file equals
  `git rev-parse "55a7d98^:<path>"`.
- [ ] **Step 2: Write the README.**
  - Provenance: the source commits `1621ba9` (2026-04-28) and `d4add41` (2026-04-29), and each
    file's retrieval date, read from its own header.
  - Why the files are kept: legacy NWIS is being retired, and these show what the Toolbox received
    before this CLI.
  - What was left out, and why: `dv_items.json` (9.9 MB) and `dv_items.csv`, which can be fetched
    again.
- [ ] **Step 3: Commit.** Message: `Restore legacy NWIS and v0 reference files for the examples`.

### Task 4.2: `1_using_the_cli`

**Files:**

- Create: `examples/1_using_the_cli.py`, `examples/1_using_the_cli.ipynb`

- [ ] **Step 1: Write the `.py`** (py:percent), covering spec Part E's list in order.
  - A `run(*args)` helper calls `subprocess.run([sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", *args], capture_output=True, text=True)`
    and displays the exit code, stdout and stderr. A markdown note gives the equivalent Windows
    exe command.
  - Commands, in order: `create-new-project` with one workflow, then several; `add-data` for each
    workflow; `xml-compat` with a station request, an add-data request, a bundle and the invalid
    request, showing the exact stdout.
  - Read the outputs back: the shapefile's attribute table and a simple map
    (`gdf.plot`, matplotlib); the CSV's header lines and first rows.
  - All output goes to `examples/outputs/1_using_the_cli/`.
  - Use 2024 date ranges for `add-data` to keep requests small. Say so in the markdown, and show
    the full-history command without running it.
- [ ] **Step 2: Sync and execute.** `pixi run jupytext --sync examples/1_using_the_cli.py`, then
  `pixi run jupyter nbconvert --to notebook --execute --inplace examples/1_using_the_cli.ipynb > .agent-workspace/nb1.txt 2>&1; echo "EXIT=$?" >> .agent-workspace/nb1.txt`.
  The exit is 0, and no cell output contains `Traceback`
  (`grep -c Traceback examples/1_using_the_cli.ipynb` prints `0`). Run
  `pixi run jupytext --sync` again so the pair agrees.
- [ ] **Step 3: Commit both files.** Message: `Add example: using the CLI`.

### Task 4.3: `2_inside_the_cli`

**Files:**

- Create: `examples/2_inside_the_cli.py`, `examples/2_inside_the_cli.ipynb`

- [ ] **Step 1: Write the `.py`.** Call `dataretrieval.waterdata` directly for the four calls, and
  show the raw frames (`.info()`, `.head()`). Then walk through the package's own functions on
  those frames. Never copy them; private helpers are acceptable.
  - `timeseries._select_matching_timeseries_metadata_row` and `_select_matching_monitoring_location_row`;
  - `_build_csv_header_metadata` and `_build_periodic_csv_header_metadata`, then
    `exports.export_timeseries_artifacts`, showing the header lines;
  - `exports._STATION_SHAPEFILE_CROSSWALK` as a table, and `_station_shapefile_field_specs`;
  - `xml_compat._transform_region_bbox_to_wgs84` on the README's projected region;
  - Task 3.4's `_format_construction_date` on the three precisions.

  End with a side-by-side of `reference_data/legacy_nwis_rdb/dv.txt` (read with
  `pd.read_csv(..., sep="\t", comment="#")`, dropping the RDB format row) and the CLI's CSV for
  02225500, over a shared date window, with a column-mapping table. Count the private helpers
  used. If there are more than about six, note it for the hand-back; do not refactor `src/`.
- [ ] **Step 2: Sync and execute** as in Task 4.2.
- [ ] **Step 3: Commit.** Message: `Add example: inside the CLI`.

### Task 4.4: examples/README.md

- [ ] **Step 1: Write `examples/README.md`.** Say what each notebook is for and who it is for; how
  to run them (`pixi run jupyter lab`, then open the `.ipynb`, or edit the `.py`); that both need
  the network and are run by hand, not by CI; what `reference_data/` and `sandbox/` hold; and
  that output goes to the git-ignored `examples/outputs/`.
- [ ] **Step 2: Check the README.** Its links resolve (`test -e` each one), and the README's
  `examples/` link from Task 1.5 now resolves.
- [ ] **Step 3: Commit.** Message: `Describe the examples folder`. Then run the gate procedure.

---

## Group 5: Round end

Branch: `dr14/g5-round-end` from local `round/dataretrieval-1-4`.

### Task 5.1: Dependency update

- [ ] **Step 1: Update the lock.** `pixi update`, then commit `pixi.lock` **alone**:
  `Update locked dependencies at round end`. Never run `pixi upgrade`.
- [ ] **Step 2: Report what the pins hold back.** Run
  `pixi upgrade --dry-run > .agent-workspace/upgrade-dry.txt 2>&1`. Mark each entry as either a
  deliberate cap or a stale cap.
- [ ] **Step 3: Verify the environments.**
  - `pixi install --locked`, and the no-PyPI-fallback grep.
  - `pixi run test`, `pixi run -e ci test`, `pixi run lint`,
    `pixi run ruff format --check` and `pixi run typecheck`, each to a file with
    its exit code.
  - Re-execute both notebooks (Task 4.2, Step 2), and commit them if their outputs changed.
- [ ] **Step 4: Check the lock diff.** Compare the package lines of
  `git diff HEAD~1 -- pixi.lock` for major-version jumps, downgrades and removed packages. If
  something breaks: fix it if the fix is small; otherwise cap it in **both** lists, with a comment
  naming the version, and commit that with a minimal `pixi lock` before the update commit.

### Task 5.2: Final review and hand-back

- [ ] **Step 1: Final whole-branch review.** Run it on the most capable model, over
  `git diff main...dr14/g5-round-end`, pointed at the ledger's rulings. The review re-measures
  every number in AGENTS.md, README, CHANGELOG, the log and the checklist. Then one fix wave and a
  scoped re-review, and fix everything (Minor findings included).
- [ ] **Step 2: Finalize the CHANGELOG.** Rename `[Unreleased]` to `[0.2.0] - unreleased`; Anthony
  dates it at tag time. Its Breaking section matches the PR description.
- [ ] **Step 3: Hand back.**
  - Every ruling of the round, in order, each with what it costs if wrong.
  - The `pixi upgrade --dry-run` list.
  - The PR title and description for **`round/dataretrieval-1-4` → `main`**, to be opened as a
    **draft**. The description includes: the Toolbox contract changes (or "none"); the probe
    summary; the regeneration report; the app-key state ("CI builds embed the key when the
    `WATERDATA_APP_KEY` secret exists; until then, builds are unkeyed"); that the draft-release
    step is untested until the first tag; the major-version jumps; and the steps for Paul (download
    the PR's `build-exe` artifact, follow `docs/toolbox-test-checklist.md`, and reply on the PR).
- [ ] **Step 4: Stop.** After Paul's comment, each fix is a short gate on this branch. One of them
  commits the regenerated `dist/outputs/`, by copying `examples/sandbox/dataretrieval_1_4/regenerated/*`
  over `dist/outputs/` and re-running `compare_outputs.py`, which exits 0 against itself. Anthony
  marks the PR ready, merges it, adds the key to the secret, and tags `v0.2.0`.
