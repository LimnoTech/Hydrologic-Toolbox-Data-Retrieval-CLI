"""PROJ's network access is off in pixi environments.

conda-forge proj's activation script turns PROJ_NETWORK on when proj-data is
absent; pyproject.toml's [tool.pixi.activation.env] turns it back off, to match
the frozen exe, which never fetches datum grids. Run through pixi, this checks
that the pixi setting wins.
"""

import pyproj.network


def test_proj_network_is_off() -> None:
    """pixi's PROJ_NETWORK=OFF wins over proj's activation script."""
    assert pyproj.network.is_network_enabled() is False
