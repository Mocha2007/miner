from random import random
from common import get_block_by_name


def is_exposed_to_sun(coord: (int, int), world) -> bool:
	coord = list(coord)
	while coord[1]:
		if world[coord[1]-1][coord[0]] is not None:
			return False
		coord[1] -= 1
	return True


def main(**kwargs) -> list:
	"""
	Grows grass on dirt exposed to light randomly 1/200 chance per tick
	"""
	blocks = kwargs['blocks']
	world = kwargs['world']
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if block and block.name == 'dirt' and random() < 1/200 and is_exposed_to_sun((x, y), world):
				world[y][x] = get_block_by_name(blocks, 'grass')
	return world
