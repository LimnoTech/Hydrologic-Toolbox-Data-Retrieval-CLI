"""Hold the package section to its one dependency list.

hydrologic-toolbox-data-retrieval-cli is a pixi-build source package,
following LimnoTech's packaging guide (python-scientific variant; private)
and adapted from GLM_modeling's test of the same name. The runtime
dependencies are ``[project.dependencies]``, in PyPI names, and nothing
else. With ``ignore-pypi-mapping = false``, pixi-build-python maps that
list, and ``requires-python``, to conda names in the package's record, and
the repo's own environments install the package through that record.

The mapping drops a requirement it cannot map without a word: a
requirement with an environment marker, a direct reference, a PyPI-only
name, or any name the mapping service was not reachable for during the
lock. The record test below reads the record pixi locked and fails on each
of those, so a re-lock that lost a dependency cannot pass.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]

# PyPI-only requirements (no conda-forge build): the record drops them, so
# each would need declaring separately. None today.
PYPI_ONLY: set[str] = set()

# Where the conda name is not one of the usual spellings `conda_names` tries.
RENAMES: dict[str, str] = {}


@pytest.fixture(scope="module")
def pyproject() -> dict:
    """The parsed pyproject.toml."""
    return tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lock() -> dict:
    """The parsed pixi.lock."""
    return yaml.safe_load((REPO / "pixi.lock").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow() -> dict:
    """The parsed CI workflow."""
    return yaml.safe_load(
        (REPO / ".github/workflows/ci.yaml").read_text(encoding="utf-8")
    )


def package(pyproject: dict) -> dict:
    """The ``[tool.pixi.package]`` table."""
    return pyproject["tool"]["pixi"]["package"]


def normalize(name: str) -> str:
    """A package name normalized per PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str:
    """The distribution name of a PEP 508 requirement."""
    return re.split(r"[\s<>=!~;\[@(]", requirement.strip(), maxsplit=1)[0]


def requirement_specifier(requirement: str) -> str:
    """The version specifier of a requirement with no marker or direct
    reference, spaces removed."""
    rest = requirement.strip()[len(requirement_name(requirement)) :]
    return re.sub(r"\s+", "", rest)


def conda_names(pypi: str) -> set[str]:
    """The conda spellings a PyPI name usually maps to."""
    base = normalize(pypi)
    names = {base, base.replace("-", "_")}
    names |= {
        f"python-{base}",
        f"py-{base}",
        f"{base}-base",
        f"{base}-core",
        f"{base}-python",
    }
    if base in RENAMES:
        names.add(RENAMES[base])
    return {normalize(n) for n in names}


def self_records(pyproject: dict, lock: dict) -> dict[str, dict]:
    """The package's own record (``conda_source: <name>[...] @ .``) for
    each declared platform.

    Fails naming the platform whose default environment has none, so a
    lock made for fewer platforms than the workspace declares cannot
    pass on the records it does have.
    """
    name = package(pyproject)["name"]
    packages = {
        str(p.get("conda_source")): p for p in lock["packages"] if "conda_source" in p
    }
    environment = lock["environments"]["default"]["packages"]
    records = {}
    for platform in pyproject["tool"]["pixi"]["workspace"]["platforms"]:
        sources = [
            e["conda_source"]
            for e in environment.get(platform, [])
            if str(e.get("conda_source", "")).startswith(f"{name}[")
            and str(e["conda_source"]).endswith("@ .")
        ]
        assert len(sources) == 1, f"{platform}: {len(sources)} self records for {name}"
        records[platform] = packages[sources[0]]
    return records


def test_conda_names_tries_the_usual_spellings():
    """Including the narrower conda packages the mapping picks."""
    assert {"geopandas-base", "pyarrow-core", "python-libarchive-c"} <= (
        conda_names("geopandas") | conda_names("pyarrow") | conda_names("libarchive-c")
    )
    assert "pandas" in conda_names("pandas")


