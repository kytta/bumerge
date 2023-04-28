# SPDX-FileCopyrightText: © 2023 Nikita Karamov <me@kytta.dev>
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

import bumerge


@pytest.mark.parametrize(
    ("argv", "output"), [
        (None, ""),
        (["--version"], bumerge.__version__),
        (["--help"], "usage:"),
    ],
)
def test_main(capsys, argv, output):
    with pytest.raises(SystemExit):
        bumerge._main(argv)  # noqa: SLF001

    captured = capsys.readouterr()
    assert output in captured.out


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
