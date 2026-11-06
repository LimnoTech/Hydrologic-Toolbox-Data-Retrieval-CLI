"""Guard the dual-declaration invariant between the PyPI and conda dependency lists.

``hydrologic-toolbox-data-retrieval-cli`` declares its runtime dependencies twice,
on purpose:

* ``[project.dependencies]`` states the contract in PyPI names, so the wheel is
  honest.
* ``[tool.pixi.feature.*.dependencies]`` supplies the actual environment from
  conda-forge, including packages with no usable PyPI distribution.

Pixi resolves conda first and maps those packages onto their PyPI names, so the
two never fight at install time -- but nothing stops them drifting apart in the
manifest. These tests are what stops that.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"

# Conda packages we depend on that have no counterpart in [project.dependencies].
CONDA_ONLY = {
    "python",  # the interpreter itself, not a dependency
}

# PyPI requirements with no conda counterpart: none yet.
PYPI_ONLY: set[str] = set()

# Conda spellings that differ from the PyPI name of the same package.
CONDA_TO_PYPI: dict[str, str] = {
    "matplotlib-base": "matplotlib",
}

# Which pixi feature mirrors which dependency list.
# ``core`` mirrors [project.dependencies]; ``jupyter`` maps to the extra of the
# same name. ``dev`` and ``build`` are deliberately left out: ``dev`` is tooling
# and ``build`` holds PyInstaller, which only builds the exe, so neither is a
# runtime dependency and neither has an extra.
FEATURE_TO_EXTRA = {"core": None, "jupyter": "jupyter"}
EXCLUDED_FEATURES = {"dev", "build"}


def normalize(name: str) -> str:
    """Map a conda spelling onto its PyPI name, then normalize per PEP 503."""
    name = CONDA_TO_PYPI.get(name, name)
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_name(requirement: str) -> str:
    """Strip version specifiers, extras, and markers from a PEP 508 requirement."""
    return re.split(r"[<>=!~\[;\s]", requirement, maxsplit=1)[0]


@pytest.fixture(scope="module")
def pyproject() -> dict:
    """The parsed pyproject.toml, read once per module."""
    return tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))


def pypi_names(pyproject: dict, extra: str | None) -> set[str]:
    """Normalized PyPI names for [project.dependencies] or one extra."""
    if extra is None:
        requirements = pyproject["project"]["dependencies"]
    else:
        requirements = pyproject["project"]["optional-dependencies"][extra]
    return {normalize(requirement_name(r)) for r in requirements}


def conda_names(pyproject: dict, feature: str) -> set[str]:
    """Raw (unnormalized) conda names declared for one pixi feature."""
    return set(pyproject["tool"]["pixi"]["feature"][feature]["dependencies"])


def requirement_specifier(requirement: str) -> str:
    """The version part of a PEP 508 requirement, or "" when it is unconstrained."""
    without_name = requirement[len(requirement_name(requirement)) :]
    without_extras = re.sub(r"^\s*\[[^\]]*\]", "", without_name)
    return without_extras.split(";", maxsplit=1)[0].strip()


def conda_specifier(spec: object) -> str:
    """The version part of a pixi conda spec, or "" when it is unconstrained.

    A spec is either a bare string (``"*"``, ``">=3"``) or a table carrying a
    ``version`` key.
    """
    if isinstance(spec, dict):
        spec = spec.get("version", "*")
    text = str(spec).strip()
    return "" if text == "*" else text


@pytest.mark.parametrize(("feature", "extra"), sorted(FEATURE_TO_EXTRA.items()))
def test_every_pypi_dependency_has_a_conda_counterpart(pyproject, feature, extra):
    """A wheel requirement with no conda package would not install under pixi."""
    declared = pypi_names(pyproject, extra)
    available = {normalize(name) for name in conda_names(pyproject, feature)}
    missing = declared - available - PYPI_ONLY
    assert not missing, (
        f"declared in [project] but absent from the '{feature}' pixi feature: "
        f"{sorted(missing)}"
    )


@pytest.mark.parametrize(("feature", "extra"), sorted(FEATURE_TO_EXTRA.items()))
def test_every_conda_dependency_is_declared_or_allowlisted(pyproject, feature, extra):
    """A conda package absent from [project] makes the wheel metadata a lie."""
    declared = pypi_names(pyproject, extra)
    undeclared = {
        name
        for name in conda_names(pyproject, feature)
        if name not in CONDA_ONLY and normalize(name) not in declared
    }
    assert not undeclared, (
        f"in the '{feature}' pixi feature but not in [project]: {sorted(undeclared)}. "
        "Either declare them, or add them to CONDA_ONLY with a comment saying why."
    )


def test_allowlists_contain_no_dead_entries(pyproject):
    """Stop the allowlists rotting into a place where exceptions hide forever."""
    all_conda = set()
    for feature in pyproject["tool"]["pixi"]["feature"]:
        all_conda |= conda_names(pyproject, feature)

    dead_conda_only = CONDA_ONLY - all_conda
    assert not dead_conda_only, (
        f"CONDA_ONLY lists packages no feature depends on: {sorted(dead_conda_only)}"
    )

    all_pypi = set(pypi_names(pyproject, None))
    for extra in pyproject["project"]["optional-dependencies"]:
        all_pypi |= pypi_names(pyproject, extra)
    dead_pypi_only = PYPI_ONLY - all_pypi
    assert not dead_pypi_only, (
        f"PYPI_ONLY lists packages no extra requires: {sorted(dead_pypi_only)}"
    )

    dead_mappings = set(CONDA_TO_PYPI) - all_conda
    assert not dead_mappings, (
        f"CONDA_TO_PYPI maps packages no feature depends on: {sorted(dead_mappings)}"
    )


def test_feature_to_extra_map_is_complete(pyproject):
    """FEATURE_TO_EXTRA is hand-maintained, unlike CONDA_ONLY and CONDA_TO_PYPI above --
    nothing forced it to stay in step with pyproject.toml. A new
    ``[tool.pixi.feature.*.dependencies]`` table or a new
    ``[project.optional-dependencies]`` extra would otherwise go unparametrized
    above and silently stop being checked. This asserts completeness in both
    directions.
    """
    all_features = set(pyproject["tool"]["pixi"]["feature"])
    covered_or_excluded = set(FEATURE_TO_EXTRA) | EXCLUDED_FEATURES
    uncovered_features = all_features - covered_or_excluded
    assert not uncovered_features, (
        "pixi features missing from FEATURE_TO_EXTRA (and not the "
        "deliberately-excluded "
        f"'dev' and 'build'): {sorted(uncovered_features)}"
    )

    all_extras = set(pyproject["project"]["optional-dependencies"])
    mapped_extras = {extra for extra in FEATURE_TO_EXTRA.values() if extra is not None}
    unmapped_extras = all_extras - mapped_extras
    assert not unmapped_extras, (
        f"[project.optional-dependencies] extras missing from FEATURE_TO_EXTRA: "
        f"{sorted(unmapped_extras)}"
    )


def bounds(spec: str) -> tuple[str | None, str | None]:
    """The ``>=X`` and ``<Y`` versions of a PEP 508 or conda spec, else None.

    Any other operator (``<=``, ``==``, ``~=``, ``!=``, ``>``) raises, as does a bare
    version, so a constraint this helper cannot compare never passes silently.
    """
    spec = re.sub(r"^[A-Za-z_][\w.-]*(\[[^\]]*\])?", "", spec.split(";")[0].strip())
    lower = upper = None
    for clause in (c.strip() for c in spec.split(",")):
        if clause in ("", "*"):
            continue
        match = re.fullmatch(r"(>=|<)\s*([^\s,<>=!~]+)", clause)
        if match is None:
            raise ValueError(
                f"unsupported version specifier {clause!r} in {spec!r}: "
                "bounds() understands only '>=' and '<'"
            )
        if match.group(1) == ">=":
            lower = match.group(2)
        else:
            upper = match.group(2)
    return (lower, upper)


def test_bounds_helper():
    """``bounds`` extracts the floor and ceiling from each specifier style."""
    assert bounds(">=1.3,<1.4") == ("1.3", "1.4")
    assert bounds("*") == (None, None)
    assert bounds(">=1.4") == ("1.4", None)
    assert bounds("dataretrieval>=1.3,<1.4") == ("1.3", "1.4")


@pytest.mark.parametrize(
    ("spec", "clause"),
    [("<=1.4", "<=1.4"), ("==1.3.*", "==1.3.*"), ("~=1.3", "~=1.3")],
)
def test_bounds_rejects_other_operators(spec, clause):
    """An operator ``bounds`` cannot compare raises, naming the specifier."""
    with pytest.raises(ValueError) as excinfo:
        bounds(spec)
    assert str(excinfo.value) == (
        f"unsupported version specifier {clause!r} in {spec!r}: "
        "bounds() understands only '>=' and '<'"
    )


def specifier_dicts(
    pyproject: dict, feature: str, extra: str | None
) -> tuple[dict[str, str], dict[str, str]]:
    """Normalized name -> version specifier, for the PyPI half and the conda half."""
    if extra is None:
        requirements = pyproject["project"]["dependencies"]
    else:
        requirements = pyproject["project"]["optional-dependencies"][extra]
    pypi = {
        normalize(requirement_name(r)): requirement_specifier(r) for r in requirements
    }
    conda = {
        normalize(name): conda_specifier(spec)
        for name, spec in pyproject["tool"]["pixi"]["feature"][feature][
            "dependencies"
        ].items()
    }
    return pypi, conda


@pytest.mark.parametrize(("feature", "extra"), sorted(FEATURE_TO_EXTRA.items()))
def test_bounds_match(pyproject, feature, extra):
    """The PyPI and conda halves carry the same floor and ceiling per package.

    ``bounds`` raises on any operator it cannot compare, and a package constrained
    on one side only has bounds ``(None, None)`` on the other, so this also covers
    "constrained on both sides or neither".
    """
    pypi_raw, conda_raw = specifier_dicts(pyproject, feature, extra)
    mismatched = {
        name: (pypi_raw[name], conda_raw[name])
        for name in pypi_raw.keys() & conda_raw.keys()
        if bounds(pypi_raw[name]) != bounds(conda_raw[name])
    }
    assert not mismatched, (
        f"'{feature}' feature and its PyPI list disagree on bounds "
        f"(package: (PyPI specifier, conda specifier)): {mismatched}"
    )
