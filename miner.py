import pygame
from json import load
from random import choice, randint, random
from sys import exit
from time import sleep
from math import ceil

# sound setup
pygame.mixer.init()
# pygame.mixer.Channel(1)


def play(filename: str):
	# pygame.mixer.Channel(1).queue(pygame.mixer.Sound(filename))
	pygame.mixer.Sound(filename).play()

# continue


def log(log_level: int, *message):
	levels = {
		0: 'info',
		1: 'warn',
		2: 'err',
	}
	print(levels[log_level]+':', *message)


def text(message: str, coords: (int, int)):
	message = message.replace('\t', ' '*4)
	lines = message.split('\n')
	for i in range(len(lines)):
		line = lines[i]
		message_to_render = font.render(line, 1, lighterColor)
		screen.blit(message_to_render, (coords[0], coords[1]+i*font_size))


cfg = load(open('settings.json', 'r'))

# pygame setup
pygame.init()
# size = 1280, 640
size = cfg['size']
screen = pygame.display.set_mode(size)
refresh = pygame.display.flip
font = pygame.font.SysFont(*cfg['font'])
font_size = cfg['font'][1]
icon = pygame.image.load('img/icon.png')
pygame.display.set_icon(icon)
pygame.display.set_caption('Miner')

# loading
screen.fill((0, 0, 0))
lighterColor = cfg['font_color']
text('Loading...', (size[0]//2, size[1]//2))
refresh()

# now, load the ruleset!!!
rule = cfg['rule']
block_list = load(open('rules/'+rule+'/blocks.json', 'r'))
rules = load(open('rules/'+rule+'/rules.json', 'r'))
world_gen = load(open('rules/'+rule+'/world.json', 'r'))
music_data = load(open('rules/'+rule+'/music.json', 'r'))
# todo bgm pygame.mixer.Sound('mus.wav').play(-1)
sfx_data = load(open('rules/'+rule+'/sfx.json', 'r'))

# now, create block classes!


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
		log(0, name, 'block registered')

	def __repr__(self):
		return self.name # temporary debug


blocks = set()


def get_block_by_name(block_name: str) -> Block:
	for b in blocks:
		if b.name == block_name:
			return b
	raise ValueError(block_name)


def get_surface(drop_x: int) -> int:
	for i in range(len(world)):
		pointer_level = world[i]
		if pointer_level[drop_x]:
			return i-1


for name, data in block_list.items():
	blocks.add(Block(name, **data))

# worldgen
width = rules['width']
height = rules['height']
world = []
for level in range(height):
	new_line = []
	for block in range(width):
		new_line.append(None)
	world.append(new_line)

for gen in world_gen:
	count = 0
	block = get_block_by_name(gen['block'])
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
		for y in range(*gen['height']):
			current_level = world[y]
			for x in range(width):
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
						# if not already ore (or None), make it ore!
						if world[cy][cx] in (block, None):
							continue
						world[cy][cx] = block
						vein_size -= 1
					count += 1
	elif gen['type'] == 'trunk':
		root = get_block_by_name(gen['root'])
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
		root = get_block_by_name(gen['root'])
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
	else:
		raise ValueError(gen['type'])
	log(0, count, gen['block'], gen['type'], 'generated')

# player setup

player = {
	'health': rules['player_hp'],
	'inventory': {},
	'pos': [width//2, get_surface(width//2)],
	'color': (255, 0, 0),
	'counters': {
		'flying': 0,
	}
}


def inv_edit(item: str, modification: int):
	# todo fix negative items
	if item in player['inventory']:
		player['inventory'][item] += modification
	else:
		player['inventory'][item] = modification


def mine(block_x: int, block_y: int) -> bool:
	if block_x < 0 or block_y < 0:
		return False
	b = world[block_y][block_x]
	if b:
		# unbreakable?
		if 'unbreakable' in b.tags:
			return False
		# todo tool level
		# add drops to inventory
		for item_name, amt in b.drops.items():
			inv_edit(item_name, amt)
			game_events.add('pickup')
		# delete block
		world[block_y][block_x] = None
		game_events.add('mine')
		return True
	return False


def move_player(d_x: int, d_y: int) -> bool:
	new_pos = [player['pos'][0]+d_x, player['pos'][1]+d_y]
	# print(new_pos)
	if new_pos[0] < 0 or width-1 < new_pos[0]:
		return False
	if new_pos[1] < 0 or world[new_pos[1]][new_pos[0]] is None:
		player['pos'] = new_pos
		return True
	# try to mine UNLESS flying
	if player['counters']['flying'] == 0 and world[new_pos[1]][new_pos[0]]:
		mine(*new_pos)
	return False


def gravity() -> bool:
	if player['counters']['flying']*8 < fps:
		player['counters']['flying'] += 1
		return False
	player['counters']['flying'] = 0
	if world[y+1][x] is None or y < -1:
		move_player(0, 1)
		return True
	return False


def score() -> int:
	return sum([get_block_by_name(i_name).value*i_quantity for i_name, i_quantity in player['inventory'].items()])


def sfx():
	[play('rules/'+rule+'/sfx/'+choice(sfx_data[e])) for e in game_events if e in sfx_data]


# display
fps = 20
tick = 0
block_size = rules['block_size']
relative_center = ceil(size[0]/2/block_size),  ceil(size[1]/2/block_size) # in-game coords, relative

while 1:
	game_events = set()
	if cfg['mini_mode']:
		absolute_rect = 0, 0, width, height
	else:
		absolute_rect = player['pos'][0]-relative_center[0], player['pos'][1]-relative_center[1], \
						player['pos'][0]+relative_center[0], player['pos'][1]+relative_center[1]  # in-game coords, absolute
	screen.fill((0, 0, 0))
	for y in range(absolute_rect[1], absolute_rect[3]):
		if y < 0 or height-1 < y:
			continue
		level = world[y]
		for x in range(absolute_rect[0], absolute_rect[2]):
			if x < 0 or width-1 < x:
				continue
			block = level[x]
			if block is None:
				continue
			if cfg['mini_mode']:
				screen.set_at((x, y), block.color)
			else:
				rect = x*block_size-absolute_rect[0]*block_size, y*block_size-absolute_rect[1]*block_size, block_size, block_size
				pygame.draw.rect(screen, block.color, rect)
	# character
	x, y = player['pos']
	if cfg['mini_mode']:
		pass
	else:
		rect = x*block_size-absolute_rect[0]*block_size, y*block_size-absolute_rect[1]*block_size, block_size, block_size
		pygame.draw.rect(screen, player['color'], rect)
	# show version coords, inv
	display_text = 'Miner a1\ncoords: '+str(player['pos'])+'\nscore: '+str(score())+'\ninv:'
	for name, quantity in player['inventory'].items():
		display_text += '\n\t'+name+': '+str(quantity)
	text(display_text, (0, 0))
	# gravity
	gravity()
	# events
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.QUIT:
			pygame.display.quit()
			pygame.quit()
			exit()
	pressed = pygame.key.get_pressed()
	if pressed[pygame.K_w]: # up
		move_player(0, -1)
	if pressed[pygame.K_s]: # down
		move_player(0, 1)
	if pressed[pygame.K_a]: # left
		move_player(-1, 0)
	if pressed[pygame.K_d]: # right
		move_player(1, 0)
	refresh()
	# sfx
	sfx()
	sleep(1/fps)
	tick += 1
