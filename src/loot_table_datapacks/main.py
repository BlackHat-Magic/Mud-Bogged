from __future__ import annotations

import argparse
from pathlib import Path

from .common import resolve_format, write_pack
from .packs import PACKS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="loot-table-datapacks",
        description="Build loot-table-tweak datapacks for a given Minecraft version.",
    )
    parser.add_argument(
        "pack",
        choices=sorted(PACKS),
        help="Which datapack to build.",
    )
    parser.add_argument(
        "-v",
        "--version",
        default=None,
        help="Java Edition version, e.g. 1.21.1 (default: latest supported).",
    )
    parser.add_argument(
        "-f",
        "--format",
        default=None,
        help="Datapack format, e.g. 48 or 94.1; overrides --version.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Output directory (default: ./<pack-display-name>, e.g. ./Bogged-Drop-Mud)."
        ),
    )
    args = parser.parse_args()

    pack = PACKS[args.pack]

    try:
        fmt = resolve_format(args.version, args.format)
    except ValueError as err:
        parser.error(str(err))

    if fmt < pack.min_format:
        parser.error(
            f"Pack {pack.name!r} requires format >= {pack.min_format[0]}; got {fmt[0]}."
        )

    out = Path(args.output) if args.output else Path(pack.display_name)
    files = pack.build(fmt)
    write_pack(out, files)

    fmt_str = f"{fmt[0]}" if fmt[1] == 0 else f"{fmt[0]}.{fmt[1]}"
    print(f"Built {pack.display_name} for format {fmt_str} -> {out}")
    for rel in sorted(files):
        print(f"  {rel}")


if __name__ == "__main__":
    main()
