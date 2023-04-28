# SPDX-FileCopyrightText: © 2023 Nikita Karamov <me@kytta.dev>
# SPDX-License-Identifier: BSD-2-Clause
from __future__ import annotations

import pytest

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
