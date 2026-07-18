from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from datapacks.common import (
    pack_zip_name,
    versions_for_format,
    zip_pack,
)


def test_versions_for_format_multi():
    # (101, 1) maps to 26.1, 26.1.1, 26.1.2
    assert versions_for_format((101, 1)) == ["26.1", "26.1.1", "26.1.2"]


def test_versions_for_format_pair():
    # (48, 0) maps to both 1.21 and 1.21.1 (the bogged's earliest support)
    assert versions_for_format((48, 0)) == ["1.21", "1.21.1"]


def test_versions_for_format_single():
    # (61, 0) is unique to 1.21.4
    assert versions_for_format((61, 0)) == ["1.21.4"]


def test_versions_for_format_empty():
    # A format tuple that no release uses
    assert versions_for_format((999, 9)) == []


def test_pack_zip_name_range():
    name = pack_zip_name("bogged-drop-mud", (101, 1), project_version="0.1.0")
    assert name == "bogged-drop-mud_0.1.0+mc26.1-26.1.2.zip"


def test_pack_zip_name_single_version():
    name = pack_zip_name("bogged-drop-mud", (61, 0), project_version="0.1.0")
    assert name == "bogged-drop-mud_0.1.0+mc1.21.4.zip"


def test_pack_zip_name_raises_for_unknown_format():
    with pytest.raises(ValueError, match="no known Java Edition versions"):
        pack_zip_name("anything", (999, 9), project_version="0.1.0")


def test_pack_zip_name_uses_installed_version_when_not_overridden():
    # Without explicit project_version, the name should still parse as
    # <name>_<digits>.<digits>.<digits>+mc<range>.zip — proving
    # importlib.metadata / pyproject.toml fallback resolved a real version.
    name = pack_zip_name("bogged-drop-mud", (48, 0))
    pattern = r"^bogged-drop-mud_\d+\.\d+\.\d+\+mc[0-9.]+(-[0-9.]+)?\.zip$"
    assert re.match(pattern, name), name


def test_zip_pack_writes_all_files(tmp_path: Path):
    files: dict[str, str | bytes] = {
        "pack.mcmeta": '{"pack": {}}',
        "data/minecraft/loot_table/entities/zombie.json": "{}",
        "pack.png": b"\x89PNG\r\n\x1a\n",  # bytes content, not str
    }
    zip_path = tmp_path / "test.zip"
    zip_pack(zip_path, files)

    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        assert names == sorted(files.keys())  # zip_pack writes in sorted order
        # Verify content is preserved for each file
        for name, content in files.items():
            data = z.read(name)
            if isinstance(content, str):
                assert data == content.encode("utf-8")
            else:
                assert data == content


def test_zip_pack_overwrites_existing(tmp_path: Path):
    zip_path = tmp_path / "overwrite.zip"
    # First write
    zip_pack(zip_path, {"a.txt": "first"})
    assert zip_path.stat().st_size > 0
    # Second write — should replace, not append
    zip_pack(zip_path, {"a.txt": "second" * 100})
    assert "second" in zipfile.ZipFile(zip_path, "r").read("a.txt").decode("utf-8")


def test_zip_pack_is_deterministic(tmp_path: Path):
    """Same input → same byte output (reproducible builds)."""
    files = {"pack.mcmeta": "{}", "data/x.json": '{"a": 1}'}
    a = tmp_path / "a.zip"
    b = tmp_path / "b.zip"
    zip_pack(a, files)
    zip_pack(b, files)
    assert a.read_bytes() == b.read_bytes()


def test_cli_zip_flag(monkeypatch, tmp_path: Path):
    """End-to-end: `datapacks bogged-drop-mud -v 26.1.2 -z` produces the zip
    in the parent of the output directory with the expected name."""
    out = tmp_path / "Bogged-Drop-Mud"
    monkeypatch.setattr(
        "sys.argv",
        [
            "datapacks",
            "bogged-drop-mud",
            "-v",
            "26.1.2",
            "-o",
            str(out),
            "--zip",
        ],
    )
    from datapacks.main import main

    main()

    # Output directory built
    assert out.is_dir()
    assert (out / "pack.mcmeta").is_file()

    # Zip named per spec, in the parent of -o (i.e., tmp_path)
    expected_zip = tmp_path / "bogged-drop-mud_0.1.0+mc26.1-26.1.2.zip"
    assert expected_zip.is_file()
    # The zip contains the same file set as the directory
    with zipfile.ZipFile(expected_zip, "r") as z:
        assert z.namelist() == sorted(
            str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()
        )


def test_cli_short_zip_flag(monkeypatch, tmp_path: Path):
    """`-z` works the same as `--zip`."""
    out = tmp_path / "Husk-Drop-Sand"
    monkeypatch.setattr(
        "sys.argv",
        [
            "datapacks",
            "husk-drop-sand",
            "-v",
            "1.21.4",
            "-o",
            str(out),
            "-z",
        ],
    )
    from datapacks.main import main

    main()
    # 1.21.4 maps uniquely to format (61, 0) → single-version zip name
    expected_zip = tmp_path / "husk-drop-sand_0.1.0+mc1.21.4.zip"
    assert expected_zip.is_file()


def test_cli_without_zip_flag_produces_no_zip(monkeypatch, tmp_path: Path):
    """Without --zip, no zip file is created."""
    out = tmp_path / "Bogged-Drop-Mud"
    monkeypatch.setattr(
        "sys.argv",
        [
            "datapacks",
            "bogged-drop-mud",
            "-v",
            "26.1.2",
            "-o",
            str(out),
        ],
    )
    from datapacks.main import main

    main()
    assert out.is_dir()
    # No .zip files anywhere in tmp_path
    assert list(tmp_path.glob("*.zip")) == []
