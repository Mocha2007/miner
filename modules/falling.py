def main(**kwargs) -> list:
	"""
	Enacts Gravity on fallers
	"""
	world = kwargs['world']
	new_world = [list(i) for i in world]
	for y in range(len(world)):
		for x in range(len(world[0])):
			block = world[y][x]
			if not block:
				continue
			if 'falling' not in block.tags:
				continue
			if not world[y+1][x]: # below
				new_world[y+1][x] = block
				new_world[y][x] = None
	return new_world
