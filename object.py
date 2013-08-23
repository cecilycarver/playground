import libtcodpy as libtcod
import draw as draw
import map as maps
import objectmods as mods
import math

# Constants
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

toy_names = ['a my little pony','a ninja turtle','a troll doll','some pogs','a toy cat','a plastic monkey','an elmo','a teddy ruxpin']
candy_names = ['pop rocks','jawbreakers','gummi bears','cheerios','goldfish','flintstones multivitamins','jelly tots','a juice box']

global player, things, visible, inventory, score, mom

#Object class
class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.alive = True
		self.talking = False
		self.is_player = False
		self.is_mom = False
		self.visible = False
		self.fighter = fighter
		if self.fighter:  #let the fighter component know who owns it
			self.fighter.owner = self
 
		self.ai = ai
		if self.ai:  #let the AI component know who owns it
			self.ai.owner = self
		
		self.item = item
		if self.item:
			self.item.owner = self
 
	def move(self, dx, dy):
		if not is_blocked(self.x + dx,self.y + dy):
			#move by the given amount
			self.x += dx
			self.y += dy
	
	def move_random(self):
		dx = libtcod.random_get_int(0,0,2) - 1
		dy = libtcod.random_get_int(0,0,2) - 1
		self.move(dx, dy)
	
	def draw(self):
		draw.draw_object(self)
 
	def clear(self):
		draw.clear_object(self)
		
	def move_towards(self, target_x, target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)
	 
		#normalize it to length 1 (preserving direction), then round it and
		#convert to integer so the movement is restricted to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		
		if not is_blocked(self.x + dx, self.y + dy):
			self.move(dx, dy)
		else:
			if (target_y > self.y) and not is_blocked(self.x, self.y + 1):
				self.move(0, 1)
			elif (target_y < self.y) and not is_blocked(self.x, self.y - 1):
				self.move(0, -1)
			elif (target_x > self.x) and not is_blocked(self.x + 1, self.y):
				self.move(1, 0)
			else:
				self.move(-1, 0)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)
			
	def send_to_back(self):
		#make this object be drawn first, so all others appear above it if they're in the same tile.
		global things
		things.remove(self)
		things.insert(0, self)

	def kill(self):
		#take this object out of the game
		global things
		things.remove(self)
	
	def notify_visible(self, action):
		#this is for notifying other visible objects about something that has happened in fov
		global visible
		
		if self.visible:
			for thing in visible:
				#you attacked something
				if thing.ai and action == 'attack' and thing.ai.on_attack:
					thing.ai.on_attack(self)
				#you attacked and damaged something
				if thing.ai and action == 'damage' and thing.ai.on_damage:
					thing.ai.on_damage(self)
				#you punished something
				if thing.ai and action == 'punish' and thing.ai.on_punish:
					thing.ai.on_punish()
				#you gave a toy to something
				if thing.ai and action == 'give' and thing.ai.on_give:
					thing.ai.on_give()

def init():
	global things, visible, inventory, counter, score
	
	things = []
	visible = []
	inventory = []
	counter = 0
	score = 0
					
def create_player(x, y):
	global player, things
	hitz = mods.Fighter(hp=10, defense=2, power=2, on_death=mods.player_death)
	player = Object(x, y, '@', 'player', libtcod.white, blocks=True, fighter=hitz)
	player.is_player = True
	draw.message('You hear there are wondrous toys to be found in the Drakalor playground. You\'ve heard there are some formidable bullies, too.')
	things.append(player)

def create_mom(x, y):
	mom_comp = mods.Mom()
	mom = Object(x, y, 'M', 'mom', libtcod.light_yellow, blocks=True, ai=mom_comp)
	mom.is_mom = True
	things.append(mom)
	
def generate_monsters_and_items():
	for room in maps.rooms:
		place_monsters(room)
		place_items(room)

def is_blocked(x, y):
    #first test the map tile
    if maps.map[x][y].blocked:
        return True
 
    #now check for any blocking objects
    for thing in things:
        if thing.blocks and thing.x == x and thing.y == y:
            return True
 
    return False

def get_target(dx, dy):
	#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy
 
	#try to find an attackable object there
	for thing in visible:
		if thing.x == x and thing.y == y and thing.ai:
			return thing

	return None		
	
def player_actions(dx, dy):
	target = get_target(dx, dy)
	
	#attack if target found, move otherwise
	if target is not None and target.fighter and not target.is_player:
		player.fighter.attack(target)
	elif target is not None and target.is_mom:
		talk_mom()
	else:
		player.move(dx, dy)
		draw.fov_recompute = True
	
