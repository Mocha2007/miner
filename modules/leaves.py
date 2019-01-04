from random import random
from common import get_block_by_name, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Regrows leaves on wood under certain conditions
	"""
	blocks = kwargs['blocks']
	world = kwargs['world']
	leaves = get_block_by_name(blocks, 'leaves')
	wood = get_block_by_name(blocks, 'wood')
	for y in range(len(world)):
		wood_check_area = (world[y-1] if y else []) + world[y] + (world[y+1] if y+1 < len(world) else [])
		if wood not in wood_check_area:
			continue
		for x in range(len(world[0])):
			block = world[y][x]
			vnns = set(von_neumann_neighborhood((x, y), world))
			if not block and random() < 1/10 and wood in vnns and vnns <= {None, leaves, wood}:
				world[y][x] = leaves
	return world