def test_requirement_specifier_drops_the_name_and_spaces():
    """A bare name has an empty specifier."""
    assert requirement_specifier("dataretrieval >= 1.3, <1.4") == ">=1.3,<1.4"
    assert requirement_specifier("pyshp") == ""


def test_the_package_is_the_project(pyproject):
    """The conda package and the wheel share one name."""
    assert package(pyproject)["name"] == pyproject["project"]["name"]
    assert package(pyproject)["name"] == "hydrologic-toolbox-data-retrieval-cli"


def test_the_mapping_is_on(pyproject):
    """Without it, [project.dependencies] never reaches the record and
    the environments get only python."""
    assert package(pyproject)["build"]["config"]["ignore-pypi-mapping"] is False


def test_no_requirement_has_a_marker_or_a_direct_reference(pyproject):
    """The mapping drops a marked requirement on every platform and
    turns a direct reference into the conda package of that name."""
    bad = [r for r in pyproject["project"]["dependencies"] if ";" in r or "@" in r]
    assert bad == []


def test_no_requirement_asks_for_an_extra(pyproject):
    """A source package's record carries no extras, so `pkg[extra]`
    would reach the environments as plain `pkg`."""
    assert [r for r in pyproject["project"]["dependencies"] if "[" in r] == []


def test_there_are_no_optional_dependencies(pyproject):
    """One list: the Jupyter packages live in the pixi `jupyter` feature
    only."""
    assert "optional-dependencies" not in pyproject["project"]


def test_core_holds_only_python(pyproject):
    """The runtime list is [project.dependencies]; feature.core holds
    only the environment's python."""
    core = pyproject["tool"]["pixi"]["feature"]["core"]["dependencies"]
    assert core == {"python": "3.12.*"}


def test_pypi_only_names_are_requirements(pyproject):
    """The allowlist names only real requirements, so it cannot hide a
    typo."""
    names = {
        normalize(requirement_name(r)) for r in pyproject["project"]["dependencies"]
    }
    assert names >= PYPI_ONLY


def test_every_requirement_reaches_the_record(pyproject, lock):
    """Each requirement not on PYPI_ONLY is in every self record's
    depends, by one of its conda names, with its specifier. A wrong name
    would pass a count."""
    missing = []
    for record in self_records(pyproject, lock).values():
        depends: dict[str, set[str]] = {}
        for entry in record.get("depends", []):
            name, _, spec = entry.partition(" ")
            depends.setdefault(normalize(name), set()).add(re.sub(r"\s+", "", spec))
        for requirement in pyproject["project"]["dependencies"]:
            name = requirement_name(requirement)
            if normalize(name) in PYPI_ONLY:
                continue
            wanted = requirement_specifier(requirement)
            specs = set().union(*(depends.get(n, set()) for n in conda_names(name)))
            if not specs or (wanted and wanted not in specs):
                missing.append(f"{record['conda_source']}: {requirement}")
    assert missing == [], (
        "requirements missing from the record (re-lock after a manifest change)"
    )


def test_requires_python_reaches_the_record(pyproject, lock):
    """``requires-python`` becomes the record's python dependency."""
    wanted = re.sub(r"\s+", "", pyproject["project"]["requires-python"])
    for record in self_records(pyproject, lock).values():
        assert f"python {wanted}" in record.get("depends", []), record["conda_source"]


def test_pypi_only_names_are_not_in_the_record(pyproject, lock):
    """If one appears, conda-forge has gained a build: take it off the
    allowlist."""
    for record in self_records(pyproject, lock).values():
        names = {normalize(entry.split()[0]) for entry in record.get("depends", [])}
        for pypi in PYPI_ONLY:
            assert not (names & conda_names(pypi)), (
                f"{pypi} is in {record['conda_source']}"
            )


def test_the_package_consumes_itself(pyproject):
    """Every environment installs the package through its record, not
    as a PyPI editable install."""
    name = "hydrologic-toolbox-data-retrieval-cli"
    assert pyproject["tool"]["pixi"]["dependencies"][name] == {"path": "."}
    assert name not in pyproject["tool"]["pixi"].get("pypi-dependencies", {})


