import sys
import pygame
from json import load
from random import choice, randint, random
from time import time, sleep
from math import ceil
from importlib.machinery import SourceFileLoader
sys.path.append('./modules')
from common import Block, hills, is_exposed_to_sun, is_lit, noise, torch_range
from common import get_block_by_name as get_block_by_name2

version = 'a0.5'
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
	shadow_dist = 2
	message = message.replace('\t', ' '*4)
	lines = message.split('\n')
	for i in range(len(lines)):
		line = lines[i]
		message_to_render = font.render(line, 1, lighterColor)
		shadow = font.render(line, 1, (0, 0, 0))
		for j in range(shadow_dist):
			screen.blit(shadow, (coords[0]+j, coords[1]+i*font_size+j))
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
module_list = rules['modules']
modules = []
for module in module_list:
	modules.append(SourceFileLoader(module, 'modules/'+module+'.py').load_module())
world_gen = load(open('rules/'+rule+'/world.json', 'r'))
recipes = load(open('rules/'+rule+'/crafting.json', 'r'))
music_data = load(open('rules/'+rule+'/music.json', 'r'))
# todo bgm pygame.mixer.Sound('mus.wav').play(-1)
sfx_data = load(open('rules/'+rule+'/sfx.json', 'r'))

# now, create block classes!
blocks = set()


def get_block_by_name(block_name: str) -> Block:
	return get_block_by_name2(blocks, block_name)


def get_surface(drop_x: int) -> int:
	for i in range(len(world)):
		pointer_level = world[i]
		if pointer_level[drop_x]:
			return i-1


for name, data in block_list.items():
	blocks.add(Block(name, **data))
	log(0, name, 'block registered')

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
	elif gen['type'] == 'noise':
		selection_height = gen['height'][1] - gen['height'][0]
		noise_map = noise((size[0], selection_height))
		for dy in range(selection_height):
			for x in range(width):
				y = gen['height'][0] + dy
				if noise_map[y][x] < gen['chance']:
					world[y][x] = block
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
	elif gen['type'] == 'modulate':
		amplitude = gen['amplitude']
		center = gen['center']
		replace_top = get_block_by_name(gen['replace_top'])
		replace_bottom = get_block_by_name(gen['replace_bottom'])
		lift = hills(amplitude, center, size[0])
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
	if item in player['inventory']:
		assert 0 <= modification + player['inventory'][item]
		player['inventory'][item] += modification
		if player['inventory'][item] == 0:
			del player['inventory'][item]
	else:
		assert 0 <= modification
		player['inventory'][item] = modification


def mine(block_x: int, block_y: int) -> bool:
	if block_x < 0 or block_y < 0:
		return False
	b = world[block_y][block_x]
	if b:
		# unbreakable?
		if 'unminable' in b.tags:
			return False
		# todo tool level
		if b.prereq and b.prereq not in player['inventory']: # best i can do for now :(
			return False
		# add drops to inventory
		for item_name, amt in b.drops.simulate().items():
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
	if player['counters']['flying']*20 < fps:
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


def recipe_to_string(reagents: dict, products: dict) -> str:
	return ' + '.join([str(q)+' '+r for r, q in reagents.items()]) + ' -> ' + \
		   ' + '.join([str(q)+' '+p for p, q in products.items()])


