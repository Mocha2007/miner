import pygame
from json import load
from random import random
from sys import exit
from time import sleep


def log(level: int, *message):
	levels = {
		0: 'info',
		1: 'warn',
		2: 'err',
	}
	print(levels[level]+':', *message)


cfg = load(open('settings.json', 'r'))
# rules = set(load(open('rules.json', 'r')))

# pygame setup
pygame.init()
# size = 1280, 640
size = cfg['size']
screen = pygame.display.set_mode(size)
refresh = pygame.display.flip
font = pygame.font.SysFont(*cfg['font'])
icon = pygame.image.load('img/icon.png')
pygame.display.set_icon(icon)
pygame.display.set_caption('Miner')

# loading
screen.fill((0, 0, 0))
lighterColor = cfg['font_color']
loading = font.render('Loading...', 1, lighterColor)
screen.blit(loading, (size[0]//2, size[1]//2))
refresh()

# now, load the ruleset!!!
rule = cfg['rule']
block_list = load(open('rules/'+rule+'/blocks.json', 'r'))
rules = load(open('rules/'+rule+'/rules.json', 'r'))
world_gen = load(open('rules/'+rule+'/world.json', 'r'))

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
		log(0, name, 'block registered')


blocks = set()


def get_block_by_name(block_name: str) -> Block:
	for block in blocks:
		if block.name == block_name:
			return block
	raise ValueError(block_name)


for name, data in block_list.items():
	blocks.add(Block(name, **data))

# todo: worldgen
width = rules['width']
height = rules['height']
world = [[None]*width]*height

for gen in world_gen:
	count = 0
	if gen['type'] == 'zone':
		for y in range(*gen['height']):
			world[y] = [get_block_by_name(gen['block'])]*width
			count += 1
	elif gen['type'] == 'ore':
		for y in range(*gen['height']):
			current_level = world[y]
			for x in range(width):
				if random() < gen['chance']:
					current_level[x] = get_block_by_name(gen['block'])
					count += 1
	else:
		raise ValueError(gen['type'])
	log(0, count, gen['block'], gen['type'], 'generated')

# todo: display

block_size = rules['block_size']
screen.fill((0, 0, 0))
for y in range(height):
	level = world[y]
	for x in range(width):
		block = level[x]
		if block is None:
			continue
		if cfg['mini_mode']:
			screen.set_at((x, y), block.color)
		else:
			rect = x*block_size, y*block_size, block_size, block_size
			pygame.draw.rect(screen, block.color, rect)
	refresh()

while 1:
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.QUIT:
			pygame.display.quit()
			pygame.quit()
			exit()
	sleep(1/20)
