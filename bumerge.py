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

if TYPE_CHECKING:
    from collections.abc import Sequence

__version__ = "0.1.0"


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
