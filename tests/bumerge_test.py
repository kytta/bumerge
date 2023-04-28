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
