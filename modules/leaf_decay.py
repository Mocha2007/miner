from random import random
from common import get_block_by_name, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Regrows or decays leaves on wood under certain conditions
	"""
	blocks = kwargs['blocks']
	world = kwargs['world']
	leaves = get_block_by_name(blocks, 'leaves')
	wood = get_block_by_name(blocks, 'wood')
	# check for decay
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if block == leaves and random() < 1/10:
				vnns = set(von_neumann_neighborhood((x, y), world))
				if wood not in vnns:
					world[y][x] = None
	return world
