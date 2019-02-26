from random import random
from common import Block, is_exposed_to_sun, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Grows grass on dirt exposed to light randomly 1/200 chance per tick
	"""
	world = kwargs['world']
	for y, row in enumerate(world):
		for x, block in enumerate(row):
			if not block:
				continue
			if 'dirt' not in block.tags:
				continue
			if 1/10 < random():
				continue
			vnns = set(von_neumann_neighborhood((x, y), world))
			grass_in_hood = True in ['grass' in i.tags for i in vnns if isinstance(i, Block)]
			if not grass_in_hood:
				continue
			grass = [i for i in vnns if isinstance(i, Block) and 'grass' in i.tags][0]
			if is_exposed_to_sun((x, y), world):
				world[y][x] = grass
	return world
