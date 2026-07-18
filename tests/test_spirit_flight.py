from __future__ import annotations

import json

import pytest

from datapacks.common import resolve_target
from datapacks.packs import PACKS
from datapacks.packs import spirit_flight as sf


def test_pack_registered():
    assert "spirit-flight" in PACKS


def test_pack_metadata():
    p = PACKS["spirit-flight"]
    assert p.display_name == "Spirit-Flight"
    assert p.min_format == (80, 0)


def test_pack_rejects_pre_1_21_6():
    p = PACKS["spirit-flight"]
    t = resolve_target("1.21.5", None)
    with pytest.raises(ValueError, match="format >= 80"):
        p.build(t)


def _build_files(version: str) -> dict[str, str | bytes]:
    t = resolve_target(version, None)
    return sf.build(t)


def test_enchantment_file_present():
    files = _build_files("1.21.6")
    assert "data/spirit_flight/enchantment/spirit_flight.json" in files
    e = json.loads(files["data/spirit_flight/enchantment/spirit_flight.json"])
    assert e["description"] == "Spirit Flight"
    assert e["weight"] == 2
    assert e["max_level"] == 5
    assert e["anvil_cost"] == 4
    assert e["slots"] == ["body"]
    assert e["supported_items"] == "#spirit_flight:harnesses"
    assert e["primary_items"] == "#spirit_flight:harnesses"
    # min_cost / max_cost shape
    assert e["min_cost"] == {"base": 15, "per_level_above_first": 10}
    assert e["max_cost"] == {"base": 40, "per_level_above_first": 10}


def test_enchantment_has_flying_speed_attribute_effect():
    files = _build_files("1.21.6")
    e = json.loads(files["data/spirit_flight/enchantment/spirit_flight.json"])
    assert set(e["effects"]) == {"minecraft:attributes"}
    attrs = e["effects"]["minecraft:attributes"]
    assert len(attrs) == 1
    a = attrs[0]
    assert a["attribute"] == "minecraft:flying_speed"
    assert a["operation"] == "add_value"
    assert a["amount"]["type"] == "minecraft:linear"
    assert a["amount"]["base"] == 0.0457
    assert a["amount"]["per_level_above_first"] == 0.0457


def test_harnesses_item_tag_present():
    files = _build_files("1.21.6")
    assert "data/spirit_flight/tags/item/harnesses_enchantable.json" in files
    t = json.loads(files["data/spirit_flight/tags/item/harnesses_enchantable.json"])
    assert "replace" in t and t["replace"] is False
    assert t["values"] == ["#minecraft:harnesses"]


def test_enchantment_tag_present():
    files = _build_files("1.21.6")
    assert "data/spirit_flight/tags/enchantment/spirit_flight.json" in files
    t = json.loads(files["data/spirit_flight/tags/enchantment/spirit_flight.json"])
    assert t["values"] == [sf.ENCHANTMENT_ID]


def test_book_1_5_subtable():
    files = _build_files("1.21.6")
    assert "data/spirit_flight/loot_table/book_1_5.json" in files
    t = json.loads(files["data/spirit_flight/loot_table/book_1_5.json"])
    entries = t["pools"][0]["entries"]
    assert len(entries) == 5
    for i, e in enumerate(entries, start=1):
        assert e["type"] == "minecraft:item"
        assert e["name"] == "minecraft:book"
        fns = e["functions"]
        assert len(fns) == 1
        assert fns[0]["function"] == "minecraft:set_enchantments"
        assert fns[0]["enchantments"] == {"spirit_flight:spirit_flight": i}


def test_harness_1_5_subtable_has_80_entries():
    files = _build_files("1.21.6")
    assert "data/spirit_flight/loot_table/harness_1_5.json" in files
    t = json.loads(files["data/spirit_flight/loot_table/harness_1_5.json"])
    entries = t["pools"][0]["entries"]
    assert len(entries) == 80  # 16 colors * 5 levels
    for e in entries:
        assert e["type"] == "minecraft:item"
        assert e["name"].endswith("_harness")
        lvl = e["functions"][0]["enchantments"]["spirit_flight:spirit_flight"]
        assert 1 <= lvl <= 5


def test_harness_subtable_covers_all_16_colors():
    files = _build_files("1.21.6")
    t = json.loads(files["data/spirit_flight/loot_table/harness_1_5.json"])
    names = {e["name"] for e in t["pools"][0]["entries"]}
    expected = {f"minecraft:{c}_harness" for c in sf.HARNESS_COLORS}
    assert names == expected


def test_harness_subtable_each_color_has_all_5_levels():
    files = _build_files("1.21.6")
    t = json.loads(files["data/spirit_flight/loot_table/harness_1_5.json"])
    seen = {c: set() for c in sf.HARNESS_COLORS}
    for e in t["pools"][0]["entries"]:
        color = e["name"].removeprefix("minecraft:").removesuffix("_harness")
        lvl = e["functions"][0]["enchantments"]["spirit_flight:spirit_flight"]
        seen[color].add(lvl)
    for color, levels in seen.items():
        assert levels == {1, 2, 3, 4, 5}, color


