"""Bogged-Drop-Mud: make the Bogged drop 0-2 Mud."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..common import (
    Pack,
    Target,
    json_dumps,
    loot_table_dir,
    looting_function,
    pack_mcmeta,
)

DESCRIPTION = "Make the Bogged drop Mud (0-2)"

# The Bogged was introduced in 1.21 (pack format 48), so this pack cannot be
# built for anything older.
MIN_FORMAT: tuple[int, int] = (48, 0)

_STATIC = Path(__file__).parent / "static"


def _item_pool(
    item: str,
    *,
    looting: str,
    min_count: float,
    max_count: float,
    looting_max: float,
    limit: int | None = None,
    conditions: list[dict[str, Any]] | None = None,
    extra_fns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    functions: list[dict[str, Any]] = [
        {
            "function": "minecraft:set_count",
            "count": {"type": "minecraft:uniform", "min": min_count, "max": max_count},
            "add": False,
        },
        {
            "function": looting,
            "enchantment": "minecraft:looting",
            "count": {"type": "minecraft:uniform", "min": 0.0, "max": looting_max},
        },
    ]
    if limit is not None:
        functions[1]["limit"] = limit
    if extra_fns:
        functions.extend(extra_fns)

    entry: dict[str, Any] = {
        "type": "minecraft:item",
        "name": item,
        "functions": functions,
    }
    pool: dict[str, Any] = {"rolls": 1.0, "bonus_rolls": 0.0, "entries": [entry]}
    if conditions:
        pool["conditions"] = conditions
    return pool


def _loot_table(fmt: tuple[int, int]) -> dict[str, Any]:
    looting = looting_function(fmt)
    return {
        "type": "minecraft:entity",
        "pools": [
            _item_pool(
                "minecraft:arrow",
                looting=looting,
                min_count=0.0,
                max_count=2.0,
                looting_max=1.0,
            ),
            _item_pool(
                "minecraft:bone",
                looting=looting,
                min_count=0.0,
                max_count=2.0,
                looting_max=1.0,
            ),
            _item_pool(
                "minecraft:mud",
                looting=looting,
                min_count=0.0,
                max_count=2.0,
                looting_max=1.0,
            ),
            _item_pool(
                "minecraft:tipped_arrow",
                looting=looting,
                min_count=0.0,
                max_count=1.0,
                looting_max=1.0,
                limit=1,
                conditions=[{"condition": "minecraft:killed_by_player"}],
                extra_fns=[
                    {"function": "minecraft:set_potion", "id": "minecraft:poison"}
                ],
            ),
        ],
        "random_sequence": "minecraft:entities/bogged",
    }


def build(target: Target) -> dict[str, str | bytes]:
    fmt = target.pack_format
    if fmt < MIN_FORMAT:
        raise ValueError(
            f"The Bogged first appeared in 1.21 (format {MIN_FORMAT[0]}); "
            f"cannot build for format {fmt[0]}.",
        )

    files: dict[str, str | bytes] = {
        "pack.mcmeta": pack_mcmeta(fmt, DESCRIPTION),
        f"data/minecraft/{loot_table_dir(fmt)}/entities/bogged.json": json_dumps(
            _loot_table(fmt)
        ),
    }

    pack_png = _STATIC / "pack.png"
    if pack_png.is_file():
        files["pack.png"] = pack_png.read_bytes()

    return files


PACK = Pack(
    name="bogged-drop-mud",
    display_name="Bogged-Drop-Mud",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
