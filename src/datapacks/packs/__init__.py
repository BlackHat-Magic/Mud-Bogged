from ..common import Pack
from . import bogged_drop_mud, husk_drop_sand, spirit_flight, stray_drop_ice

PACKS: dict[str, Pack] = {
    bogged_drop_mud.PACK.name: bogged_drop_mud.PACK,
    husk_drop_sand.PACK.name: husk_drop_sand.PACK,
    spirit_flight.PACK.name: spirit_flight.PACK,
    stray_drop_ice.PACK.name: stray_drop_ice.PACK,
}

__all__ = ["PACKS", "Pack"]
