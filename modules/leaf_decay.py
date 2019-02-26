from random import random
from common import Block, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Regrows or decays leaves on wood under certain conditions
	"""
	world = kwargs['world']
	# check for decay
	for y, row in enumerate(world):
		for x, block in enumerate(row):
			if block and 'leaves' in block.tags and random() < 1/10:
				vnns = set(von_neumann_neighborhood((x, y), world))
				wood_in_hood = True in ['wood' in i.tags for i in vnns if isinstance(i, Block)]
				if not wood_in_hood:
					world[y][x] = None
	return world
