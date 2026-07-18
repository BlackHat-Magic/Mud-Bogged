"""Spirit-Flight: a happy ghast harness enchantment (5 levels) scaling flying_speed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..common import Pack, Target, json_dumps, pack_mcmeta, pack_png

DESCRIPTION = "Spirit Flight — happy ghast harness enchantment"

# The happy ghast and harness item both first exist in 1.21.6 (format 80).
MIN_FORMAT: tuple[int, int] = (80, 0)

# Speed scaling. Vanilla flying_speed is 0.05; ridden cruising speed is
# empirically ~flying_speed * 72 in m/s. Target ~20 m/s at level V:
#   level V bonus = 0.2785 - 0.05 = 0.2285
#   per-level increment = 0.2285 / 5 = 0.0457
# See docs/superpowers/specs/2026-07-18-spirit-flight-design.md for derivation.
SPEED_PER_LEVEL = 0.0457
VANILLA_FLYING_SPEED = 0.05

# Enchantment constants. See spec for rationale.
ENCHANTMENT_NAMESPACE = "spirit_flight"
ENCHANTMENT_ID = f"{ENCHANTMENT_NAMESPACE}:spirit_flight"
# Per spec: 5 levels scaling flying_speed from vanilla 0.05 up to ~20 m/s at level V.
MAX_ENCHANTMENT_LEVEL = 5

HARNESS_COLORS = (
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
)

_STATIC = Path(__file__).parent / "static"
_VANILLA_BASE = _STATIC / "vanilla"


def _vanilla_dir(fmt: tuple[int, int]) -> str:
    """Directory under static/vanilla/ for the given format."""
    return str(fmt[0]) if fmt[1] == 0 else f"{fmt[0]}_{fmt[1]}"


def _enchantment_json() -> dict[str, Any]:
    return {
        "description": "Spirit Flight",
        "supported_items": "#spirit_flight:harnesses",
        "primary_items": "#spirit_flight:harnesses",
        "weight": 2,
        "max_level": MAX_ENCHANTMENT_LEVEL,
        "min_cost": {"base": 15, "per_level_above_first": 10},
        "max_cost": {"base": 40, "per_level_above_first": 10},
        "anvil_cost": 4,
        "slots": ["body"],
        "effects": {
            "minecraft:attributes": [
                {
                    "id": "spirit_flight:spirit_flight",
                    "attribute": "minecraft:flying_speed",
                    "amount": {
                        "type": "minecraft:linear",
                        "base": SPEED_PER_LEVEL,
                        "per_level_above_first": SPEED_PER_LEVEL,
                    },
                    "operation": "add_value",
                }
            ]
        },
    }


def _harnesses_item_tag() -> dict[str, Any]:
    return {
        "replace": False,
        "values": ["#minecraft:harnesses"],
    }


def _enchantment_tag() -> dict[str, Any]:
    return {
        "replace": False,
        "values": [ENCHANTMENT_ID],
    }


def _level_book_entry(level: int) -> dict[str, Any]:
    return {
        "type": "minecraft:item",
        "name": "minecraft:book",
        "functions": [
            {
                "function": "minecraft:set_enchantments",
                "enchantments": {ENCHANTMENT_ID: level},
            }
        ],
    }


def _level_harness_entry(color: str, level: int) -> dict[str, Any]:
    return {
        "type": "minecraft:item",
        "name": f"minecraft:{color}_harness",
        "functions": [
            {
                "function": "minecraft:set_enchantments",
                "enchantments": {ENCHANTMENT_ID: level},
            }
        ],
    }


def _book_1_5_table() -> dict[str, Any]:
    return {
        "type": "minecraft:empty",
        "pools": [
            {
                "rolls": 1.0,
                "bonus_rolls": 0.0,
                "entries": [
                    _level_book_entry(i) for i in range(1, MAX_ENCHANTMENT_LEVEL + 1)
                ],
            }
        ],
    }


def _harness_1_5_table() -> dict[str, Any]:
    entries = [
        _level_harness_entry(color, level)
        for color in HARNESS_COLORS
        for level in range(1, MAX_ENCHANTMENT_LEVEL + 1)
    ]
    return {
        "type": "minecraft:empty",
        "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": entries}],
    }


_BASTION_CHESTS = (
    "chests/bastion_bridge",
    "chests/bastion_hoglin_stable",
    "chests/bastion_other",
    "chests/bastion_treasure",
)


def _spirit_flight_pool() -> dict[str, Any]:
    return {
        "rolls": 1.0,
        "bonus_rolls": 0.0,
        "entries": [
            {"type": "minecraft:empty", "weight": 21},
            {
                "type": "minecraft:reference",
                "name": "spirit_flight:book_1_5",
                "weight": 6,
            },
            {
                "type": "minecraft:reference",
                "name": "spirit_flight:harness_1_5",
                "weight": 6,
            },
        ],
    }


def _merge_bastion_chest(fmt: tuple[int, int], chest_path: str) -> dict[str, Any]:
    """Load the embedded vanilla chest table for this format and append our pool."""
    p = _VANILLA_BASE / _vanilla_dir(fmt) / f"{chest_path}.json"
    table = json.loads(p.read_text())
    table["pools"].append(_spirit_flight_pool())
    return table


def _barter_book_entry(level: int) -> dict[str, Any]:
    return {
        "type": "minecraft:item",
        "name": "minecraft:book",
        "weight": 1,
        "functions": [
            {
                "function": "minecraft:set_enchantments",
                "enchantments": {ENCHANTMENT_ID: level},
            }
        ],
    }


def _barter_harness_reference() -> dict[str, Any]:
    return {
        "type": "minecraft:reference",
        "name": "spirit_flight:harness_1_5",
        "weight": 5,
    }


def _merge_piglin_bartering(fmt: tuple[int, int]) -> dict[str, Any]:
    """Load the embedded vanilla piglin_bartering table and add our entries."""
    p = _VANILLA_BASE / _vanilla_dir(fmt) / "gameplay/piglin_bartering.json"
    table = json.loads(p.read_text())
    assert len(table["pools"]) == 1, (
        f"unexpected barter pool count {len(table['pools'])} for format {fmt}; "
        f"piglin_bartering has historically been a single-pool table"
    )
    pool = table["pools"][0]
    pool["entries"].extend(
        [_barter_book_entry(i) for i in range(1, MAX_ENCHANTMENT_LEVEL + 1)]
        + [_barter_harness_reference()]
    )
    return table


def build(target: Target) -> dict[str, str | bytes]:
    fmt = target.pack_format
    if fmt < MIN_FORMAT:
        raise ValueError(
            f"Spirit Flight requires the happy ghast (format >= {MIN_FORMAT[0]}, "
            f"1.21.6); cannot build for format {fmt[0]}.",
        )

    files: dict[str, str | bytes] = {
        "pack.mcmeta": pack_mcmeta(fmt, DESCRIPTION),
        "data/spirit_flight/enchantment/spirit_flight.json": json_dumps(
            _enchantment_json()
        ),
        "data/spirit_flight/tags/item/harnesses.json": json_dumps(
            _harnesses_item_tag()
        ),
        "data/spirit_flight/tags/enchantment/spirit_flight.json": json_dumps(
            _enchantment_tag()
        ),
        "data/spirit_flight/loot_table/book_1_5.json": json_dumps(_book_1_5_table()),
        "data/spirit_flight/loot_table/harness_1_5.json": json_dumps(
            _harness_1_5_table()
        ),
    }

    icon = pack_png(PACK.name)
    if icon is not None:
        files["pack.png"] = icon

    for chest in _BASTION_CHESTS:
        files[f"data/minecraft/loot_table/{chest}.json"] = json_dumps(
            _merge_bastion_chest(fmt, chest)
        )

    files["data/minecraft/loot_table/gameplay/piglin_bartering.json"] = json_dumps(
        _merge_piglin_bartering(fmt)
    )

    return files


PACK = Pack(
    name="spirit-flight",
    display_name="Spirit-Flight",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
