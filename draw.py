import libtcodpy as libtcod
import map as maps
import textwrap

#globals
global con, gui_con, fov_recompute, game_msgs

#constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 45
FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10
GAME_FONT = 'consolas10x10_gs_tc.png'
WINDOW_TITLE = 'The Playground'
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 4
MSG_HEIGHT = PANEL_HEIGHT - 2

def init_console():
	global con, gui_con, fov_recompute
	libtcod.console_set_custom_font(GAME_FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
	libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE, False)
	con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
	gui_con = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
	fov_recompute = True

def instructions(header, options, width):
	global con
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

	#calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	height = len(options) + header_height + 3

	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 1, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

	#print all the options
	y = header_height

	for option_text in options:
		text = option_text
		libtcod.console_print_ex(window, 1, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
	
	libtcod.console_print_ex(window, 1, y, libtcod.BKGND_NONE, libtcod.LEFT, '')
	libtcod.console_print_ex(window, 1, y + 1, libtcod.BKGND_NONE, libtcod.LEFT, 'Press enter to close the menu.')	
	libtcod.console_print_ex(window, 1, y + 2, libtcod.BKGND_NONE, libtcod.LEFT, '')
	
	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.9)

	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)	
	
	if (key.vk == libtcod.KEY_ENTER):
		return
	else:
		key = libtcod.console_wait_for_keypress(True)
	
def menu(header, options, width):
	global con
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

	#calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	height = len(options) + header_height + 1

	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 1, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1

	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)	
	
	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None
	
def show_stats(player, inventory, score):
	global game_msgs
	#prepare to render the GUI panel
	libtcod.console_set_default_background(gui_con, libtcod.black)
	libtcod.console_clear(gui_con)
 
	#show the player's stats
	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
		libtcod.light_red, libtcod.darker_red)
 
 	#print the game messages, one line at a time
	y = 1
	for (line, color) in game_msgs:
		libtcod.console_set_default_foreground(gui_con, color)
		libtcod.console_print_ex(gui_con, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		y += 1

	#calculate toy and candy count
	toys = 0
	candy = 0
	
	for thing in inventory:
		if thing.item.type == 'candy':
			candy += 1
		elif thing.item.type == 'toy':
			toys += 1
	
	libtcod.console_set_default_foreground(gui_con, libtcod.white)
	libtcod.console_print_ex(gui_con, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Toys: ' + str(toys) + ' Candy: ' + str(candy))
	libtcod.console_print_ex(gui_con, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, 'Score: ' + str(score))
 
	#blit the contents of "panel" to the root console
	libtcod.console_blit(gui_con, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def message(new_msg, color = libtcod.white):
	global gui_con
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]
 
		#add the new line as a tuple, with the text and the color
		game_msgs.append( (line, color) )
	
def draw_object(obj):
	global con
	#set the color and then draw the character that represents this object at its position
	if libtcod.map_is_in_fov(maps.fov_map, obj.x, obj.y):
		libtcod.console_set_default_foreground(con, obj.color)
		libtcod.console_put_char(con, obj.x, obj.y, obj.char, libtcod.BKGND_NONE)

def clear_object(obj):
	global con
	#erase the character that represents this object
	if libtcod.map_is_in_fov(maps.fov_map, obj.x, obj.y):
		libtcod.console_put_char_ex(con, obj.x, obj.y, '.', libtcod.light_grey, libtcod.black)
	else:
		libtcod.console_put_char_ex(con, obj.x, obj.y, '.', libtcod.black, libtcod.black)

def fov_update(x, y):
	global fov_recompute
	if fov_recompute:
		#recompute FOV if needed (the player moved or something)
		fov_recompute = False
		libtcod.map_compute_fov(maps.fov_map, x, y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	global gui_con
	
	#render a bar (HP, experience, etc). first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)

	#render the background first
	libtcod.console_set_default_background(gui_con, back_color)
	libtcod.console_rect(gui_con, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

	#now render the bar on top
	libtcod.console_set_default_background(gui_con, bar_color)
	if bar_width > 0:
		libtcod.console_rect(gui_con, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
	
	#finally, some centered text with the values
	libtcod.console_set_default_foreground(gui_con, libtcod.white)
	libtcod.console_print_ex(gui_con, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))
	
def render_all(player, objs, inventory, score):
	fov_update(player.x, player.y)
	
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			visible = libtcod.map_is_in_fov(maps.fov_map, x, y)
			wall = maps.map[x][y].block_sight
			if not visible and not maps.map[x][y].explored:
				libtcod.console_put_char_ex(con, x, y, ' ', libtcod.black, libtcod.black)
			else:
				maps.map[x][y].explored = True
				if wall:
					libtcod.console_put_char_ex(con, x, y, '#', libtcod.light_grey, libtcod.black)
				else:
					libtcod.console_put_char_ex(con, x, y, '.', libtcod.light_grey, libtcod.black)
	
	#draw all objects in the list
	for obj in objs:
		if (obj != player):
			draw_object(obj)
	
	draw_object(player)
	
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
	
	#show player stats
	show_stats(player, inventory, score)