def latest_release() -> str:
    """The newest released CHANGELOG heading, or, before the first one,
    the version the ``[Unreleased]`` section names as the previous
    release."""
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## \[(\d+(?:\.\d+)*)\]", changelog, flags=re.MULTILINE)
    if released:
        return released[0]
    previous = re.search(r"^The previous release is v(\d+(?:\.\d+)*) ", changelog, re.M)
    assert previous, "CHANGELOG.md names no release"
    return previous.group(1)


def test_package_version_is_the_latest_release(pyproject):
    """The record's version is the last release, bumped beside
    CHANGELOG.md in each release PR. __version__ still comes from
    hatch-vcs."""
    assert latest_release() == "0.1.0"
    assert package(pyproject)["version"] == latest_release()


def test_pixi_build_is_enabled(pyproject):
    """pixi-build is a preview, so the workspace opts in."""
    workspace = pyproject["tool"]["pixi"]["workspace"]
    assert "pixi-build" in workspace["preview"]


def test_requires_pixi_is_a_floor_only(pyproject):
    """A ceiling would refuse every newer pixi."""
    required = pyproject["tool"]["pixi"]["workspace"]["requires-pixi"]
    assert re.fullmatch(r">=\d+\.\d+\.\d+", required), required


def test_windows_blas_is_openblas(pyproject):
    """conda-forge resolves Intel MKL on win-64 otherwise, and its DLLs
    land in the exe (spec amendment, item 11)."""
    win = pyproject["tool"]["pixi"]["target"]["win-64"]["dependencies"]
    assert win["libblas"] == {"version": "*", "build": "*openblas"}


def locked_names(entry: dict) -> str | None:
    """The package name of a lock environment entry: a conda URL's file
    name, or a PyPI wheel's or sdist's; None for a source package
    (``conda_source``)."""
    url = entry.get("conda") or entry.get("pypi")
    if not url:
        return None
    filename = url.rsplit("/", 1)[-1].split("#", 1)[0]
    if "conda" in entry:
        stem = re.sub(r"\.(conda|tar\.bz2)$", "", filename)
        return normalize(stem.rsplit("-", 2)[0])
    return normalize(re.split(r"-\d", filename, maxsplit=1)[0])


def locked_version(entry: dict) -> str:
    """The version in a conda entry's file name."""
    filename = (entry.get("conda") or "").rsplit("/", 1)[-1]
    return re.sub(r"\.(conda|tar\.bz2)$", "", filename).rsplit("-", 2)[1]


def version_tuple(version: str) -> tuple[int, ...]:
    """The first three numeric parts of a version, for comparison."""
    return tuple(int(part) for part in re.findall(r"\d+", version)[:3])


def locked_platforms(lock: dict):
    """Each (environment, platform, entries) the lock holds."""
    for env_name, env in lock["environments"].items():
        for platform, entries in env["packages"].items():
            yield env_name, platform, entries


def test_locked_names_reads_conda_and_pypi_entries():
    """Names and versions come from the URL's file name."""
    conda = {
        "conda": "https://conda.anaconda.org/conda-forge/osx-arm64/"
        "pyarrow-core-26.0.0-py312h_1_cpu.conda"
    }
    pypi = {
        "pypi": "https://files.pythonhosted.org/packages/0f/b7/ab/"
        "pcodec-1.1.0-cp312-cp312-macosx_11_0_arm64.whl"
    }
    assert locked_names(conda) == "pyarrow-core"
    assert locked_version(conda) == "26.0.0"
    assert locked_names(pypi) == "pcodec"
    assert locked_names({"conda_source": "x[1] @ ."}) is None
    assert version_tuple("3.38.2") >= (3, 38)


