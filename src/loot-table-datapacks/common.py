from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Pool:
	rolls: float = 1.0
	bonus_rolls: float = 0.0
	entries: list[PoolEntry]

@dataclass
class PoolEntry:
	name: str
	type: str	# TODO: can this be anything other than "minecraft:item"?
	name: str
	functions: list[Function]


# ----- Functions -----
@dataclass
class SetCount:
	function: Literal["minecraft:set_count"]
	count: Count
	add: bool


@dataclass
class EnchantCountIncrease:
	function: Literal["minecraft:enchant_count_increase"]
	enchantment: str
	count: Count


Function = SetCount | EnchantCountIncrease


@dataclass
class Uniform:
	type: Literal["minecraft:uniform"]
	min: float
	max: float


Count = Uniform
