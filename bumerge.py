"""bumerge: Merge Butane configurations.

bumerge is a simple Python script that will merge Butane configurations
from multiple files into one. Run it from the command line with the list
of files or use it via an API.

bumerge

* **merges** multiple ``.bu`` files into one
* **inlines** external files into the configs
* **checks** source configs for errors

bumerge currently only supports Fedora CoreOS Specification v1.5.0.
Support for other distributions is planned, but not prioritized.

Source code is hosted on GitHub:
<https://github.com/kytta/bumerge.git>

SPDX-FileCopyrightText: © 2023 Nikita Karamov <me@kytta.dev>
SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence
    from pathlib import Path

from ruamel.yaml import YAML

__version__ = "0.1.0"

# A very simple dict type for the config
# TODO: use a proper schema (with validation?)
JSONDict = dict[str, Any]


def merge_dicts(source: JSONDict, destination: JSONDict) -> JSONDict:
    """Merge one JSON-valid dictionary into another.

    This goes over every key in `source` and sets the keys in
    `destination` with the values, replacing on duplicates. If it
    encounters another dict, it will merge it recursively.

    :param source: the dictionary to be merged
    :param destination: the dictionary to be merged into

    :return: the result of merging two dicts
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            if not isinstance(node, dict):
                destination[key] = value
            else:
                merge_dicts(value, node)
        else:
            destination[key] = value

    return destination


def read_config_files(config_files: Iterable[Path]) -> list[JSONDict]:
    """Read config files and return the configurations.

    :param config_files: list of configuration files to parse
    :return: list of parsed configurations
    """
    yaml = YAML(typ="safe", pure=True)
    result = []
    for file in config_files:
        with file.open() as fp:
            result.append(yaml.load(fp))

    return result


def _main(argv: Sequence[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=__version__,
    )
    parser.parse_args(argv)


if __name__ == "__main__":
    _main()
