from random import random
from common import Block, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Regrows leaves if both leaves and wood in VNN and only those and air are in VNN
	"""
	world = kwargs['world']
	# check for regrowth
	for y, row in enumerate(world):
		# wood_check_area = (world[y-1] if y else []) + row + (world[y+1] if y+1 < len(world) else [])
		# if wood not in wood_check_area:
		# 	continue
		for x, block in enumerate(row):
			if not block and random() < 1/10:
				vnns = set(von_neumann_neighborhood((x, y), world))
				wood_in_hood = True in ['wood' in i.tags for i in vnns if isinstance(i, Block)]
				if not wood_in_hood:
					continue
				leaves_in_hood = True in ['leaves' in i.tags for i in vnns if isinstance(i, Block)]
				if not leaves_in_hood:
					continue
				leaves = [i for i in vnns if isinstance(i, Block) and 'leaves' in i.tags][0]
				only_alw_in_hood = False not in ['wood' in i.tags or 'leaves' in i.tags for i in vnns if isinstance(i, Block)]
				if only_alw_in_hood:
					world[y][x] = leaves
	return world
