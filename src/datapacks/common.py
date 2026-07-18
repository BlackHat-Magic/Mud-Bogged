from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# A datapack format is a (major, minor) pair. Minor is 0 for all formats before
# 1.21.9; from format 88 onward the minor version is significant and must be
# emitted in pack.mcmeta as [major, minor].
# Source: https://minecraft.wiki/w/Pack_format
PACK_FORMATS: dict[str, tuple[int, int]] = {
    # 1.13-1.14.4 (format 4) - datapacks introduced in 1.13
    "1.13": (4, 0),
    "1.13.1": (4, 0),
    "1.13.2": (4, 0),
    "1.14": (4, 0),
    "1.14.1": (4, 0),
    "1.14.2": (4, 0),
    "1.14.3": (4, 0),
    "1.14.4": (4, 0),
    # 1.15-1.16.1 (format 5)
    "1.15": (5, 0),
    "1.15.1": (5, 0),
    "1.15.2": (5, 0),
    "1.16": (5, 0),
    "1.16.1": (5, 0),
    # 1.16.2-1.16.5 (format 6)
    "1.16.2": (6, 0),
    "1.16.3": (6, 0),
    "1.16.4": (6, 0),
    "1.16.5": (6, 0),
    # 1.17-1.17.1 (format 7)
    "1.17": (7, 0),
    "1.17.1": (7, 0),
    # 1.18-1.18.1 (format 8)
    "1.18": (8, 0),
    "1.18.1": (8, 0),
    # 1.18.2 (format 9)
    "1.18.2": (9, 0),
    # 1.19-1.19.3 (format 10)
    "1.19": (10, 0),
    "1.19.1": (10, 0),
    "1.19.2": (10, 0),
    "1.19.3": (10, 0),
    # 1.19.4 (format 12)
    "1.19.4": (12, 0),
    # 1.20-1.20.1 (format 15)
    "1.20": (15, 0),
    "1.20.1": (15, 0),
    # 1.20.2 (format 18)
    "1.20.2": (18, 0),
    # 1.20.3-1.20.4 (format 26)
    "1.20.3": (26, 0),
    "1.20.4": (26, 0),
    # 1.20.5-1.20.6 (format 41)
    "1.20.5": (41, 0),
    "1.20.6": (41, 0),
    # 1.21-1.21.1 (format 48)
    "1.21": (48, 0),
    "1.21.1": (48, 0),
    # 1.21.2-1.21.3 (format 57)
    "1.21.2": (57, 0),
    "1.21.3": (57, 0),
    # 1.21.4 (format 61)
    "1.21.4": (61, 0),
    # 1.21.5 (format 71)
    "1.21.5": (71, 0),
    # 1.21.6 (format 80)
    "1.21.6": (80, 0),
    # 1.21.7-1.21.8 (format 81)
    "1.21.7": (81, 0),
    "1.21.8": (81, 0),
    # 1.21.9-1.21.10 (format 88)
    "1.21.9": (88, 0),
    "1.21.10": (88, 0),
    # 1.21.11 (format 94, minor 1)
    "1.21.11": (94, 1),
    # 26.1-26.1.2 (format 101, minor 1)
    "26.1": (101, 1),
    "26.1.1": (101, 1),
    "26.1.2": (101, 1),
    # 26.2 (format 107, minor 1)
    "26.2": (107, 1),
}

LATEST_VERSION = "26.2"

# Oldest datapack format this tooling emits. Datapacks were introduced in 1.13
# (pack_format 4); that is the floor for every pack built by this project.
# Individual packs may declare a higher `min_format` (e.g. the Bogged only exists
# from 1.21 onward).
MIN_SUPPORTED_FORMAT: tuple[int, int] = (4, 0)

# Format thresholds for the three version-sensitive transforms. Compared by
# major version only.
LOOT_TABLE_SINGULAR_FORMAT = 48  # 1.21: loot_tables -> loot_table
ENCHANTED_COUNT_INCREASE_FORMAT = (
    27  # 1.20.5: looting_enchant -> enchanted_count_increase
)
NEW_META_FORMAT = 82  # 1.21.9: pack_format -> min_format/max_format


