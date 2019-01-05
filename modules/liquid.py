from random import choice


def main(**kwargs) -> list:
	"""
	Moves Liquids
	"""
	world = kwargs['world']
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if not block:
				continue
			if 'liquid' not in block.tags:
				continue
			if not world[y+1][x]: # below
				world[y+1][x] = block
				world[y][x] = None
				continue
			directions = [(0, 0)]
			if not world[y][x-1]: # left
				directions.append((-1, 0)) # x, y
			if not world[y][x+1]: # right
				directions.append((1, 0)) # x, y
			# move randomly
			dx, dy = choice(directions)
			world[y][x] = None
			world[y+dy][x+dx] = block
	return world
