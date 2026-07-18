"""Husk-Drop-Sand: make the Husk drop 0-2 Sand."""

from __future__ import annotations

from typing import Any

from ..common import Pack, Target, json_dumps, loot_table_dir, pack_mcmeta, pack_png

DESCRIPTION = "Make the Husk drop Sand (0-2)"

# The Husk has existed since 1.10 and datapacks since 1.13, so this pack can be
# built all the way back to format 4 (1.13).
MIN_FORMAT: tuple[int, int] = (4, 0)


# --------------------------------------------------------------------------- #
# Era predicates, keyed off the Java Edition *version* (not pack_format).
#
# This is necessary because pack_format does not uniquely determine the loot
# table content shape: pack_format 4 covers both 1.13.x (unprefixed ids, no
# root `type`, integer counts, `weight` on entries) and 1.14.x (namespaced ids,
# root `type`, float counts with `type`, no `weight`). All other era transitions
# happen to align with a pack_format boundary, but resolving from the version
# string keeps the reasoning uniform and correct.
#
# Verified against vanilla husk loot tables fetched per release: 1.13.2,
# 1.14.4, 1.16.5, 1.17.1, 1.18.1, 1.18.2, 1.19.4, 1.20.1, 1.20.5, 1.21,
# 1.21.1, 1.21.9, 1.21.11.
# --------------------------------------------------------------------------- #


