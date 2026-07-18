"""Stray-Drop-Ice: make the Stray drop 0-2 Ice."""

from __future__ import annotations

from typing import Any

from ..common import Pack, Target, json_dumps, loot_table_dir, pack_mcmeta, pack_png

DESCRIPTION = "Make the Stray drop Ice (0-2)"

# The Stray has existed since 1.10 and datapacks since 1.13, so this pack can be
# built all the way back to format 4 (1.13).
MIN_FORMAT: tuple[int, int] = (4, 0)


# --------------------------------------------------------------------------- #
# Era predicates, keyed off the Java Edition *version* (not pack_format).
#
# Same rationale as the husk pack: pack_format 4 covers both the unprefixed
# 1.13 era and the prefixed 1.14 era.
#
# NOTE: the Stray's looting_enchant -> enchanted_count_increase transition
# occurs at 1.21 (format 48), NOT at 1.20.5 (format 27) like the husk and
# bogged. Vanilla simply did not regenerate the stray table at 1.20.5 -- the
# old function name still works there. Reproducing vanilla faithfully means
# using the name that vanilla actually used in each era, so this pack has its
# own threshold rather than sharing common.looting_function().
#
# Verified against vanilla stray loot tables fetched per release: 1.13.2,
# 1.14.4, 1.16.5, 1.17.1, 1.18.2, 1.19.4, 1.20.1, 1.20.5, 1.20.6, 1.21,
# 1.21.1, 1.21.11.
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


def _has_random_sequence(v: tuple[int, ...]) -> bool:
    """random_sequence field appears from 1.20 onward."""
    return v >= (1, 20)


def _new_looting(v: tuple[int, ...]) -> bool:
    """1.21+ use enchanted_count_increase + an enchantment field.

    NOTE: the Stray switched at 1.21, not 1.20.5 like the husk/bogged. Vanilla
    did not regenerate the stray table at 1.20.5 and kept looting_enchant there.
    """
    return v >= (1, 21)


def _uses_set_potion(v: tuple[int, ...]) -> bool:
    """1.17+ use set_potion instead of set_nbt for tipped arrows."""
    return v >= (1, 17)


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

    Used for the arrow, bone, and added ice pools, so the ice drop mirrors the
    era's own conventions exactly.
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


def _tipped_arrow_pool(v: tuple[int, ...]) -> dict[str, Any]:
    """Slowness tipped arrow: 0-1 + Looting bonus (limit 1), killed_by_player gated."""
    set_count: dict[str, Any] = {
        "function": _ns(v, "minecraft:set_count"),
        "count": _count(v, 0, 1, typed=True),
    }
    if _modern_pool(v):
        set_count["add"] = False

    looting: dict[str, Any] = {
        "function": _looting_fn(v),
        "count": _count(v, 0, 1, typed=_modern_pool(v)),
        "limit": 1,
    }
    if _new_looting(v):
        looting["enchantment"] = "minecraft:looting"

    if _uses_set_potion(v):
        potion_fn: dict[str, Any] = {
            "function": "minecraft:set_potion",
            "id": "minecraft:slowness",
        }
    else:
        potion_fn = {
            "function": _ns(v, "minecraft:set_nbt"),
            "tag": '{Potion:"minecraft:slowness"}',
        }

    entry: dict[str, Any] = {
        "type": _ns(v, "minecraft:item"),
        "name": "minecraft:tipped_arrow",
    }
    if v < (1, 14):
        entry["weight"] = 1
    entry["functions"] = [set_count, looting, potion_fn]

    pool = _rolls(v)
    pool["entries"] = [entry]
    pool["conditions"] = [{"condition": _ns(v, "minecraft:killed_by_player")}]
    return pool


def _loot_table(v: tuple[int, ...]) -> dict[str, Any]:
    pools: list[dict[str, Any]] = [
        _quantity_pool(v, "minecraft:arrow"),
        _quantity_pool(v, "minecraft:bone"),
        _quantity_pool(v, "minecraft:ice"),
        _tipped_arrow_pool(v),
    ]

    table: dict[str, Any] = {}
    if _prefixed(v):
        table["type"] = "minecraft:entity"
    table["pools"] = pools
    if _has_random_sequence(v):
        table["random_sequence"] = "minecraft:entities/stray"
    return table


# --------------------------------------------------------------------------- #
# Pack entry point
# --------------------------------------------------------------------------- #


def build(target: Target) -> dict[str, str | bytes]:
    fmt = target.pack_format
    if fmt < MIN_FORMAT:
        raise ValueError(
            f"The Stray pack targets format >= {MIN_FORMAT[0]} (1.13); "
            f"cannot build for format {fmt[0]}.",
        )

    v = _vkey(target.version)
    files: dict[str, str | bytes] = {
        "pack.mcmeta": pack_mcmeta(fmt, DESCRIPTION),
        f"data/minecraft/{loot_table_dir(fmt)}/entities/stray.json": json_dumps(
            _loot_table(v)
        ),
    }

    icon = pack_png(PACK.name)
    if icon is not None:
        files["pack.png"] = icon

    return files


PACK = Pack(
    name="stray-drop-ice",
    display_name="Stray-Drop-Ice",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