def crafting():
	global selected
	# show version coords, inv
	t = []
	i = 0
	for recipe in recipes:
		if not set(recipe['reagents'].keys()) <= set(player['inventory'].keys()):
			continue
		available = True
		for reagent, quantity in recipe['reagents'].items():
			if player['inventory'][reagent] < quantity:
				available = False
				break
		if available:
			i += 1
			if selected == i:
				t.append('> ('+str(i)+') '+recipe_to_string(recipe['reagents'], recipe['products']))
				if pressed[pygame.K_x]: # crafting
					for reagent, quantity in recipe['reagents'].items():
						inv_edit(reagent, -quantity)
					for product, quantity in recipe['products'].items():
						inv_edit(product, quantity)
			else:
				t.append('('+str(i)+') '+recipe_to_string(recipe['reagents'], recipe['products']))

	text('\n'.join(t), (0, size[1]//2))
	# make sure cursor is visible
	if selected not in range(1, len(t)+1):
		selected = 1
	# move pointer up/down
	if pressed[pygame.K_UP]:
		selected -= 1
	if pressed[pygame.K_DOWN]:
		selected += 1


def build():
	global selected_build
	# make sure cursor is visible
	if selected_build not in range(len(player['inventory'])):
		selected_build = 0
	# move pointer up/down
	if pressed[pygame.K_LEFTBRACKET]:
		selected_build -= 1
	if pressed[pygame.K_RIGHTBRACKET]:
		selected_build += 1
	px, py = player['pos']
	directions = {
		pygame.K_i: (0, -1),
		pygame.K_j: (-1, 0),
		pygame.K_l: (1, 0),
		pygame.K_k: (0, 1),
	}
	for key, direction in directions.items():
		dx, dy = direction
		if pressed[key] and not world[py+dy][px+dx] and player['inventory']:
			block_name = list(player['inventory'].keys())[selected_build]
			block_block = get_block_by_name(block_name)
			if 'item' not in block_block.tags:
				# remove block from inventory
				inv_edit(block_name, -1)
				# place block in world
				world[py+dy][px+dx] = block_block


def sky(b: bool):
	global clouds
	global darkness
	day_length_in_minutes = 24
	time_rate = size[1]/(day_length_in_minutes*30*fps)
	adjusted_tick = tick * time_rate
	sun_x = size[0]-adjusted_tick % size[0]*2
	moon_x = (9/8*-adjusted_tick) % size[0]*2
	solar_eclipse = abs(sun_x - moon_x) < block_size
	is_day = -block_size < sun_x < size[0]
	is_moon = moon_x < size[0]
	is_dawn = size[0]-block_size < sun_x < size[0]
	is_dusk = -block_size < sun_x < 0
	# light level calculation
	background_light = 16
	light_sources = [background_light]
	if solar_eclipse:
		light_sources.append(255*abs(sun_x - moon_x)/block_size)
	elif is_dawn:
		light_sources.append(255*(size[0]-sun_x)/block_size)
	elif is_dusk:
		light_sources.append(255*(block_size+sun_x)/block_size)
	elif is_day:
		light_sources.append(255)
	if is_moon and not solar_eclipse:
		light_sources.append(128)
	# figure out lighting from sources
	torchlight = 255*is_lit(player['pos'], world)/torch_range
	light_sources.append(torchlight)
	if torchlight and is_exposed_to_sun(player['pos'], world):
		light_level = int(max(light_sources))
	elif torchlight:
		light_level = int(torchlight)
	else:
		light_level = background_light
	# main
	m = {
		True: (96, 192, 224) if is_day else (0, 0, 0),
		False: (0, 0, 0),
	}
	screen.fill(m[b])
	if not b:
		return None
	# todo sun/moon
	sun_coords = sun_x, size[1]//4, block_size, block_size
	moon_coords = moon_x, size[1]//4, block_size, block_size
	pygame.draw.rect(screen, (255, 255, 0), sun_coords)
	pygame.draw.rect(screen, (192, 192, 192), moon_coords) # todo vary brightness via sin with sun
	# clouds
	if not clouds:
		cloud_scale = 8
		cloud_size = size[0]//cloud_scale*2, size[1]//cloud_scale*2
		cloud_map = {
			True: (255, 255, 255, 192),
			False: (0, 0, 0, 0),
		}
		clouds = pygame.Surface((size[0]*2, size[1]*2), pygame.SRCALPHA)
		noisemap = noise(cloud_size)
		for x in range(cloud_size[0]):
			for y in range(cloud_size[1]):
				color = cloud_map[.6 < noisemap[y][x]]
				if cloud_scale == 1:
					clouds.set_at((x, y), color)
				else:
					rect = x*cloud_scale, y*cloud_scale, cloud_scale, cloud_scale
					pygame.draw.rect(clouds, color, rect)
	screen.blit(clouds, (0-player['pos'][0], 0-player['pos'][1]))
	# darkness
	darkness = pygame.Surface(size, pygame.SRCALPHA)
	darkness.fill((0, 0, 0, 255-light_level))


# display
fps = 30
tick = 0
block_size = rules['block_size']
relative_center = ceil(size[0]/2/block_size),  ceil(size[1]/2/block_size) # in-game coords, relative
selected = 1
selected_build = 0
clouds = None
frame_start_time = 0

while 1:
	game_events = set()
	if cfg['mini_mode']:
		absolute_rect = 0, 0, width, height
	else:
		absolute_rect = player['pos'][0]-relative_center[0], player['pos'][1]-relative_center[1], \
						player['pos'][0]+relative_center[0], player['pos'][1]+relative_center[1]  # in-game coords, absolute
	# sky or blank?
	sky(rules['sky'])
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
	# debug show brightness
	if cfg['show_brightness']:
		show_range = 8
		y_range = player['pos'][1]-show_range, player['pos'][1]+show_range+1
		x_range = player['pos'][0]-show_range, player['pos'][0]+show_range+1
		for y in range(*y_range):
			for x in range(*x_range):
				lighting = is_lit((x, y), world)
				rect = x * block_size - absolute_rect[0] * block_size, y * block_size - absolute_rect[
					1] * block_size, block_size, block_size
				pygame.draw.rect(screen, (lighting*31, lighting*31, 0), rect)
	# end of debug
	# character
	x, y = player['pos']
	if cfg['mini_mode']:
		pass
	else:
		rect = x*block_size-absolute_rect[0]*block_size, y*block_size-absolute_rect[1]*block_size, block_size, block_size
		pygame.draw.rect(screen, player['color'], rect)
	# darkness
	screen.blit(darkness, (0, 0))
	# show version coords, inv
	current_fps = str(int(1/(time()-frame_start_time)))
	frame_start_time = time()
	display_text = 'Miner '+version+'\nFPS: '+current_fps+'\ncoords: '+str(player['pos'])[1:-1]+'\nscore: '+str(score())+'\ninv:'
	for i, (name, quantity) in enumerate(player['inventory'].items()):
		if i == selected_build:
			build_info = '(b) '
		else:
			build_info = ''
		display_text += '\n\t'+build_info+name+': '+str(quantity)
	text(display_text, (0, 0))
	# gravity
	gravity()
	# events
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.QUIT:
			pygame.display.quit()
			pygame.quit()
			sys.exit()
	pressed = pygame.key.get_pressed()
	if pressed[pygame.K_w]: # up
		move_player(0, -1)
	if pressed[pygame.K_s]: # down
		move_player(0, 1)
	if pressed[pygame.K_a]: # left
		move_player(-1, 0)
	if pressed[pygame.K_d]: # right
		move_player(1, 0)
	if pressed[pygame.K_c]: # crafting
		crafting()
	else:
		selected = 1 # reset crafting cursor
	# let player build
	if rules['build']:
		build()
	# run modules
	for i, module in enumerate(modules):
		if tick % fps == i:
			world = module.main(world=world, blocks=blocks)
	refresh()
	# sfx
	sfx()
	sleep(1/fps)
	tick += 1
