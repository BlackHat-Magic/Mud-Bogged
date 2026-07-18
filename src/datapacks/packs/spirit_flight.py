"""Spirit-Flight: a happy ghast harness enchantment (5 levels) scaling flying_speed."""

from __future__ import annotations

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


def _enchantment_json() -> dict[str, Any]:
    return {
        "description": "Spirit Flight",
        "supported_items": "#spirit_flight:harnesses",
        "primary_items": "#spirit_flight:harnesses",
        "weight": 2,
        "max_level": 5,
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
        "data/spirit_flight/tags/item/harnesses_enchantable.json": json_dumps(
            _harnesses_item_tag()
        ),
        "data/spirit_flight/tags/enchantment/spirit_flight.json": json_dumps(
            _enchantment_tag()
        ),
    }

    icon = pack_png(PACK.name)
    if icon is not None:
        files["pack.png"] = icon

    return files


PACK = Pack(
    name="spirit-flight",
    display_name="Spirit-Flight",
    description=DESCRIPTION,
    min_format=MIN_FORMAT,
    build=build,
)
