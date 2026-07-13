from ..common import Pack
from . import bogged_drop_mud, husk_drop_sand

PACKS: dict[str, Pack] = {
    bogged_drop_mud.PACK.name: bogged_drop_mud.PACK,
    husk_drop_sand.PACK.name: husk_drop_sand.PACK,
}

__all__ = ["PACKS", "Pack"]
