from random import choice, randint, random, uniform
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


def get_block_by_name(blocks: set, block_name: str):
	if block_name is None:
		return None
	for b in blocks:
		if b.name == block_name:
			return b
	raise ValueError(block_name)


def is_exposed_to_sun(coord: (int, int), world) -> bool:
	coord = list(coord)
	while coord[1]:
		if coord[1] <= 0:
			return True
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


def world_generator(width: int, height: int, **kwargs) -> list:
	blocks = kwargs['blocks']
	world_gen = kwargs['world_gen']
	world = []
	for level in range(height):
		new_line = []
		for block in range(width):
			new_line.append(None)
		world.append(new_line)

	for gen in world_gen:
		count = 0
		block = get_block_by_name(blocks, gen['block'])
		if gen['type'] == 'zone':
			for y in range(*gen['height']):
				world[y] = [block]*width
				count += 1
		elif gen['type'] == 'ore':
			for y in range(*gen['height']):
				current_level = world[y]
				for x in range(width):
					if random() < gen['chance']:
						current_level[x] = block
						count += 1
		elif gen['type'] == 'vein':
			if gen['roots']:
				roots = [get_block_by_name(blocks, i) for i in gen['roots']]
			else:
				roots = blocks
			for y in range(*gen['height']):
				current_level = world[y]
				for x in range(width):
					# not root!
					if world[y][x] not in roots:
						continue
					if random() < gen['chance']:
						current_level[x] = block
						vein_size = gen['size']-1
						cx, cy = x, y
						while vein_size:
							if random() < .5: # x-axis movement
								cx += choice([-1, 1])
							else:
								cy += choice([-1, 1])
							# reset height if out of control
							if not gen['height'][0] <= cy < gen['height'][1]:
								cy = y
							# x-value outside world:
							if cx < 0 or width-1 < cx:
								continue
							# not root!
							if world[cy][cx] not in roots:
								continue
							# make it ore!
							world[cy][cx] = block
							vein_size -= 1
						count += 1
		elif gen['type'] == 'noise':
			selection_height = gen['height'][1] - gen['height'][0]
			noise_map = noise((width, selection_height))
			for dy in range(selection_height):
				for x in range(width):
					y = gen['height'][0] + dy
					if noise_map[y][x] < gen['chance']:
						world[y][x] = block
						count += 1
		elif gen['type'] == 'trunk':
			root = get_block_by_name(blocks, gen['root'])
			for y in range(height):
				current_level = world[y]
				if None not in current_level: # underground
					break
				if root not in list(world[y+1]): # no root
					continue
				for x in range(width):
					# no neighbors!
					if block in current_level[x-2:x+3]:
						continue
					# below isn't root!
					if world[y+1][x] != root:
						continue
					if random() < gen['chance']:
						current_level[x] = block
						vein_size = randint(*gen['size'])-1
						cy = y
						while vein_size:
							cy -= 1
							# stop if height out of control
							if cy < 0:
								break
							world[cy][x] = block
							vein_size -= 1
						count += 1
		elif gen['type'] == 'leaves':
			root = get_block_by_name(blocks, gen['root'])
			for y in range(height):
				current_level = world[y]
				if None not in current_level: # underground
					break
				if root not in current_level+world[y+1]: # no root
					continue
				for x in range(width):
					# refuse if block not NONE
					if current_level[x]:
						continue
					neighbors = current_level[x-1] if x-1 in range(len(current_level)) else None, \
								current_level[x+1] if x+1 in range(len(current_level)) else None, \
								world[y+1][x] if y+1 in range(len(world)) else None, \
								world[y-1][x] if y-1 in range(len(world)) else None
					# refuse neighbors other than ROOT or SELF or NONE
					if not set(neighbors) <= {None, block, root}:
						continue
					# refuse if no root neighbor
					if root not in neighbors:
						continue
					current_level[x] = block
					count += 1
		elif gen['type'] == 'modulate':
			amplitude = gen['amplitude']
			center = gen['center']
			replace_top = get_block_by_name(blocks, gen['replace_top'])
			replace_bottom = get_block_by_name(blocks, gen['replace_bottom'])
			lift = hills(amplitude, center, width)
			new_world = [] # IF SOMETHING IS BROKEN THIS IS WHY, MAY NEED TO BE A DEEP COPY
			for y in range(height):
				new_row = world[y].copy()
				for x in range(width):
					if y-lift[x] < 0:
						new_row[x] = replace_top
					elif y-lift[x] < height:
						new_row[x] = world[y-lift[x]][x]
					else:
						new_row[x] = replace_bottom
				new_world.append(new_row)
			world = new_world
		else:
			raise ValueError(gen['type'])
		log(0, count, gen['block'], gen['type'], 'generated')
	return world


def dist(a: tuple, b: tuple) -> float:
	return sum((i-j)**2 for i, j in zip(a, b))**.5
