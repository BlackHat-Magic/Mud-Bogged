from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from datapacks.common import (
    pack_zip_name,
    resolve_target,
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


def test_versions_for_format_format_4_spans_both_eras():
    # Format 4 spans 1.13.x AND 1.14.x with a content-era break in between.
    assert versions_for_format((4, 0)) == [
        "1.13",
        "1.13.1",
        "1.13.2",
        "1.14",
        "1.14.1",
        "1.14.2",
        "1.14.3",
        "1.14.4",
    ]


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


def test_pack_zip_name_ambiguous_format_without_version_uses_full_range():
    """When a format is ambiguous and no version is supplied, pack_zip_name
    falls back to the full release list (the legacy behaviour for callers
    that don't disambiguate). This mirrors what the CLI does when invoked
    before resolve_target has had a chance to refuse — but resolve_target
    normally blocks `-f 4` alone first, so this path is rare. Documented
    regardless so it doesn't silently change."""
    name = pack_zip_name("husk-drop-sand", (4, 0), project_version="0.1.0")
    assert name == "husk-drop-sand_0.1.0+mc1.13-1.14.4.zip"


def test_pack_zip_name_ambiguous_format_with_version_before_boundary():
    """For format 4 with version=1.13 (pre-boundary), the range is capped
    at the era the chosen release belongs to: 1.13-1.13.2, NOT 1.13-1.14.4."""
    name = pack_zip_name(
        "husk-drop-sand", (4, 0), version="1.13", project_version="0.1.0"
    )
    assert name == "husk-drop-sand_0.1.0+mc1.13-1.13.2.zip"


def test_pack_zip_name_ambiguous_format_with_version_after_boundary():
    """For format 4 with version=1.14 (post-boundary), the range is capped at
    1.14-1.14.4."""
    name = pack_zip_name(
        "husk-drop-sand", (4, 0), version="1.14", project_version="0.1.0"
    )
    assert name == "husk-drop-sand_0.1.0+mc1.14-1.14.4.zip"


def test_pack_zip_name_ambiguous_format_with_version_at_last_before_boundary():
    """version=1.13.2 (the last pre-boundary release) lands in the 1.13 era."""
    name = pack_zip_name(
        "husk-drop-sand", (4, 0), version="1.13.2", project_version="0.1.0"
    )
    assert name == "husk-drop-sand_0.1.0+mc1.13-1.13.2.zip"


def test_pack_zip_name_ambiguous_format_with_version_at_first_after_boundary():
    """version=1.14 (the first post-boundary release) lands in the 1.14 era."""
    name = pack_zip_name(
        "husk-drop-sand", (4, 0), version="1.14", project_version="0.1.0"
    )
    assert name == "husk-drop-sand_0.1.0+mc1.14-1.14.4.zip"


def test_resolve_target_f_without_v_for_ambiguous_format_refuses():
    """`-f 4` alone must refuse to silently pick an era, with a message that
    points the user at -v as the fix."""
    with pytest.raises(ValueError, match=r"content-era boundary.*-v"):
        resolve_target(version=None, fmt="4")


def test_resolve_target_f_with_v_for_ambiguous_format_uses_version_era():
    """`-f 4 -v 1.13` resolves cleanly to 1.13's content era."""
    t = resolve_target("1.13", "4")
    assert t.pack_format == (4, 0)
    assert t.version == "1.13"


def test_resolve_target_v_alone_for_ambiguous_release_works():
    """`-v 1.13` alone (no -f) resolves normally."""
    t = resolve_target("1.13", None)
    assert t.pack_format == (4, 0)
    assert t.version == "1.13"


def test_resolve_target_f_with_mismatching_v_raises():
    """`-f 4 -v 1.21` should error: 1.21 uses format 48, not 4."""
    with pytest.raises(ValueError, match=r"uses pack format 48, not 4"):
        resolve_target("1.21", "4")


def test_resolve_target_unambiguous_format_with_f_alone_still_picks_latest():
    """Sanity: the new ambiguity handling only kicks in for AMBIGUOUS_FORMATS.
    Non-ambiguous formats (e.g. format 48) still pick the latest sharing the
    format, as before."""
    t = resolve_target(None, "48")
    assert t.pack_format == (48, 0)
    assert t.version == "1.21.1"  # latest of 1.21, 1.21.1


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


def test_cli_ambiguous_format_alone_errors_with_helpful_message(
    monkeypatch, capsys, tmp_path: Path
):
    """`datapacks husk-drop-sand -f 4` must print a message telling the user
    to disambiguate with -v, and exit non-zero."""
    out = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["datapacks", "husk-drop-sand", "-f", "4", "-o", str(out)],
    )
    from datapacks.main import main

    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    # argparse parser.error writes to stderr
    assert "1.13.2" in captured.err or "1.13.2" in captured.out
    assert "1.14" in captured.err or "1.14" in captured.out
    assert "-v" in captured.err or "-v" in captured.out


def test_cli_ambiguous_format_with_v_builds_and_zips_correct_era(
    monkeypatch, tmp_path: Path
):
    """`datapacks husk-drop-sand -v 1.13 -z` builds the 1.13-era pack and
    names the zip with the era-capped range `1.13-1.13.2`."""
    out = tmp_path / "Husk-Drop-Sand"
    monkeypatch.setattr(
        "sys.argv",
        ["datapacks", "husk-drop-sand", "-v", "1.13", "-o", str(out), "-z"],
    )
    from datapacks.main import main

    main()
    expected_zip = tmp_path / "husk-drop-sand_0.1.0+mc1.13-1.13.2.zip"
    assert expected_zip.is_file()


def test_cli_ambiguous_format_with_v_after_boundary_builds_correct_era(
    monkeypatch, tmp_path: Path
):
    """`datapacks husk-drop-sand -v 1.14 -z` names the zip with `1.14-1.14.4`."""
    out = tmp_path / "Husk-Drop-Sand"
    monkeypatch.setattr(
        "sys.argv",
        ["datapacks", "husk-drop-sand", "-v", "1.14", "-o", str(out), "-z"],
    )
    from datapacks.main import main

    main()
    expected_zip = tmp_path / "husk-drop-sand_0.1.0+mc1.14-1.14.4.zip"
    assert expected_zip.is_file()
