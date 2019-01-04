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
