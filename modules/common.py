from random import choice, random, seed, uniform
from json import dump, load


class Block:
	def __init__(self, block_name: str, **kwargs):
		self.name = block_name
		# drops
		self.drops = Drops(self, kwargs['drops'] if 'drops' in kwargs else {})
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


class Drops:
	def __init__(self, block: Block, drops):
		if type(drops) == dict:
			self.drops = drops
		elif type(drops) == int:
			self.drops = {block.name: {'probability': 1, 'range': [drops, drops+1]}}
		elif type(drops) == float:
			assert 0 <= drops <= 1
			self.drops = {block.name: {'probability': drops, 'range': [1, 2]}}
		else:
			raise TypeError

	def simulate(self) -> dict:
		drops = {}
		for drop, data in self.drops.items():
			probability = data['probability']
			drop_range = range(*data['range'])
			if random() < probability:
				drops[drop] = choice(drop_range)
		return drops


def get_block_by_name(blocks: set, block_name: str) -> Block:
	if block_name is None:
		return None
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


def von_neumann_neighborhood(coord: (int, int), world: list) -> tuple:
	x, y = coord
	return world[y-1][x] if 0 < y else None, \
		   world[y][x-1] if 0 < x else None, \
		   world[y][x+1] if x+1 < len(world[0]) else None, \
		   world[y+1][x] if y+1 < len(world) else None # up, left, right, down


def vnn2(coord: (int, int), world: list) -> tuple:
	return tuple(i for i in von_neumann_neighborhood(coord, world) if i)


def moore_neighborhood(coord: (int, int), world: list) -> tuple:
	x, y = coord
	return von_neumann_neighborhood(coord, world) + (
		   world[y-1][x-1] if x > 0 < y else None,
		   world[y-1][x+1] if 0 < y and x+1 < len(world[0]) else None,
		   world[y+1][x-1] if 0 < x and y+1 < len(world) else None,
		   world[y+1][x+1] if x+1 < len(world[0]) and y+1 < len(world) else None) # vn, ul, ur, dl, dr


def mean(values) -> float:
	return sum(values)/len(values)


def noise(size: (int, int)) -> list:
	smoothing = 4
	grid = []
	# initial generation
	for y in range(size[1]):
		row = []
		for x in range(size[0]):
			# seed((x, y))
			point = uniform(0, 1)
			row.append(point)
		grid.append(row)
	# smoothing
	for _ in range(smoothing):
		new_grid = [list(i) for i in grid] # try to delete ANY links
		for y in range(size[1]):
			for x in range(size[0]):
				vnn = vnn2((x, y), grid)
				try:
					point = mean(vnn)
				except TypeError: # todo
					continue
				new_grid[y][x] = point
		grid = new_grid
	return grid


def noise1d(size: int) -> list:
	smoothing = 8
	# initial generation
	grid = [uniform(0, 1) for _ in range(size)]
	# smoothing
	for _ in range(smoothing):
		new_grid = grid.copy()
		for x in range(size):
			vnn = vnn2((x, 0), [grid])
			point = mean(vnn)
			new_grid[x] = point
		grid = new_grid
	return grid


def hills(amplitude: float, center: float, size: int) -> list:
	max_slope = 1
	# initial generation
	lift = [int((i-center)*amplitude) for i in noise1d(size)]
	# smoothing
	is_problem = True
	while is_problem:
		for x in range(1, size):
			if max_slope < abs(lift[x] - lift[x-1]):
				if lift[x-1] < lift[x]:
					lift[x] -= 1
				else:
					lift[x] += 1
		# check for problem
		for x in range(1, size):
			if max_slope < abs(lift[x] - lift[x-1]):
				break
			if x+1 == size:
				is_problem = False
		if is_problem:
			continue
		# now, check if amplitude needs to be increased
		if max(lift) < amplitude:
			scalar = amplitude / max(lift)
			lift = [round(scalar*i) for i in lift]
			is_problem = True
	return lift


torch_range = 16


def is_lit(coord: (int, int), world) -> int:
	# DO THIS FOR FASTER COMPUTATION
	block = world[coord[1]][coord[0]]
	if block:
		if 'light_source' in block.tags:
			return torch_range
		else:
			return 0
	elif is_exposed_to_sun(coord, world):
		return torch_range
	# MAIN FUNCTION
	x_slice = max(0, coord[0]-torch_range), min(coord[0]+torch_range, len(world[0]))
	y_slice = max(0, coord[1]-torch_range), min(coord[1]+torch_range, len(world))
	# create matrix
	lit = []
	for y in range(*y_slice):
		new_line = []
		for x in range(*x_slice):
			block = world[y][x]
			is_torch = block and 'light_source' in block.tags # torches
			if block:
				new_line.append(torch_range if is_torch else 0)
				continue
			iets = is_exposed_to_sun((x, y), world) # sunlight
			new_line.append(torch_range if iets else 0)
		lit.append(new_line)
	# simulate lighting
	for i in range(torch_range):
		new_lit = [list(i) for i in lit]
		for y, level in enumerate(lit):
			for x, _ in enumerate(level):
				if world[y][x]: # inside of blocks is dark
					continue
				if lit[y][x]: # don't recompute
					continue
				vnn = [i for i in von_neumann_neighborhood((x, y), lit) if i]
				if len(vnn) == 0:
					continue
				brightest_neighbor = max(vnn)
				if brightest_neighbor:
					if torch_range == x == y: # should be the center
						return brightest_neighbor-1
					new_lit[y][x] = brightest_neighbor-1
		lit = new_lit
	return lit[torch_range][torch_range]


def save_game(world: list, player: dict, filename: str):
	dump({'world': world, 'player': player}, filename)


def load_game(filename: str) -> (list, dict):
	data = load(open(filename, 'r'))
	return data['world'], data['player']


def log(log_level: int, *message):
	levels = {
		0: 'info',
		1: 'warn',
		2: 'err',
	}
	print(levels[log_level]+':', *message)
