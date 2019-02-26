from random import choice


def main(**kwargs) -> list:
	"""
	Moves Liquids
	"""
	world = kwargs['world']
	for y, row in enumerate(world):
		widths = range(len(world[0]))
		for x, block in enumerate(row):
			if not block:
				continue
			if 'liquid' not in block.tags:
				continue
			if len(world) <= y+1:
				continue
			if not world[y+1][x]: # below
				world[y+1][x] = block
				world[y][x] = None
				continue
			directions = [(0, 0)]
			if x-1 in widths and not row[x-1]: # left
				directions.append((-1, 0)) # x, y
			if x+1 in widths and not row[x+1]: # right
				directions.append((1, 0)) # x, y
			# move randomly
			dx, dy = choice(directions)
			world[y][x] = None
			world[y+dy][x+dx] = block
	return world
