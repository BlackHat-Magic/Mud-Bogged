from ..common import Pack
from . import bogged_drop_mud

PACKS: dict[str, Pack] = {
    bogged_drop_mud.PACK.name: bogged_drop_mud.PACK,
}

__all__ = ["PACKS", "Pack"]
