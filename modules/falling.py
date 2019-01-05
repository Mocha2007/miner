def main(**kwargs) -> list:
	"""
	Enacts Gravity on fallers
	"""
	world = kwargs['world']
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if not block:
				continue
			if 'falling' not in block.tags:
				continue
			if not world[y+1][x]: # below
				world[y+1][x] = block
				world[y][x] = None
	return world
