import libtcodpy as libtcod
import map as maps
import object as objects
import draw
import shelve

# constants
LIMIT_FPS = 22

#globals
global game_state, player_action

# initialization
draw.init_console()
libtcod.sys_set_fps(LIMIT_FPS)
game_state = 'playing'
player_action = None

instructions = ['','Press arrow keys or numpad to move.','','c: pick up candy and toys.','e: eat candy to regain health', 'g: give a toy to another child','esc: quit','','If the teacher sees you, you\'ll get in trouble.','','Giving away your toys calms your enemies down.']
credits = ['\"Playground\" was created by Cecily Carver', 'during the Dames Making Games Toronto game jam,','\"Mother, May I?\"','','The program is heavily based on example code', 'by Joao F. Henriques (a.k.a. Jotaf).','','Written using Python and libtcod.']

#colors
color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

def main_menu():
	global game_state

	img = libtcod.image_load('playground-title-small.png')
	
	while not libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0)

		#show options and wait for the player's choice
		if game_state == 'won':
			img = libtcod.image_load('playground-win-small.png')
			choice = draw.menu('Congrats! Your score was ' + str(objects.score) + '.', ['Play a new game', 'Instructions','About','Quit'], 35)
		else:
			choice = draw.menu('', ['Play a new game', 'Instructions','About','Quit'], 24)

		if choice == 0:  #new game
			new_game()
			play_game()
		elif choice == 1: #instructions
			blah = draw.instructions('',instructions,50)
		elif choice == 2: #about
			blah = draw.instructions('',credits,50)
		elif choice == 3:  #quit
			break
	
#initialize a new game
def new_game():
	global game_state
	game_state = 'playing'
	#create the map
	maps.make_map()
	maps.init_fov()		
	draw.game_msgs = []
			
	#define initial objects
	objects.init()
	objects.create_player(maps.startx, maps.starty)
	objects.create_mom(maps.endx, maps.endy)
	objects.generate_monsters_and_items()
	
	draw.fov_update(objects.player.x, objects.player.y)

def play_game():	
	global game_state, player_action
	# main loop
	while not libtcod.console_is_window_closed():	
		draw.render_all(objects.player, objects.things, objects.inventory, objects.score)
		objects.find_visible()
		objects.find_at_loc()
		libtcod.console_flush()
		
		#clear position of character
		for thing in objects.things:
			thing.clear()
		
		#get next keystroke
		player_action = handle_keys()
		if player_action == 'exit':
			save_game()
			break
		
		if player_action == 'won':
			break
		
			#let monsters take their turn
		if game_state == 'playing' and player_action != 'didnt-take-turn':
			objects.monster_actions()

def save_game():
	global game_state
	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = maps.map
	file['things'] = objects.things
	file['inventory'] = objects.inventory
	file['score'] = objects.score
	file['player-index'] = objects.things.index(objects.player)
	file['game-msgs'] = draw.game_msgs
	file['game-state'] = game_state
	file.close()

def load_game():
	#open the previously saved shelve and load the game data
	global game_state

	file = shelve.open('savegame', 'r')
	maps.map = file['map']
	objects.things = file['things']
	objects.player = objects.things[file['player_index']]  #get index of player in objects list and access it
	objects.inventory = file['inventory']
	objects.score = file['score']
	draw.game_msgs = file['game_msgs']
	game_state = file['game_state']
	file.close()

	draw.fov_update = True
	draw.fov_update(objects.player.x, objects.player.y)
	
#getting keys
def get_key(key):
    if key.vk == libtcod.KEY_CHAR:
        return chr(key.c)
    else:
        return key.vk
	
#key input handling
def handle_keys():

	global playerx, playery, game_state
	key = libtcod.console_wait_for_keypress(True)
    
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
	elif key.vk == libtcod.KEY_ESCAPE or game_state == 'dead':
		return 'exit'  #exit game
 
	#check for player death
	if (not objects.player.alive):
		game_state = 'dead'
		return 'died'
	
	if (objects.player.talking):
		game_state = 'talking'
		#test for other keys
		key_char = chr(key.c)
		
		if key_char == 'y' and libtcod.console_is_key_pressed(key):
			game_state = 'won'
			objects.add_toys_to_score()
			return 'won'
		elif key_char == 'n' and libtcod.console_is_key_pressed(key):
			game_state = 'playing'
			return 'didnt-take-turn'
	
    #movement keys
	if game_state == 'playing':
		if libtcod.console_is_key_pressed(libtcod.KEY_KP7):
			objects.player_actions(-1,-1)
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_UP) or libtcod.console_is_key_pressed(libtcod.KEY_KP8):
			objects.player_actions(0,-1)
	 
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
			objects.player_actions(1,-1)
		
		elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or libtcod.console_is_key_pressed(libtcod.KEY_KP2):
			objects.player_actions(0,1)
	 
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
			objects.player_actions(-1,1)
	 
		elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or libtcod.console_is_key_pressed(libtcod.KEY_KP4):
			objects.player_actions(-1,0)
	 
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
			objects.player_actions(1,1)
	 
		elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or libtcod.console_is_key_pressed(libtcod.KEY_KP6):
			objects.player_actions(1,0)	
		
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP5):
			objects.player_actions(0,0)
		else:
			#test for other keys
			key_char = chr(key.c)

			if key_char == 'c' and libtcod.console_is_key_pressed(key):
				#pick up an item
				objects.collect_item()
				return 'collected-item'
				
			elif key_char == '.' and libtcod.console_is_key_pressed(key):
				objects.player_actions(0,0)
				
			elif key_char == 'e' and libtcod.console_is_key_pressed(key):
				objects.eat_candy()
				return 'ate-candy'
				
			elif key_char == 'g' and libtcod.console_is_key_pressed(key):
				draw.message('Press a direction key to give the toy:')
				game_state = 'giving-toy'
				return 'didnt-take-turn'
				
			elif key_char == 'h' and libtcod.console_is_key_pressed(key):
				draw.instructions('Key commands', ['','Press arrow keys or numpad to move.','','c: pick up candy and toys.','e: eat candy to regain health', 'g: give a toy to another child','esc: quit','','If the teacher sees you, you\'ll get in trouble.','','Giving away your toys calms your enemies down.'], 50)
				return 'didnt-take-turn'
				
			else:
				return 'didnt-take-turn'
	if game_state == 'giving-toy':
		if libtcod.console_is_key_pressed(libtcod.KEY_KP7):
			objects.give_toy(-1,-1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_UP) or libtcod.console_is_key_pressed(libtcod.KEY_KP8):
			objects.give_toy(0,-1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
			objects.give_toy(1,-1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or libtcod.console_is_key_pressed(libtcod.KEY_KP2):
			objects.give_toy(0,1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
			objects.give_toy(-1,1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or libtcod.console_is_key_pressed(libtcod.KEY_KP4):
			objects.give_toy(-1,0)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
			objects.give_toy(1,1)
			game_state = 'playing'
			
		elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or libtcod.console_is_key_pressed(libtcod.KEY_KP6):
			objects.give_toy(1,0)
			game_state = 'playing'
			
		else:
			return 'didnt-take-turn'

main_menu()			
				

