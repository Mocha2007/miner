import sys
import pygame
from json import load
from random import choice
from time import time, sleep
from math import ceil
from importlib.machinery import SourceFileLoader
sys.path.append('./modules')
from common import Block, dist, hills, is_exposed_to_sun, is_lit, log, noise, torch_range, von_neumann_neighborhood, world_generator
from common import get_block_by_name as get_block_by_name2

version = 'a0.8'
# sound setup
pygame.mixer.init()
# pygame.mixer.Channel(1)


def play(filename: str):
	# pygame.mixer.Channel(1).queue(pygame.mixer.Sound(filename))
	pygame.mixer.Sound(filename).play()


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


def get_block_by_name(block_name: str) -> Block:
	return get_block_by_name2(blocks, block_name)


def get_surface(drop_x: int) -> int:
	for i in range(len(world)):
		pointer_level = world[i]
		if pointer_level[drop_x]:
			return i-1
	return -1


# load blocks
def load_blockpack(blockpack_name: str) -> set:
	blocks_ = set()
	block_list = load(open('rules/' + blockpack_name + '/blocks.json', 'r'))
	for block_name, data in block_list.items():
		if block_name == 'import':
			for new_blockpack in data:
				blocks_ = blocks_.union(load_blockpack(new_blockpack))
			continue
		blocks_.add(Block(block_name, **data))
		log(0, block_name, 'block registered')
	return blocks_


blocks = load_blockpack(rule)

# worldgen
width = rules['width']
height = rules['height']
world = world_generator(width, height, world_gen=world_gen, blocks=blocks)

# player setup
if rules['powder_like']:
	start_pos = [width//2, height//2]
else:
	start_pos = [width//2, get_surface(width//2)]

player = {
	'health': rules['player_hp'],
	'inventory': {},
	'pos': start_pos,
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
		if not rules['powder_like']:
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
	if height <= new_pos[1]:
		return False
	if new_pos[1] < 0 or world[new_pos[1]][new_pos[0]] is None:
		player['pos'] = new_pos
		return True
	# maybe it's a liquid?
	if 'liquid' in world[new_pos[1]][new_pos[0]].tags:
		player['pos'] = new_pos
		return True
	# try to mine UNLESS flying
	if player['counters']['flying'] == 0 and world[new_pos[1]][new_pos[0]]:
		mine(*new_pos)
	return False


def gravity() -> bool:
	if rules['powder_like']:
		return False
	if player['counters']['flying']*20 < fps:
		player['counters']['flying'] += 1
		return False
	player['counters']['flying'] = 0
	if height <= y+1:
		return False
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
		for reagent, r_quantity in recipe['reagents'].items():
			if player['inventory'][reagent] < r_quantity:
				available = False
				break
		if available:
			i += 1
			if selected == i:
				t.append('> ('+str(i)+') '+recipe_to_string(recipe['reagents'], recipe['products']))
				if pressed[pygame.K_x]: # crafting
					for reagent, r_quantity in recipe['reagents'].items():
						inv_edit(reagent, -r_quantity)
					for product, r_quantity in recipe['products'].items():
						inv_edit(product, r_quantity)
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
	max_build_dist = 3
	mouse_coords = get_coords_at_mouse()
	mouse_x, mouse_y = mouse_coords
	mouse_wants_to_build = pygame.mouse.get_pressed()[2] == 1
	if not rules['powder_like']:
		mouse_distance_good = dist(mouse_coords, player['pos']) <= max_build_dist
		if not mouse_distance_good:
			return None
		if set(von_neumann_neighborhood(mouse_coords, world)) == {None}:
			return None
	mouse_on_map = (0 <= mouse_x < len(world[0])) and (0 <= mouse_y < len(world))
	if mouse_on_map and mouse_wants_to_build and player['inventory'] and not world[mouse_y][mouse_x]:
		block_name = list(player['inventory'].keys())[selected_build]
		block_block = get_block_by_name(block_name)
		if 'item' not in block_block.tags:
			# remove block from inventory
			if not rules['powder_like']:
				inv_edit(block_name, -1)
			# place block in world
			world[mouse_y][mouse_x] = block_block


def sky(b: bool):
	if not b:
		return screen.fill((0, 0, 0))
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
	if 0 <= player['pos'][1]:
		torchlight = 255*is_lit(player['pos'], world)/torch_range
	else:
		torchlight = 255
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
	# sun/moon
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
					cloud_rect = x*cloud_scale, y*cloud_scale, cloud_scale, cloud_scale
					pygame.draw.rect(clouds, color, cloud_rect)
	screen.blit(clouds, (0-player['pos'][0], 0-player['pos'][1]))
	# darkness
	darkness = pygame.Surface(size, pygame.SRCALPHA)
	darkness.fill((0, 0, 0, 255-light_level))


def get_coords_at_mouse() -> (int, int):
	mouse_x, mouse_y = pygame.mouse.get_pos()
	block_x, block_y = absolute_rect[0] + mouse_x // block_size, absolute_rect[1] + mouse_y // block_size
	return block_x, block_y


def is_point_on_map(coords: (int, int)) -> bool:
	return coords[0] in range(width) and coords[1] in range(height)


# display
fps = 20
tick = 0
block_size = rules['block_size']
relative_center = ceil(size[0]/2/block_size),  ceil(size[1]/2/block_size) # in-game coords, relative
selected = 1
selected_build = 0
clouds = None
frame_start_time = 0
# creative shit
if rules['powder_like']:
	for block in blocks:
		player['inventory'][block.name] = 1

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
	if not (cfg['mini_mode'] or rules['powder_like']):
		rect = x*block_size-absolute_rect[0]*block_size, y*block_size-absolute_rect[1]*block_size, block_size, block_size
		pygame.draw.rect(screen, player['color'], rect)
	# darkness
	if rules['sky']:
		screen.blit(darkness, (0, 0))
	# show version coords, inv
	current_fps = str(int(1/(time()-frame_start_time)))
	frame_start_time = time()
	display_text = 'Miner '+version+'\nFPS: '+current_fps+'\ncoords: '+str(player['pos'])[1:-1]+'\nscore: ' + \
				   str(score())+'\ninv:'
	for i, (name, quantity) in enumerate(player['inventory'].items()):
		if i == selected_build:
			build_info = '(b) '
		else:
			build_info = ''
		display_text += '\n\t'+build_info+name+': '+str(quantity)
	text(display_text, (0, 0))
	# mouseover
	mc = get_coords_at_mouse()
	if is_point_on_map(mc):
		mouse_block = str(world[mc[1]][mc[0]]).title()
		if mouse_block == 'None':
			mouse_block = 'Air'
	else:
		mouse_block = 'Void'
	text_coords = pygame.mouse.get_pos()
	text_coords = text_coords[0]+10, text_coords[1]+10
	text(mouse_block, text_coords)
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
	if pressed[pygame.K_c]: # crafting
		crafting()
	if pressed[pygame.K_ESCAPE]: # exit
		exit()
	else:
		selected = 1 # reset crafting cursor
	# let player build
	if rules['build']:
		build()
	# run modules
	for i, module in enumerate(modules):
		if tick % fps == i:
			# module_start_time = time()
			world = module.main(world=world, blocks=blocks)
			# log(0, module, 'took', time()-module_start_time)
	refresh()
	# sfx
	sfx()
	sleep(.5/fps)
	tick += 1
