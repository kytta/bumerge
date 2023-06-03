# SPDX-FileCopyrightText: © 2023 Nikita Karamov <me@kytta.dev>
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from contextlib import nullcontext
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

import bumerge


@pytest.mark.parametrize(
    ("argv", "output"), [
        ([], ""),
        (["--version"], bumerge.__version__),
        (["--help"], "usage:"),
    ],
)
def test_main(capsys, argv, output):
    with pytest.raises(SystemExit):
        bumerge._main(argv)

    captured = capsys.readouterr()
    assert output in captured.out


@pytest.mark.parametrize(
    ("file", "printed"), [
        ("users.bu", "Error in field"),
        ("idontexist.bu", "Configuration error:"),
    ],
)
def test_main_bad_config(
        capsys,
        shared_datadir: Path,
        file: str,
        printed: str):
    with pytest.raises(SystemExit):
        bumerge._main([str(shared_datadir / file)])

    captured = capsys.readouterr()
    assert printed in captured.err


def test_main_with_files(capsys, shared_datadir: Path):
    files = [
        shared_datadir / "root.bu",
        shared_datadir / "users.bu",
        shared_datadir / "disks.bu",
        shared_datadir / "filesystems.bu",
    ]
    expected_output = """\
variant: fcos
version: 1.5.0
storage:
  disks:
  - device: /dev/disk/by-id/coreos-boot-disk
    wipe_table: false
    partitions:
    - label: root
      number: 4
      size_mib: 8192
      resize: true
    - label: var
      size_mib: 0
  filesystems:
  - device: /dev/disk/by-partlabel/var
    format: ext4
    path: /var
    with_mount_unit: true
passwd:
  users:
  - name: admin
    ssh_authorized_keys:
    - ssh-ed25519 ...
    groups:
    - sudo
    - wheel
"""

    bumerge._main([str(f) for f in files])

    captured = capsys.readouterr()
    assert expected_output in captured.out


def test_main_writes_to_file(shared_datadir, tmp_path):
    argv = [
        "--output",
        str(tmp_path / "output.bu"),
        str((shared_datadir / "root.bu").resolve()),
    ]
    expected_output = """\
variant: fcos
version: 1.5.0
"""

    bumerge._main(argv)

    assert (tmp_path / "output.bu").read_text() == expected_output


@pytest.mark.parametrize(
    ("source", "destination", "result"), [
        ({}, {}, {}),
        ({"key": 42}, {}, {"key": 42}),
        ({"key": "new"}, {"key": "old"}, {"key": "new"}),
        ({"key": {"sub": 42}}, {"key": "old"}, {"key": {"sub": 42}}),
        (
            {"key": {"sub": "new"}},
            {"key": {"sub": "old"}},
            {"key": {"sub": "new"}},
        ),
    ],
)
def test_merge_dicts(
    source: bumerge.JSONDict,
    destination: bumerge.JSONDict,
    result: bumerge.JSONDict,
):
    retval = bumerge.merge_dicts(source, destination)

    assert retval == result


def test_read_config_files(shared_datadir: Path):
    config_files = [
        shared_datadir / "root.bu",
        shared_datadir / "users.bu",
        shared_datadir / "disks.bu",
        shared_datadir / "filesystems.bu",
    ]

    retval = bumerge.read_config_files(config_files)

    assert retval == [
        {
            "variant": "fcos",
            "version": "1.5.0",
        },
        {
            "passwd": {
                "users": [
                    {
                        "name": "admin",
                        "groups": [
                            "sudo",
                            "wheel",
                        ],
                        "ssh_authorized_keys": [
                            "ssh-ed25519 ...",
                        ],
                    },
                ],
            },
        },
        {
            "storage": {
                "disks": [
                    {
                        "device": "/dev/disk/by-id/coreos-boot-disk",
                        "wipe_table": False,
                        "partitions": [
                            {
                                "label": "root",
                                "number": 4,
                                "size_mib": 8192,
                                "resize": True,
                            },
                            {
                                "label": "var",
                                "size_mib": 0,
                            },
                        ],
                    },
                ],
            },
        },
        {
            "storage": {
                "filesystems": [
                    {
                        "device": "/dev/disk/by-partlabel/var",
                        "format": "ext4",
                        "path": "/var",
                        "with_mount_unit": True,
                    },
                ],
            },
        },
    ]


@pytest.mark.parametrize(
    ("config", "variant", "version", "context", "result"), [
        ({}, None, None, pytest.raises(bumerge.FieldRequiredError), None),
        ({"version": "1.5.0"}, None, None, pytest.raises(
            bumerge.FieldRequiredError), None),
        ({"variant": "fcos"}, None, None, pytest.raises(
            bumerge.FieldRequiredError), None),
        ({"version": "1.5.0"}, "fcos", "1.5.0", nullcontext(),
         {"version": "1.5.0", "variant": "fcos"}),
        ({"variant": "fcos"}, "fcos", "1.5.0", nullcontext(),
         {"variant": "fcos", "version": "1.5.0"}),
        ({"version": "1.4.0", "variant": "fcos"}, "fcos", "1.5.0",
         pytest.raises(bumerge.FieldMismatchError), None),
        ({"version": "1.5.0", "variant": "openshift"}, "fcos", "1.5.0",
         pytest.raises(bumerge.FieldMismatchError), None),
    ],
)
def test_validate_config(config, variant, version, context, result):
    with context:
        retval = bumerge.validate_config(config, variant, version)

    if result:
        assert retval == result