@dataclass(frozen=True)
class Target:
    """A resolved build target: a Minecraft version and its pack format.

    `pack_format` drives pack.mcmeta. `version` is the canonical Java Edition
    release (e.g. "1.13.2", "1.21.11"); packs whose loot-table shape evolved
    independently of pack_format (notably the Husk, where pack_format 4 covers
    both the unprefixed 1.13 era and the prefixed 1.14 era) derive their content
    era from `version` rather than from the format number alone.
    """

    version: str
    pack_format: tuple[int, int]


@dataclass(frozen=True)
class Pack:
    """A distributable datapack this project can generate."""

    name: str
    display_name: str
    description: str
    min_format: tuple[int, int]
    build: Callable[[Target], dict[str, str | bytes]]


def resolve_target(version: str | None, fmt: str | None) -> Target:
    """Resolve a build target from a version string or an explicit pack format.

    If `fmt` is given, the version defaults to the latest release sharing that
    pack_format (so `-f 4` resolves to 1.14.4, the last format-4 release). This
    matters because some pack_format numbers span releases with differing
    loot-table content conventions (e.g. format 4 = both 1.13 and 1.14).
    """
    if fmt is not None:
        parsed = _parse_format(fmt)
        if parsed < MIN_SUPPORTED_FORMAT:
            raise ValueError(
                f"Datapack format {fmt} is not supported "
                f"(minimum is {MIN_SUPPORTED_FORMAT[0]}).",
            )
        resolved = _latest_version_for_format(parsed)
        if resolved is None:
            raise ValueError(
                f"No known Minecraft release uses pack format {fmt}.",
            )
        return Target(version=resolved, pack_format=parsed)

    version = LATEST_VERSION if version is None else version
    if version not in PACK_FORMATS:
        known = ", ".join(sorted(PACK_FORMATS, key=_version_sort_key, reverse=True))
        raise ValueError(f"Unknown version {version!r}. Known: {known}")
    return Target(version=version, pack_format=PACK_FORMATS[version])


def _latest_version_for_format(fmt: tuple[int, int]) -> str | None:
    """Newest release string that maps to the given (major, minor) pack format."""
    matches = [v for v, pf in PACK_FORMATS.items() if pf == fmt]
    if not matches:
        return None
    return max(matches, key=_version_sort_key)


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


def pack_png(pack_name: str) -> bytes | None:
    """Read a pack's icon from packs/static/<pack_name>.png, or None if absent."""
    p = Path(__file__).parent / "packs" / "static" / f"{pack_name}.png"
    return p.read_bytes() if p.is_file() else None


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


def versions_for_format(fmt: tuple[int, int]) -> list[str]:
    """All Java Edition release versions sharing the given pack format tuple,
    ordered earliest to latest."""
    return sorted(
        (v for v, pf in PACK_FORMATS.items() if pf == fmt),
        key=_version_sort_key,
    )


def _project_version() -> str:
    """The datapacks project's own version, from package metadata or pyproject.toml."""
    try:
        from importlib.metadata import version

        return version("datapacks")
    except Exception:
        import tomllib

        p = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with p.open("rb") as f:
            return tomllib.load(f)["project"]["version"]


def pack_zip_name(
    pack_name: str,
    fmt: tuple[int, int],
    *,
    project_version: str | None = None,
) -> str:
    """Standard distributable zip name: <pack-name>_<proj-ver>+mc<range>.zip.

    `<range>` is the earliest-to-latest Java Edition version range sharing the
    target's pack_format tuple. If only one version maps to the format, the
    range collapses to that single version (no `-` separator).

    Pass `project_version` explicitly in tests for determinism; production
    callers leave it None to use the installed package's version.
    """
    versions = versions_for_format(fmt)
    if not versions:
        raise ValueError(f"no known Java Edition versions use pack format {fmt}")
    range_str = versions[0] if len(versions) == 1 else f"{versions[0]}-{versions[-1]}"
    if project_version is None:
        project_version = _project_version()
    return f"{pack_name}_{project_version}+mc{range_str}.zip"


def zip_pack(zip_path: Path, files: dict[str, str | bytes]) -> None:
    """Write a generated pack's files to a zip archive at `zip_path`.

    Overwrites any existing file at that path. Zips from the in-memory files
    dict, not the on-disk output, so contents are byte-identical to what
    `write_pack` would emit. Uses a fixed date_time (1980-01-01) on every
    entry so the zip is byte-reproducible given the same input.
    """
    import zipfile

    if zip_path.exists():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files):
            content = files[rel]
            data = content.encode("utf-8") if isinstance(content, str) else content
            zi = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, data)
