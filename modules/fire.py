from random import random
from common import Block, von_neumann_neighborhood


def main(**kwargs) -> list:
	"""
	Turns flammable blocks 1/10 chance into fire if they're in the VNN of a fire_starter
	Deletes burning blocks 1/10 chance
	"""
	blocks = kwargs['blocks']
	world = kwargs['world']
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if not block or 1/10 < random():
				continue
			# BALEET FIRE
			if 'burning' in block.tags:
				world[y][x] = None
			# burn shit
			elif 'flammable' in block.tags:
				vnns = set(von_neumann_neighborhood((x, y), world))
				fire_starter_in_hood = True in ['fire_starter' in i.tags for i in vnns if type(i) == Block]
				if not fire_starter_in_hood:
					continue
				fire = [i for i in blocks if type(i) == Block and 'burning' in i.tags][0]
				world[y][x] = fire
	return world
