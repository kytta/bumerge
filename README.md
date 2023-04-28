<!--
SPDX-FileCopyrightText: © 2023 Nikita Karamov <me@kytta.dev>
SPDX-License-Identifier: CC-BY-4.0 OR BSD-2-Clause
-->

# bumerge

> Merge Butane configurations

This is a simple Python script that will merge [Butane] configurations from
multiple files into one. Makes your job easier when you manage servers.

- **merges** multiple `.bu` files into one
- **inlines** external files into the configs
- **checks** source configs for errors

bumerge currently supports [Fedora CoreOS Specification v1.5.0][fcos-1.5].
Support for other distributions is planned, but not prioritized.

## Install

```sh
pipx install bumerge  # or pip, or conda, or pipsi, or ...
```

## Use

Just pass the list of the files to the app

```sh
bumerge root.bu modules/time.bu modules/user.bu
```

**Important:** bumerge will perform a deep merge. If there are key conflicts,
the latter file takes precedence.

### Command-line arguments

TBA

## Licence

© 2023 [Nikita Karamov]\
Licensed under the [BSD 2-Clause "Simplified" License][BSD-2-Clause].

This README can also be licensed under the
[Creative Commons Attribution 4.0 International][CC-BY-4.0]

---

This project is hosted on GitHub:
<https://github.com/kytta/bumerge.git>

[Butane]: https://coreos.github.io/butane/
[BSD-2-Clause]: https://spdx.org/licenses/BSD-2-Clause.html
[CC-BY-4.0]: https://spdx.org/licenses/CC-BY-4.0.html
[fcos-1.5]: https://coreos.github.io/butane/config-fcos-v1_5/
[nikita karamov]: https://www.kytta.dev/