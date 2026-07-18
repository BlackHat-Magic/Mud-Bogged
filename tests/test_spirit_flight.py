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