def monster_actions():
	global player, things
	for thing in things:
		if thing.ai:
			thing.ai.take_turn(player)			
			
def add_toys_to_score():
	global inventory, score
	
	for thing in inventory:
		if thing.item and thing.item.type == 'toy':
			score += 20
			
def find_visible():
	global things
	del visible[:]
	for thing in things:
		if libtcod.map_is_in_fov(maps.fov_map, thing.x, thing.y):
			thing.visible = True
			visible.append(thing)
		else:
			thing.visible = False

def find_at_loc():
	global visible, player
	for thing in visible:
		if (thing.x == player.x and thing.y == player.y and not thing.is_player):
			if (thing.item):
				draw.message('You see ' + thing.name + ' lying here.')
			else:
				draw.message('You see a ' + thing.name + ' sitting here.') 
		
def talk_mom():
	global player
	draw.message('Your mom strokes your head.')
	draw.message('\"Looks like you\'ve been having fun! Are you ready to leave (y/n)?')
	player.talking = True
		
def collect_item():
	global things
	for thing in things:  #look for an item in the player's tile
		if thing.x == player.x and thing.y == player.y and thing.item:
			thing.item.pick_up()
			things.remove(thing)
			break
	#draw.message('You paw through the dirt but there\'s nothing to pick up.')

def eat_candy():
	global player, things, inventory
	for thing in inventory:
		if thing.item.type == 'candy':
			draw.message('You eat the ' + thing.name + '. You feel better.')
			player.fighter.hp += 1
			inventory.remove(thing)
			return
	
	draw.message('You have no candy to eat.')

#give toy to enemy in that direction	
def give_toy(x,y):
	global inventory, score
	target = get_target(x,y)
	
	if target is not None:
		if not target.fighter:
			draw.message('The ' + target.name + ' doesn\'t want it.')
		else:
			for thing in inventory:
				if thing.item.type == 'toy':
					draw.message('You give the ' + thing.name + ' to the ' + target.name + '.')
					if target.ai.hostile:
						draw.message('The ' + target.name + ' calms down.')
						score += 5
						target.ai.hostile = False
					else:
						draw.message('The ' + target.name + ' says \'thank you\'')
					inventory.remove(thing)
					return
			
			draw.message('You have no toys to give away.')	
	else:
		draw.message('There\'s no one to give a toy to.')
	
def place_monsters(room):
	#choose random number of monsters
	num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
 
	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
 
		if not is_blocked(x, y):
			i = libtcod.random_get_int(0, 0, 100)
			if i < 20:
				#create a teacher
				teacher_ai = mods.Teacher()
				monster = Object(x, y, 'T', 'teacher', libtcod.light_blue, blocks=True, ai=teacher_ai)
			elif i < 80:  #80% chance of getting a child
				#create a child
				child_fighter = mods.Fighter(hp=3, defense=0, power=1, on_death=mods.monster_death)
				child_ai = mods.BasicMonster()
				monster = Object(x, y, 't', 'toddler', libtcod.light_pink, blocks=True, fighter=child_fighter, ai=child_ai)
			elif i < 90:
				#create a bully
				bully_fighter = mods.Fighter(hp=5, defense=1, power=2, on_death=mods.monster_death)
				bully_ai = mods.BasicMonster()
				monster = Object(x, y, 'B', 'bully', libtcod.light_green, blocks=True, fighter=bully_fighter, ai=bully_ai)
			else:
				#create a smart bully
				bully_fighter = mods.Fighter(hp=5, defense=1, power=3, on_death=mods.monster_death)
				bully_ai = mods.SmartMonster()
				monster = Object(x, y, 'B', 'smart bully', libtcod.dark_green, blocks=True, fighter=bully_fighter, ai=bully_ai)				
			
			things.append(monster)	

# creates a random item at x,y
def generate_random_item(x, y):				
	item = None
	if libtcod.random_get_int(0,0,100) < 65:
		#create candy
		item_comp = mods.Item('candy')
		item = Object(x, y, '!', candy_names[libtcod.random_get_int(0,0,len(candy_names)) - 1], libtcod.violet, item=item_comp)
	else:
		#create toy
		item_comp = mods.Item('toy')
		item = Object(x, y, ':', toy_names[libtcod.random_get_int(0,0,len(toy_names)) - 1], libtcod.blue, item=item_comp)
		
	things.append(item)
	item.send_to_back()  #items appear below other objects
			
def place_items(room):
	#choose random number of items
	num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)

	for i in range(num_items):
		#choose random spot for this item
		x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			generate_random_item(x, y)