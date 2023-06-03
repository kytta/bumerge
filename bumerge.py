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
SPDX-License-Identifier: BSD-3-Clause
"""
import sys
from collections.abc import Iterable
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Optional
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from pydantic import StrictInt
from pydantic import root_validator
from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)
yaml.sort_base_mapping_type_on_output = False
yaml.default_flow_style = False

__version__ = "0.2.0"

# A very simple dict type for the config
# TODO: use a proper schema (with validation?)
JSONDict = dict[str, Any]

# TODO: support other distributions
Variant = Literal["fcos"]
Version = str


class Entity(BaseModel):
    id: Optional[StrictInt]  # noqa: A003
    name: Optional[str]


class FSObject(BaseModel):
    path: str
    overwrite: Optional[bool]
    user: Optional[Entity]
    group: Optional[Entity]


class Tang(BaseModel):
    url: str
    thumbprint: str
    advertisement: Optional[str]


class LUKSBoot(BaseModel):
    tang: Optional[list[Tang]]
    tpm2: Optional[bool]
    threshold: Optional[StrictInt]
    discard: Optional[bool]


class BootMirror(BaseModel):
    devices: Optional[list[str]]


class BootDevice(BaseModel):
    layout: Optional[str]
    luks: Optional[LUKSBoot]
    mirror: Optional[BootMirror]


class CustomClevis(BaseModel):
    pin: str
    config: str
    needs_network: Optional[bool]


class Clevis(BaseModel):
    tang: Optional[list[Tang]]
    tpm2: Optional[bool]
    threshold: Optional[StrictInt]
    custom: Optional[CustomClevis]


class Directory(FSObject):
    mode: Optional[StrictInt]


class Partition(BaseModel):
    label: Optional[str]
    number: Optional[StrictInt]
    size_mib: Optional[StrictInt]
    start_mib: Optional[StrictInt]
    type_guid: Optional[UUID]
    guid: Optional[UUID]
    wipe_partition_entry: Optional[bool]
    should_exist: Optional[bool]
    resize: Optional[bool]


class Disk(BaseModel):
    device: str
    wipe_table: Optional[bool]
    partitions: Optional[list[Partition]]


class Dropin(BaseModel):
    name: str
    contents: Optional[str]
    contents_local: Optional[str]

    @root_validator()
    def _mutually_exclusive(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("contents") and values.get("contents_local"):
            _msg = "'contents' and 'contents_local' are mutually exclusive."
            raise ValueError(_msg)

        return values


class HttpHeader(BaseModel):
    name: str
    value: Optional[str]


class Verification(BaseModel):
    hash: Optional[str]  # noqa: A003


class FileContents(BaseModel):
    source: str
    inline: str
    local: str
    compression: Optional[Literal["gzip"]]
    http_headers: Optional[list[HttpHeader]]
    verification: Optional[Verification]

    @root_validator()
    def _mutually_exclusive(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("source") and values.get("inline") \
                or values.get("source") and values.get("local") \
                or values.get("inline") and values.get("local"):
            _msg = "'source', 'inline', and 'local' are mutually exclusive."
            raise ValueError(_msg)
        return values


class File(FSObject):
    contents: Optional[FileContents]
    append: Optional[list[FileContents]]
    mode: Optional[StrictInt]


class Filesystem(BaseModel):
    device: str
    format: Literal[  # noqa: A003
        "ext4", "btrfs", "xfs", "vfat", "swap", "none"]
    path: Optional[str]
    wipe_filesystem: Optional[bool]
    label: Optional[str]
    uuid: Optional[UUID]
    options: Optional[list[str]]
    mount_options: Optional[list[str]]
    with_mount_unit: Optional[bool]


class GrubUser(BaseModel):
    name: str
    password_hash: str


class Grub(BaseModel):
    users: Optional[list[GrubUser]]


class IgnitionConfig(BaseModel):
    merge: Optional[list[FileContents]]
    replace: Optional[FileContents]


class Proxy(BaseModel):
    http_proxy: Optional[str]
    https_proxy: Optional[str]
    no_proxy: Optional[list[str]]


class TLS(BaseModel):
    certificate_authorities: Optional[list[FileContents]]


class Security(BaseModel):
    tls: Optional[TLS]


class Timeouts(BaseModel):
    http_response_headers: StrictInt
    http_total: StrictInt


class IgnitionSchema(BaseModel):
    config: Optional[IgnitionConfig]
    timeouts: Optional[Timeouts]
    security: Optional[Security]
    proxy: Optional[Proxy]


class Link(FSObject):
    target: str
    hard: Optional[bool]


class LUKS(BaseModel):
    name: str
    device: str
    key_file: Optional[FileContents]
    label: Optional[str]
    uuid: Optional[UUID]
    options: Optional[list[str]]
    discard: Optional[bool]
    open_options: Optional[list[str]]
    wipe_volume: Optional[bool]
    clevis: Optional[Clevis]


class KernelArguments(BaseModel):
    should_exist: Optional[list[str]]
    should_not_exist: Optional[list[str]]


class PasswdGroup(BaseModel):
    name: str
    gid: Optional[StrictInt]
    password_hash: Optional[str]
    should_exist: Optional[bool]
    system: Optional[bool]


class PasswdUser(BaseModel):
    name: str
    password_hash: Optional[str]
    ssh_authorized_keys: Optional[list[str]]
    uid: Optional[StrictInt]
    gecos: Optional[str]
    home_dir: Optional[str]
    no_create_home: Optional[bool]
    primary_group: Optional[str]
    groups: Optional[list[str]]
    no_user_group: Optional[bool]
    no_log_init: Optional[bool]
    shell: Optional[str]
    should_exist: Optional[bool]
    system: Optional[bool]

    class Config:
        fields = {
            "ssh_authorized_keys": {
                "unique_items": True,
            },
        }


class PasswdSchema(BaseModel):
    users: Optional[list[PasswdUser]]
    groups: Optional[list[PasswdGroup]]


class RAID(BaseModel):
    name: str
    level: str
    devices: list[str]
    spares: Optional[StrictInt]
    options: Optional[list[str]]


class Tree(BaseModel):
    local: str
    path: Optional[str]


class StorageSchema(BaseModel):
    disks: Optional[list[Disk]]
    raid: Optional[list[RAID]]
    filesystems: Optional[list[Filesystem]]
    files: Optional[list[File]]
    directories: Optional[list[Directory]]
    links: Optional[list[Link]]
    luks: Optional[list[LUKS]]
    trees: Optional[list[Tree]]


class SystemdUnit(BaseModel):
    name: str
    enabled: Optional[bool]
    mask: Optional[bool]
    contents: Optional[str]
    contents_local: Optional[str]
    dropins: Optional[list[Dropin]]

    @root_validator()
    def _mutually_exclusive(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("contents") and values.get("contents_local"):
            _msg = "'contents' and 'contents_local' are mutually exclusive."
            raise ValueError(_msg)
        return values


class SystemdSchema(BaseModel):
    units: Optional[list[SystemdUnit]]


class FCOS150Schema(BaseModel):
    """Schema for Fedora CoreOS Specification v1.5.0.

    See: https://coreos.github.io/butane/config-fcos-v1_5/
    """

    variant: Literal["fcos"] = "fcos"
    version: Literal["1.5.0"] = "1.5.0"
    ignition: Optional[IgnitionSchema]
    storage: Optional[StorageSchema]
    systemd: Optional[SystemdSchema]
    passwd: Optional[PasswdSchema]
    kernel_arguments: Optional[KernelArguments]
    boot_device: Optional[BootDevice]
    grub: Optional[Grub]


class ConfigurationError(BaseException):
    """Base exception class for configuration errors."""

    def __init__(
        self,
        message: str = "",
        *,
        field: Optional[str] = None,
    ) -> None:
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

    def __init__(self, field: str, flag: Optional[str] = None) -> None:
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
        flag: Optional[str] = None,
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
    result = []

    for file in config_files:
        try:
            with file.open() as f:
                result.append(yaml.load(f))
        except OSError as exc:
            raise ConfigurationError(str(exc)) from exc

    return result


def validate_config(
    config: JSONDict,
    variant: Optional[Variant],
    version: Optional[Version],
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


def _main(argv: Optional[Sequence[str]] = None) -> None:
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
        type=Path,
        default=None,
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

    result = FCOS150Schema.parse_obj(result).dict(exclude_unset=True)

    if args.output is None:
        yaml.dump(result, sys.stdout)
    else:
        with args.output.open("w") as f:
            yaml.dump(result, f)


if __name__ == "__main__":
    _main()