def test_pyarrow_is_not_locked(lock):
    """This repo is exempt from LimnoTech's rule that pandas implies
    pyarrow (spec amendment, item 4, 2026-11-16), so a dependency that
    starts pulling pyarrow in is caught here.

    On the Windows runner, pyarrow added 23.9 MB to the zipped exe bundle
    (296.5 -> 320.4 MB) and 0.04 s to `--help`. Measured on macOS with
    pandas 3.1.1, it gave nothing the Toolbox would notice: the CLI's
    dataretrieval calls all take the OGC JSON path, where building the
    tables was 7-10% slower with pyarrow; `to_csv` was unchanged; memory
    fell 60-65%, on tables of a few MB. pandas 3 does not switch
    `read_csv` to the pyarrow engine.
    """
    found = []
    for env_name, platform, entries in locked_platforms(lock):
        names = {locked_names(e) for e in entries}
        if names & {"pyarrow", "pyarrow-core"}:
            found.append(f"{env_name}/{platform}")
    assert found == [], "pyarrow is locked"


def test_sqlite_is_at_least_3_38_wherever_libgdal_is(lock):
    """proj and libspatialite leave sqlite unbounded, and GDAL needs
    3.38. geopandas maps to geopandas-base, which locks no GDAL today;
    this holds the floor if a dependency brings it back."""
    too_old = []
    for env_name, platform, entries in locked_platforms(lock):
        by_name = {locked_names(e): e for e in entries if "conda" in e}
        if not {"libgdal", "libgdal-core"} & set(by_name):
            continue
        sqlite = by_name.get("sqlite") or by_name.get("libsqlite")
        if sqlite is None or version_tuple(locked_version(sqlite)) < (3, 38):
            too_old.append(f"{env_name}/{platform}")
    assert too_old == [], "libgdal is locked beside sqlite older than 3.38"


def lock_source_packages(lock: dict, env: str) -> set[str]:
    """The source packages pixi.lock records in one environment."""
    return {
        str(e["conda_source"]).split("[", 1)[0]
        for entries in lock["environments"][env]["packages"].values()
        for e in entries
        if "conda_source" in e
    }


def reinstall_args(pyproject: dict, env: str, run: list[str]) -> list[str] | None:
    """The `pixi reinstall` a step runs, without `--locked`: directly, or
    through a `pixi run -e <env> <task>` whose task depends on one (the
    build-exe job's `refresh-version`)."""
    if run[:2] == ["pixi", "reinstall"]:
        return [a for a in run if a != "--locked"]
    if run[:4] != ["pixi", "run", "-e", env] or len(run) != 5:
        return None
    tasks = {}
    for feature in pyproject["tool"]["pixi"].get("feature", {}).values():
        tasks |= feature.get("tasks", {})
    tasks |= pyproject["tool"]["pixi"].get("tasks", {})
    task = tasks.get(run[4])
    if not isinstance(task, dict):
        return None
    for name in task.get("depends-on", []):
        found = reinstall_args(pyproject, env, str(tasks.get(name, "")).split())
        if found:
            return found
    return None


def test_ci_rebuilds_the_source_package(pyproject, lock, workflow):
    """The step after every setup-pixi step reinstalls the source
    packages of its environment: on a cache hit, pixi 0.84.2 restores the
    environment without building them, so a fresh checkout lacks the
    git-ignored _version.py their hatch-vcs build hook writes (the
    packaging guide's gotcha)."""
    checked = 0
    for job in workflow["jobs"].values():
        steps = job.get("steps", [])
        for step, after in zip(steps, steps[1:], strict=False):
            if "setup-pixi" not in step.get("uses", ""):
                continue
            env = step["with"]["environments"]
            run = after.get("run", "").split()
            args = reinstall_args(pyproject, env, run)
            assert args is not None, f"{after.get('name')}: {run}"
            assert args[:4] == ["pixi", "reinstall", "-e", env], args
            assert set(args[4:]) == lock_source_packages(lock, env), args
            assert lock_source_packages(lock, env) == {
                "hydrologic-toolbox-data-retrieval-cli"
            }
            checked += 1
    assert checked == 3