def _vkey(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def _prefixed(v: tuple[int, ...]) -> bool:
    """1.14+ use namespaced ids; 1.13 is the lone unprefixed era."""
    return v >= (1, 14)


def _ns(v: tuple[int, ...], name: str) -> str:
    """Strip the `minecraft:` prefix in 1.13."""
    return name if _prefixed(v) else name.removeprefix("minecraft:")


def _modern_pool(v: tuple[int, ...]) -> bool:
    """1.17+ use float rolls, bonus_rolls, and add:false on set_count."""
    return v >= (1, 17)


def _has_furnace_smelt(v: tuple[int, ...]) -> bool:
    """furnace_smelt on the potato entry appears from 1.17 onward."""
    return v >= (1, 17)


def _has_random_sequence(v: tuple[int, ...]) -> bool:
    """random_sequence field appears from 1.20 onward."""
    return v >= (1, 20)


def _new_looting(v: tuple[int, ...]) -> bool:
    """1.20.5+ use enchanted_count_increase + an enchantment field."""
    return v >= (1, 20, 5)


def _any_of_smelt(v: tuple[int, ...]) -> bool:
    """1.21+ gate furnace_smelt with any_of[is_on_fire, #smelts_loot]."""
    return v >= (1, 21)


def _camel_husk(v: tuple[int, ...]) -> bool:
    """1.21.11+ add a rabbit_foot pool for camel-ridden husks."""
    return v >= (1, 21, 11)


def _looting_fn(v: tuple[int, ...]) -> str:
    if _new_looting(v):
        return "minecraft:enchanted_count_increase"
    return _ns(v, "minecraft:looting_enchant")


def _count(v: tuple[int, ...], lo: float, hi: float, *, typed: bool) -> dict[str, Any]:
    """A uniform count range, shaped to match the targeted era.

    1.13: integer {min, max}, no `type`.
    1.14-1.16.5: float {min, max}, `type` only when `typed` (vanilla omits it
        on the looting-enchant count).
    1.17+: float {type, min, max}, `type` always present.
    """
    if v < (1, 14):
        return {"min": int(lo), "max": int(hi)}
    if v < (1, 17):
        d: dict[str, Any] = {"min": float(lo), "max": float(hi)}
        if typed:
            d["type"] = "minecraft:uniform"
        return d
    return {"type": "minecraft:uniform", "min": float(lo), "max": float(hi)}


def _rolls(v: tuple[int, ...]) -> dict[str, Any]:
    pool: dict[str, Any] = {"rolls": 1.0 if _modern_pool(v) else 1}
    if _modern_pool(v):
        pool["bonus_rolls"] = 0.0
    return pool


# --------------------------------------------------------------------------- #
# Pools
# --------------------------------------------------------------------------- #


def _quantity_pool(v: tuple[int, ...], item: str) -> dict[str, Any]:
    """A single-item pool: set_count 0-2 plus a Looting bonus 0-1.

    Used for both the rotten_flesh pool and the added sand pool, so the sand
    drop mirrors the era's own conventions exactly.
    """
    set_count: dict[str, Any] = {
        "function": _ns(v, "minecraft:set_count"),
        "count": _count(v, 0, 2, typed=True),
    }
    if _modern_pool(v):
        set_count["add"] = False

    looting: dict[str, Any] = {
        "function": _looting_fn(v),
        "count": _count(v, 0, 1, typed=_modern_pool(v)),
    }
    if _new_looting(v):
        looting["enchantment"] = "minecraft:looting"

    entry: dict[str, Any] = {
        "type": _ns(v, "minecraft:item"),
        "name": item,
    }
    if v < (1, 14):
        entry["weight"] = 1
    entry["functions"] = [set_count, looting]

    pool = _rolls(v)
    pool["entries"] = [entry]
    return pool


def _is_on_fire_cond(v: tuple[int, ...]) -> dict[str, Any]:
    return {
        "condition": _ns(v, "minecraft:entity_properties"),
        "entity": "this",
        "predicate": {"flags": {"is_on_fire": True}},
    }


def _smelts_loot_cond() -> dict[str, Any]:
    return {
        "condition": "minecraft:entity_properties",
        "entity": "direct_attacker",
        "predicate": {
            "equipment": {
                "mainhand": {
                    "predicates": {
                        "minecraft:enchantments": [
                            {"enchantments": "#minecraft:smelts_loot"}
                        ]
                    }
                }
            }
        },
    }


def _furnace_smelt_fn(v: tuple[int, ...]) -> dict[str, Any]:
    fn: dict[str, Any] = {"function": _ns(v, "minecraft:furnace_smelt")}
    if _any_of_smelt(v):
        fn["conditions"] = [
            {
                "condition": "minecraft:any_of",
                "terms": [_is_on_fire_cond(v), _smelts_loot_cond()],
            }
        ]
    else:
        fn["conditions"] = [_is_on_fire_cond(v)]
    return fn


def _rare_drop_condition(v: tuple[int, ...]) -> dict[str, Any]:
    if _new_looting(v):
        return {
            "condition": "minecraft:random_chance_with_enchanted_bonus",
            "unenchanted_chance": 0.025,
            "enchanted_chance": {
                "type": "minecraft:linear",
                "base": 0.035,
                "per_level_above_first": 0.01,
            },
            "enchantment": "minecraft:looting",
        }
    return {
        "condition": _ns(v, "minecraft:random_chance_with_looting"),
        "chance": 0.025,
        "looting_multiplier": 0.01,
    }


def _rare_drop_pool(v: tuple[int, ...]) -> dict[str, Any]:
    def plain(item: str) -> dict[str, Any]:
        e: dict[str, Any] = {"type": _ns(v, "minecraft:item"), "name": item}
        if v < (1, 14):
            e["weight"] = 1
        return e

    entries: list[dict[str, Any]] = [
        plain("minecraft:iron_ingot"),
        plain("minecraft:carrot"),
    ]

    potato: dict[str, Any] = {
        "type": _ns(v, "minecraft:item"),
        "name": "minecraft:potato",
    }
    if _has_furnace_smelt(v):
        potato["functions"] = [_furnace_smelt_fn(v)]
    if v < (1, 14):
        potato["weight"] = 1
    entries.append(potato)

    pool = _rolls(v)
    pool["entries"] = entries
    pool["conditions"] = [
        {"condition": _ns(v, "minecraft:killed_by_player")},
        _rare_drop_condition(v),
    ]
    return pool


def _camel_husk_pool() -> dict[str, Any]:
    return {
        "rolls": 1.0,
        "bonus_rolls": 0.0,
        "entries": [
            {
                "type": "minecraft:item",
                "name": "minecraft:rabbit_foot",
                "conditions": [
                    {
                        "condition": "minecraft:entity_properties",
                        "entity": "this",
                        "predicate": {"vehicle": {"type": "minecraft:camel_husk"}},
                    }
                ],
                "functions": [
                    {
                        "function": "minecraft:set_count",
                        "count": {
                            "type": "minecraft:uniform",
                            "min": 0.0,
                            "max": 1.0,
                        },
                        "add": False,
                    },
                    {
                        "function": "minecraft:enchanted_count_increase",
                        "enchantment": "minecraft:looting",
                        "count": {
                            "type": "minecraft:uniform",
                            "min": 0.0,
                            "max": 1.0,
                        },
                    },
                ],
            }
        ],
    }


def _loot_table(v: tuple[int, ...]) -> dict[str, Any]:
    pools: list[dict[str, Any]] = [
        _quantity_pool(v, "minecraft:rotten_flesh"),
        _quantity_pool(v, "minecraft:sand"),
    ]
    if _camel_husk(v):
        pools.append(_camel_husk_pool())
    pools.append(_rare_drop_pool(v))

    table: dict[str, Any] = {}
    if _prefixed(v):
        table["type"] = "minecraft:entity"
    table["pools"] = pools
    if _has_random_sequence(v):
        table["random_sequence"] = "minecraft:entities/husk"
    return table


# --------------------------------------------------------------------------- #
# Pack entry point
# --------------------------------------------------------------------------- #


def build(target: Target) -> dict[str, str | bytes]:
    fmt = target.pack_format
    if fmt < MIN_FORMAT:
        raise ValueError(
            f"The Husk pack targets format >= {MIN_FORMAT[0]} (1.13); "
            f"cannot build for format {fmt[0]}.",
        )

    v = _vkey(target.version)
    files: dict[str, str | bytes] = {
        "pack.mcmeta": pack_mcmeta(fmt, DESCRIPTION),
        f"data/minecraft/{loot_table_dir(fmt)}/entities/husk.json": json_dumps(
            _loot_table(v)
        ),
    }

    icon = pack_png(PACK.name)
    if icon is not None:
        files["pack.png"] = icon

    return files


PACK = Pack(
    name="husk-drop-sand",
    display_name="Husk-Drop-Sand",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
