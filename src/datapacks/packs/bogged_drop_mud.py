"""Bogged-Drop-Mud: make the Bogged drop Mud or Moss, plus rare swamp drops."""

from __future__ import annotations

from typing import Any

from ..common import (
    Pack,
    Target,
    json_dumps,
    loot_table_dir,
    looting_function,
    pack_mcmeta,
    pack_png,
)

DESCRIPTION = "Make the Bogged drop Mud/Moss Blocks (0-2) plus rare swamp drops"

# The Bogged was introduced in 1.21 (pack format 48), so this pack cannot be
# built for anything older.
MIN_FORMAT: tuple[int, int] = (48, 0)


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


def _weighted_item_pool(
    items: list[str],
    *,
    looting: str,
    min_count: float,
    max_count: float,
    looting_max: float,
) -> dict[str, Any]:
    """A pool with multiple equally-weighted item entries that share the same
    set_count/looting function shape. Each roll picks ONE of the items
    (weighted random across entries) so the count distribution stays per-item.
    """
    entries: list[dict[str, Any]] = []
    for item in items:
        functions: list[dict[str, Any]] = [
            {
                "function": "minecraft:set_count",
                "count": {
                    "type": "minecraft:uniform",
                    "min": min_count,
                    "max": max_count,
                },
                "add": False,
            },
            {
                "function": looting,
                "enchantment": "minecraft:looting",
                "count": {"type": "minecraft:uniform", "min": 0.0, "max": looting_max},
            },
        ]
        entries.append(
            {
                "type": "minecraft:item",
                "name": item,
                "weight": 1,
                "functions": functions,
            }
        )
    return {"rolls": 1.0, "bonus_rolls": 0.0, "entries": entries}


def _rare_drop_pool() -> dict[str, Any]:
    """Rare-drop pool gated by killed_by_player + a Looting-scaled chance.
    Mirrors vanilla's zombie/husk rare-drop condition shape; entries are
    plain items with no set_count (one stack of one item)."""
    return {
        "rolls": 1.0,
        "bonus_rolls": 0.0,
        "conditions": [
            {"condition": "minecraft:killed_by_player"},
            {
                "condition": "minecraft:random_chance_with_enchanted_bonus",
                "unenchanted_chance": 0.025,
                "enchanted_chance": {
                    "type": "minecraft:linear",
                    "base": 0.035,
                    "per_level_above_first": 0.01,
                },
                "enchantment": "minecraft:looting",
            },
        ],
        "entries": [
            {"type": "minecraft:item", "name": "minecraft:red_mushroom"},
            {"type": "minecraft:item", "name": "minecraft:brown_mushroom"},
            {"type": "minecraft:item", "name": "minecraft:glow_berries"},
            {"type": "minecraft:item", "name": "minecraft:azalea"},
            {"type": "minecraft:item", "name": "minecraft:flowering_azalea"},
            {"type": "minecraft:item", "name": "minecraft:mangrove_propagule"},
        ],
    }


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
            _weighted_item_pool(
                ["minecraft:mud", "minecraft:moss_block"],
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
            _rare_drop_pool(),
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

    icon = pack_png(PACK.name)
    if icon is not None:
        files["pack.png"] = icon

    return files


PACK = Pack(
    name="bogged-drop-mud",
    display_name="Bogged-Drop-Mud",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