def test_bastion_chest_tables_have_extra_spirit_flight_pool():
    for ver in ("1.21.6", "1.21.11", "26.2"):
        files = _build_files(ver)
        for chest in (
            "bastion_bridge",
            "bastion_hoglin_stable",
            "bastion_other",
            "bastion_treasure",
        ):
            path = f"data/minecraft/loot_table/chests/{chest}.json"
            assert path in files, (ver, chest)
            t = json.loads(files[path])
            # The new pool is last, with the three expected entries
            new_pool = t["pools"][-1]
            entries = new_pool["entries"]
            assert len(entries) == 3
            assert entries[0] == {"type": "minecraft:empty", "weight": 21}
            assert entries[1] == {
                "type": "minecraft:reference",
                "name": "spirit_flight:book_1_5",
                "weight": 6,
            }
            assert entries[2] == {
                "type": "minecraft:reference",
                "name": "spirit_flight:harness_1_5",
                "weight": 6,
            }


def test_bastion_chest_original_pools_preserved():
    """All vanilla pools before the new one are preserved untouched."""
    for ver in ("1.21.6", "26.2"):
        files = _build_files(ver)
        out = json.loads(files["data/minecraft/loot_table/chests/bastion_bridge.json"])
        # vanilla bastion_bridge has 5 pools; we add 1 -> 6
        assert len(out["pools"]) == 6
        # random_sequence preserved
        assert out["random_sequence"] == "minecraft:chests/bastion_bridge"
        # type preserved
        assert out["type"] == "minecraft:chest"


def test_piglin_bartering_has_spirit_flight_entries():
    for ver in ("1.21.6", "1.21.11", "26.2"):
        files = _build_files(ver)
        path = "data/minecraft/loot_table/gameplay/piglin_bartering.json"
        assert path in files, ver
        t = json.loads(files[path])
        assert t["type"] == "minecraft:barter"
        entries = t["pools"][0]["entries"]
        # The 5 book entries (one per level) with weight 1 each
        book_entries = [
            e
            for e in entries
            if e.get("name") == "minecraft:book"
            and any(
                fn.get("function") == "minecraft:set_enchantments"
                and fn["enchantments"].get("spirit_flight:spirit_flight")
                in (1, 2, 3, 4, 5)
                for fn in e.get("functions", [])
            )
        ]
        assert len(book_entries) == 5
        levels = sorted(
            fn["enchantments"]["spirit_flight:spirit_flight"]
            for e in book_entries
            for fn in e.get("functions", [])
            if fn.get("function") == "minecraft:set_enchantments"
        )
        assert levels == [1, 2, 3, 4, 5], ver
        for e in book_entries:
            assert e["weight"] == 1
        # The 1 reference entry to spirit_flight:harness_1_5 with weight 5
        ref_entries = [
            e
            for e in entries
            if e.get("type") == "minecraft:reference"
            and e.get("name") == "spirit_flight:harness_1_5"
        ]
        assert len(ref_entries) == 1
        assert ref_entries[0]["weight"] == 5


def test_piglin_bartering_vanilla_entries_preserved():
    for ver in ("1.21.6", "26.2"):
        files = _build_files(ver)
        t = json.loads(
            files["data/minecraft/loot_table/gameplay/piglin_bartering.json"]
        )
        entries = t["pools"][0]["entries"]
        # Soul Speed book at weight 5 must still be present
        soul_book = [
            e
            for e in entries
            if e.get("name") == "minecraft:book"
            and any(
                fn.get("function") == "minecraft:enchant_randomly"
                and fn.get("options") == "minecraft:soul_speed"
                for fn in e.get("functions", [])
            )
        ]
        assert len(soul_book) == 1, ver
        assert soul_book[0]["weight"] == 5, ver
        # random_sequence preserved
        assert t["random_sequence"] == "minecraft:gameplay/piglin_bartering", ver


@pytest.mark.parametrize(
    "version",
    [
        "1.21.6",
        "1.21.8",
        "1.21.10",
        "1.21.11",
        "26.1.2",
        "26.2",
    ],
)
def test_builds_for_all_supported_versions(version):
    files = _build_files(version)
    required = [
        "pack.mcmeta",
        "data/spirit_flight/enchantment/spirit_flight.json",
        "data/spirit_flight/tags/item/harnesses_enchantable.json",
        "data/spirit_flight/tags/enchantment/spirit_flight.json",
        "data/spirit_flight/loot_table/book_1_5.json",
        "data/spirit_flight/loot_table/harness_1_5.json",
        "data/minecraft/loot_table/chests/bastion_bridge.json",
        "data/minecraft/loot_table/chests/bastion_hoglin_stable.json",
        "data/minecraft/loot_table/chests/bastion_other.json",
        "data/minecraft/loot_table/chests/bastion_treasure.json",
        "data/minecraft/loot_table/gameplay/piglin_bartering.json",
    ]
    for r in required:
        assert r in files, (version, r)
    for path, content in files.items():
        if path.endswith(".json"):
            json.loads(content)


def test_other_packs_still_build():
    """Adding Spirit Flight must not break the existing three packs."""
    for name, ver in [
        ("bogged-drop-mud", "1.21.1"),
        ("husk-drop-sand", "1.13.2"),
        ("stray-drop-ice", "1.21.11"),
    ]:
        p = PACKS[name]
        t = resolve_target(ver, None)
        files = p.build(t)
        assert "pack.mcmeta" in files, name
        for path, content in files.items():
            if path.endswith(".json"):
                json.loads(content)
