import pygame
from json import load


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
world = load(open('rules/'+rule+'/world.json', 'r'))

# now, create block classes!


class Block:
	def __init__(self, name: str, **kwargs):
		self.name = name
		# drops
		self.drops = kwargs['drops'] if 'drops' in kwargs else {}
		# prereq
		self.prereq = kwargs['prereq'] if 'prereq' in kwargs else None
		# color
		self.color = tuple(kwargs['color']) if 'color' in kwargs else (255, 0, 255)
		# value
		self.value = kwargs['value'] if 'value' in kwargs else 0
		log(0, name, 'block created')


blocks = set()

for name, data in block_list.items():
	blocks.add(Block(name, **data))

# todo: worldgen
# todo: display
