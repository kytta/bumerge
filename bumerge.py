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

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence

from ruamel.yaml import YAML

__version__ = "0.2.0"

# A very simple dict type for the config
# TODO: use a proper schema (with validation?)
JSONDict = dict[str, Any]

# TODO: support other distributions
Variant = Literal["fcos"]
Version = str


class ConfigurationError(BaseException):
    """Base exception class for configuration errors."""

    def __init__(self, message: str = "", *, field: str | None = None) -> None:
        """Create a configuration error instance.

        :param message: message that describes the error
        :param field: configuration field that caused the error
        """
        super().__init__()
        self.message = message
        self.field = field

    def __str__(self) -> str:
        if self.field:
            prefix = f"Error in field '{self.field}'"
        else:
            prefix = "Configuration error"

        return f"{prefix}: {self.message}"


class FieldRequiredError(ConfigurationError):
    """Exception class for missing fields."""

    def __init__(self, field: str, flag: str | None = None) -> None:
        """Create a missing field error instance.

        :param field: name of the field that is missing
        :param flag: name of the CLI flag to set the default field value
        """
        super().__init__(
            "Cannot infer field, and no default was given. Set the field in "
            f"one of the configuration files, or use the '--{flag or field}' "
            "command-line option.",
            field=field,
        )


class FieldMismatchError(ConfigurationError):
    """Exception class for mismatched fields.

    These exception happen when the field defined in the config doesn't
    match the one defined on the command line.
    """

    T = TypeVar("T")

    def __init__(
        self,
        field: str,
        expected: T,
        actual: T,
        flag: str | None = None,
    ) -> None:
        """Create a field mismatch error instance.

        :param field:
            name of the field with the incorrect value
        :param expected:
            the expected field value, that is, the one set via
            the command-line argument
        :param actual:
            the actual field value, that is, the one set in the Butane
            file
        :param flag:
            name of the CLI flag to set the default field value
        """
        super().__init__(
            f"The configuration value {actual!r} does not match the value of "
            f"the --{flag or field} flag: {expected!r}. Fix either the "
            "configuration file or the flag.",
            field=field,
        )


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
        try:
            with file.open() as fp:
                result.append(yaml.load(fp))
        except OSError as exc:
            raise ConfigurationError(str(exc)) from exc

    return result


def validate_config(
    config: JSONDict,
    variant: Variant | None,
    version: Version | None,
) -> JSONDict:
    """Validate the configuration.

    This method will check the values of "variant" and "version" that
    are required in Butane configuration files. If possible, it will add
    the missing values.

    :param config:
        the configuration to be validated
    :param variant:
        the expected Butane specification
    :param version:
        the expected specification version
    """
    if "variant" not in config:
        if variant is None:
            raise FieldRequiredError(
                field="variant",
                flag="variant",
            )
        config["variant"] = variant
    elif variant is not None and config["variant"] != variant:
        raise FieldMismatchError(
            field="variant",
            expected=variant,
            actual=config["variant"],
            flag="variant",
        )

    if "version" not in config:
        if version is None:
            raise FieldRequiredError(
                field="version",
                flag="spec-version",
            )
        config["version"] = version
    elif version is not None and config["version"] != version:
        raise FieldMismatchError(
            field="version",
            expected=version,
            actual=config["version"],
            flag="spec-version",
        )

    return config


def _main(argv: Sequence[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=__version__,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=argparse.FileType("w", encoding="UTF-8"),
        default="-",
        help="output file. Outputs to stdout by default",
        metavar="FILE",
    )
    parser.add_argument(
        "--variant",
        default=None,
        choices=["fcos"],
        help="Butane specification variant",
    )
    parser.add_argument(
        "--spec-version",
        default=None,
        choices=["1.5.0"],
        help="Butane specification version",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="config files to merge",
        metavar="FILE",
    )
    args = parser.parse_args(argv)

    result: JSONDict = {}

    try:
        for config in read_config_files(args.files):
            merge_dicts(config, result)
    except ConfigurationError as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from exc

    try:
        result = validate_config(result, args.variant, args.spec_version)
    except ConfigurationError as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from exc

    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False

    yaml.dump(result, args.output)


if __name__ == "__main__":
    _main()
