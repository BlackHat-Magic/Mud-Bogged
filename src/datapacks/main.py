from __future__ import annotations

import argparse
from pathlib import Path

from .common import pack_zip_name, resolve_target, write_pack, zip_pack
from .packs import PACKS


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="datapacks",
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
    parser.add_argument(
        "-z",
        "--zip",
        action="store_true",
        help=(
            "After building, also zip the pack to "
            "<pack-name>_<project-ver>+mc<supported-version-range>.zip "
            "(e.g. bogged-drop-mud_0.1.0+mc26.1-26.1.2.zip) "
            "in the parent of the output directory."
        ),
    )
    args = parser.parse_args()

    pack = PACKS[args.pack]

    try:
        target = resolve_target(args.version, args.format)
    except ValueError as err:
        parser.error(str(err))

    if target.pack_format < pack.min_format:
        parser.error(
            f"Pack {pack.name!r} requires format >= {pack.min_format[0]}; "
            f"got {target.pack_format[0]}."
        )

    out = Path(args.output) if args.output else Path(pack.display_name)
    files = pack.build(target)
    write_pack(out, files)

    fmt_str = (
        f"{target.pack_format[0]}"
        if target.pack_format[1] == 0
        else f"{target.pack_format[0]}.{target.pack_format[1]}"
    )
    print(f"Built {pack.display_name} for {target.version} (format {fmt_str}) -> {out}")
    for rel in sorted(files):
        print(f"  {rel}")

    if args.zip:
        zip_path = out.parent / pack_zip_name(pack.name, target.pack_format)
        zip_pack(zip_path, files)
        print(f"Zipped -> {zip_path}")


if __name__ == "__main__":
    main()
