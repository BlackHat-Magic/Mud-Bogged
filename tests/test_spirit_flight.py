from __future__ import annotations

import pytest

from datapacks.common import resolve_target
from datapacks.packs import PACKS


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
