"""Spirit-Flight: a happy ghast harness enchantment (5 levels) scaling flying_speed."""

from __future__ import annotations

from pathlib import Path

from ..common import Pack, Target, pack_mcmeta, pack_png

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

_STATIC = Path(__file__).parent / "static"


def build(target: Target) -> dict[str, str | bytes]:
    fmt = target.pack_format
    if fmt < MIN_FORMAT:
        raise ValueError(
            f"Spirit Flight requires the happy ghast (format >= {MIN_FORMAT[0]}, "
            f"1.21.6); cannot build for format {fmt[0]}.",
        )

    files: dict[str, str | bytes] = {
        "pack.mcmeta": pack_mcmeta(fmt, DESCRIPTION),
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
