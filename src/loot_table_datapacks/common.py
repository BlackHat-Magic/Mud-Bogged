from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# A datapack format is a (major, minor) pair. Minor is 0 for all formats before
# 1.21.9; from format 88 onward the minor version is significant and must be
# emitted in pack.mcmeta as [major, minor].
# Source: https://minecraft.wiki/w/Pack_format
PACK_FORMATS: dict[str, tuple[int, int]] = {
    "1.20.5": (41, 0),
    "1.20.6": (41, 0),
    "1.21": (48, 0),
    "1.21.1": (48, 0),
    "1.21.2": (57, 0),
    "1.21.3": (57, 0),
    "1.21.4": (61, 0),
    "1.21.5": (71, 0),
    "1.21.6": (80, 0),
    "1.21.7": (81, 0),
    "1.21.8": (81, 0),
    "1.21.9": (88, 0),
    "1.21.10": (88, 0),
    "1.21.11": (94, 1),
    "26.1": (101, 1),
    "26.1.1": (101, 1),
    "26.1.2": (101, 1),
    "26.2": (107, 1),
}

LATEST_VERSION = "26.2"

# Oldest datapack format this tooling emits. Below this the loot-table folder
# was plural (`loot_tables`) and the looting function was `looting_enchant`; the
# generator handles both, but versions older than 1.20.5 predate the datapack
# shape this project targets.
MIN_SUPPORTED_FORMAT: tuple[int, int] = (41, 0)

# Format thresholds for the three version-sensitive transforms. Compared by
# major version only.
LOOT_TABLE_SINGULAR_FORMAT = 48  # 1.21: loot_tables -> loot_table
ENCHANTED_COUNT_INCREASE_FORMAT = (
    27  # 1.20.5: looting_enchant -> enchanted_count_increase
)
NEW_META_FORMAT = 82  # 1.21.9: pack_format -> min_format/max_format


@dataclass(frozen=True)
class Pack:
    """A distributable datapack this project can generate."""

    name: str
    display_name: str
    description: str
    min_format: tuple[int, int]
    build: Callable[[tuple[int, int]], dict[str, str | bytes]]


def resolve_format(version: str | None, fmt: str | None) -> tuple[int, int]:
    """Resolve a target datapack format from a version string or explicit format."""
    if fmt is not None:
        parsed = _parse_format(fmt)
        if parsed < MIN_SUPPORTED_FORMAT:
            raise ValueError(
                f"Datapack format {fmt} is not supported "
                f"(minimum is {MIN_SUPPORTED_FORMAT[0]}).",
            )
        return parsed

    version = LATEST_VERSION if version is None else version
    if version not in PACK_FORMATS:
        known = ", ".join(sorted(PACK_FORMATS, key=_version_sort_key, reverse=True))
        raise ValueError(f"Unknown version {version!r}. Known: {known}")
    return PACK_FORMATS[version]


def _parse_format(fmt: str) -> tuple[int, int]:
    """Parse a pack format string like '48', '94.1', or '[94,1]'."""
    s = fmt.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p for p in s.replace(",", ".").split(".") if p != ""]
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    return (major, minor)


def _version_sort_key(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def loot_table_dir(fmt: tuple[int, int]) -> str:
    """Folder name for loot tables in the given format."""
    return "loot_table" if fmt[0] >= LOOT_TABLE_SINGULAR_FORMAT else "loot_tables"


def looting_function(fmt: tuple[int, int]) -> str:
    """Namespaced id of the Looting-scaling function for the given format."""
    return (
        "minecraft:enchanted_count_increase"
        if fmt[0] >= ENCHANTED_COUNT_INCREASE_FORMAT
        else "minecraft:looting_enchant"
    )


def _meta_format_value(fmt: tuple[int, int]) -> int | list[int]:
    """min_format/max_format may be a single int (= [major, 0]) or [major, minor]."""
    return [fmt[0], fmt[1]] if fmt[1] != 0 else fmt[0]


def pack_mcmeta(fmt: tuple[int, int], description: str) -> str:
    """Render pack.mcmeta valid for the given format."""
    pack: dict[str, Any] = {"description": description}
    if fmt[0] < NEW_META_FORMAT:
        pack["pack_format"] = fmt[0]
    else:
        # As of 1.21.9 (format 82) pack_format is optional/removed in favour of
        # min_format/max_format, which may be a single int (= [major, 0]) or
        # [major, minor] when the minor version is significant.
        pack["min_format"] = _meta_format_value(fmt)
        pack["max_format"] = _meta_format_value(fmt)
    return json_dumps({"pack": pack})


def json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def write_pack(out: Path, files: dict[str, str | bytes]) -> None:
    """Write a generated pack to `out`, replacing any existing pack there."""
    import shutil

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
