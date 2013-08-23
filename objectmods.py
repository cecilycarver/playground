import libtcodpy as libtcod
import map as maps
import draw as draw
import object as objects

enemy_attacks = ['taunts','scowls at','whines at','calls names at','throws a toy at','bites','smacks','yells at','screams at','scratches','pushes', 'eye-pokes']
player_attacks = ['taunt','scowl at','whine at','call names at','throw a toy at','bite','smack','yell at','scream at','scratch','push','eye-poke']

class Fighter:
	#combat-related properties and methods (monster, player, NPC).
	def __init__(self, hp, defense, power, on_death):
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.on_death = on_death

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
		
		#check for death. if there's a death function, call it
		if self.hp <= 0:
			function = self.on_death
			if function is not None:
				function(self.owner)
	
	def instakill(self):
		function = self.on_death
		if function is not None:
			function(self.owner, False)
	
	def attack(self, target):		
		#a simple formula for attack damage
		hit_power = libtcod.random_get_int(0, 0, self.power)
		hit_defense = libtcod.random_get_int(0, 0, target.fighter.defense)
		
		damage = hit_power - hit_defense
		if (self.owner.is_player):
			attack_word = libtcod.random_get_int(0, 0, len(player_attacks) - 1)
		else:
			attack_word = libtcod.random_get_int(0, 0, len(enemy_attacks) - 1)
 
		if damage > 0:
			#make the target take some damage
			if (self.owner.is_player):
				draw.message('You ' + player_attacks[attack_word] + ' the ' + target.name + '.')
			else:
				draw.message('The ' + self.owner.name + ' ' + enemy_attacks[attack_word] + ' you. It hurts.')
			target.fighter.take_damage(damage)			
			# notify other visible objects about attack
			if (self.owner.visible):
				self.owner.notify_visible('damage')			
		else:
			if (self.owner.is_player):
				draw.message('You ' + player_attacks[attack_word] + ' the ' + target.name + ' but it has no effect!')
			else:
				draw.message('The ' + self.owner.name + ' ' + enemy_attacks[attack_word] + ' you but it has no effect!')
		
			# notify other visible objects about attack
			if (self.owner.visible):
				self.owner.notify_visible('attack')
	
class BasicMonster:

	def __init__(self):
		self.hostile = True

	#AI for a basic monster.
	def take_turn(self, player):

		#a basic monster takes its turn. If you can see it, it can see you
		monster = self.owner
		if monster.visible and self.hostile:
			#move towards player if far away
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)

			#close enough, attack! (if the player is still alive.)
			elif monster.fighter and player.fighter.hp > 0:
				monster.fighter.attack(player)
		else:
			monster.move_random()
	
	def on_attack(self, attacker):
		return
	
	def on_damage(self, attacker):
		return
	
	def on_give(self):
		return
	
	def on_punish(self):
		draw.message('The ' + self.owner.name + ' calms down.')
		self.hostile = False

class SmartMonster(BasicMonster):
	#AI for a smart monster (doesn't attack if a Teacher is visible).
	def take_turn(self, player):

		#a basic monster takes its turn. If you can see it, it can see you
		monster = self.owner
		if monster.visible and self.hostile:
			#move towards player if far away
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)

			#close enough, attack! (if the player is still alive.)
			elif monster.fighter and player.fighter.hp > 0:
				#check for teachers
				if not self.check_teacher():
					monster.fighter.attack(player)
				else:
					draw.message('The smart bully glances at the teacher and holds back.')
		else:
			monster.move_random()

	def check_teacher(self):
		if self.owner.visible:
			for thing in objects.visible:
				if thing.name == 'teacher':
					return True
		return False
	
	def on_punish(self):
		return

class Mom: 
	def take_turn(self, player):
		myself = self.owner
		myself.move_random()
	
	def on_attack(self, attacker):
		return
	
	def on_damage(self, attacker):
		return
	
	def on_give(self):
		return
		
	def on_punish(self):
		return
		
class Teacher:
	def __init__(self):
		self.target = None
	
	#AI for a teacher - removes attacking children in his/her field of view.
	def take_turn(self, player):
		myself = self.owner
		if self.target is not None:
			# check if target is still a fighter
			if self.target.fighter is not None:
				# both teacher and target must be in FOV
				if myself.visible and self.target.visible:
					if myself.distance_to(self.target) >= 2:
						myself.move_towards(self.target.x, self.target.y)
					elif self.target.fighter and self.target.fighter.hp > 0:
						self.punish()
			else:
				# clear the target if it's been killed/neutralized already
				self.target = None
		else:
			xdir = libtcod.random_get_int(0,0,2) - 1
			ydir = libtcod.random_get_int(0,0,2) - 1
			myself.move_random()
	
	def punish(self):
		if self.target.is_player:
			draw.message('The teacher pulls you off the playground with a threat to call your parents.')
		else:
			draw.message('The teacher pulls the ' + self.target.name + ' off the playground.')
		self.target.fighter.instakill()
		self.target = None
		self.owner.notify_visible('punish')
	
	def on_attack(self, attacker):
		if self.target is None:
			draw.message('The teacher says to knock it off!')
	
	def on_damage(self, attacker):
		if self.target is None:
			draw.message('The teacher says, \'that\'s enough.\'')
			self.target = attacker
	
	def on_give(self):
		draw.message('The teacher says, \'I\'m so glad to see you sharing!\'', libtcod.green)
		objects.score += 10
		
	def on_punish(self):
		return
				
class Item:
	#an item that can be picked up and used.
	def __init__(self, type):
		self.type = type
	
	def pick_up(self):
		#add to the player's inventory and remove from the map
		if len(objects.inventory) >= 10:
			draw.message('Your pockets are full. You can\'t pick up the ' + self.owner.name + '.', libtcod.red)
		else:
			objects.inventory.append(self.owner)
			draw.message('You found ' + self.owner.name + '!', libtcod.green)
			
def player_death(player, leave_corpse=False):
	#the game ended!
	draw.message('You start to cry. Your mom appears and takes you away', libtcod.red)
	draw.message('You\'ve been pulled off the playground!', libtcod.red)
	player.alive = False
 
	#for added effect, transform the player into a corpse!
	if leave_corpse:
		player.char = '%'
		player.color = libtcod.dark_red
		
def monster_death(monster, leave_corpse=True):
	draw.message('the ' + monster.name.capitalize() + ' begins to cry.', libtcod.green)
	objects.score += (monster.fighter.power * 10)
	
	monster.fighter = None
	monster.ai = None
	
	# chance to leave a random item behind
	if libtcod.random_get_int(0, 0, 5) == 5:
		objects.generate_random_item(monster.x, monster.y)
	
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	if leave_corpse:
		monster.color = libtcod.dark_grey
		monster.blocks = False
		monster.fighter = None
		monster.ai = None
		monster.name = 'crying ' + monster.name
		monster.send_to_back()
	else:
		monster.kill()
	