def main(**kwargs) -> list:
	"""
	Enacts Gravity on fallers
	"""
	world = kwargs['world']
	new_world = [list(i) for i in world]
	for y, row in enumerate(world):
		for x, block in enumerate(row):
			if not block:
				continue
			if 'falling' not in block.tags:
				continue
			if len(world) <= y+1:
				continue
			if not world[y+1][x]: # below
				new_world[y+1][x] = block
				new_world[y][x] = None
	return new_world
