from random import random
from common import Block, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Regrows leaves if both leaves and wood in VNN and only those and air are in VNN
	"""
	world = kwargs['world']
	# check for regrowth
	for y in range(len(world)):
		# wood_check_area = (world[y-1] if y else []) + world[y] + (world[y+1] if y+1 < len(world) else [])
		# if wood not in wood_check_area:
		# 	continue
		for x in range(len(world[0])):
			block = world[y][x]
			if not block and random() < 1/10:
				vnns = set(von_neumann_neighborhood((x, y), world))
				wood_in_hood = True in ['wood' in i.tags for i in vnns if type(i) == Block]
				if not wood_in_hood:
					continue
				leaves_in_hood = True in ['leaves' in i.tags for i in vnns if type(i) == Block]
				if not wood_in_hood:
					continue
				leaves = [i for i in vnns if type(i) == Block and 'leaves' in i.tags][0]
				only_alw_in_hood = False not in ['wood' in i.tags or 'leaves' in i.tags for i in vnns if type(i) == Block]
				if only_alw_in_hood:
					world[y][x] = leaves
	return world
