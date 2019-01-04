class Block:
	def __init__(self, block_name: str, **kwargs):
		self.name = block_name
		# drops
		self.drops = kwargs['drops'] if 'drops' in kwargs else {}
		# prereq
		self.prereq = kwargs['prereq'] if 'prereq' in kwargs else None
		# color
		self.color = tuple(kwargs['color']) if 'color' in kwargs else (255, 0, 255)
		# value
		self.value = kwargs['value'] if 'value' in kwargs else 0
		# tags
		self.tags = set(kwargs['tags']) if 'tags' in kwargs else set()

	def __repr__(self):
		return self.name # temporary debug


def get_block_by_name(blocks: set, block_name: str) -> Block:
	for b in blocks:
		if b.name == block_name:
			return b
	raise ValueError(block_name)


def is_exposed_to_sun(coord: (int, int), world) -> bool:
	coord = list(coord)
	while coord[1]:
		if world[coord[1]-1][coord[0]] is not None:
			return False
		coord[1] -= 1
	return True

def von_neumann_neighborhood(coord: (int, int), world: list) -> list:
	x, y = coord
	return world[y-1][x] if 0 < y else None, \
		   world[y][x-1] if 0 < x else None, \
		   world[y][x+1] if x+1 < len(world[0]) else None, \
		   world[y+1][x] if y+1 < len(world) else None # up, left, right, down

def moore_neighborhood(coord: (int, int), world: list) -> list:
	x, y = coord
	return von_neumann_neighborhood(coord, world) + ( \
		   world[y-1][x-1] if x > 0 < y else None, \
		   world[y-1][x+1] if 0 < y and x+1 < len(world[0]) else None, \
		   world[y+1][x-1] if 0 < x and y+1 < len(world) else None, \
		   world[y+1][x+1] if x+1 < len(world[0]) and y+1 < len(world) else None) # vn, ul, ur, dl, dr