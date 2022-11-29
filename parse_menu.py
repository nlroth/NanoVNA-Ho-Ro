#!/usr/bin/python

import re

# parse the source code for DiSlord's NanoVNA-H / -H4 firmware
# show all possible menu entries regardless if they are enabled / disabled
# in nanovna.h
# copy this file in the source code directory

# parse 'plot.c' and create a directory from lines like this
# [MS_SERIES_RX] = {"R+jX SERIES","%F%+jF" S_OHM,                s21series_r, s21series_x },
# key = entry in brackets and value = 1st string
# e.g.: { "MS_SERIES_RX" : "R+jX SERIES" }

with open( 'plot.c' ) as plot_c:
    lines = plot_c.read().splitlines()

# find 'key' in brackets and 'val' in 1st double quote pair
pattern_text = r'.*?\[(?P<key>\w+?)\].*?\"(?P<val>.+?)\"'
pattern = re.compile(pattern_text)

ms_dict = {} # start with an empty dictionary

for line in lines:
    if 'marker_info_t' in line:
        continue
    line = line.strip()
    if '[MS_' == line[0:4]:
        match = pattern.match( line )
        key, val = match.groups()
        ms_dict[ key ] = val # put in dictionary


# read the file 'ui.c' which contains the menu structure
# skip "#if 0 ... #endif" or "#if 0 ... #else" sections
with open( 'ui.c' ) as ui_c:
    lines = ui_c.read().splitlines()


# use line content left of c comment "//"
pattern_text = r'(?P<line>.*?)(?P<comment>//.*)'
pattern = re.compile(pattern_text)

skip_lines = False
ui = []

for line in lines:
    if '#if 0' in line: # skip the lines starting from here
        skip_lines = True
    elif skip_lines:
        if '#else' in line or '#endif' in line: # stop skipping
            skip_lines = False
    else:
        if '//' in line: # cut comment
            match = pattern.match( line )
            line = match.group( 'line' )
        ui.append( line )


# format a string like 'menu_XXXXX_acb' or 'menu_XXXXX_cb' and return only 'XXXXX'
def strip_menu( name ):
    if '_acb' in name:
        return name[5:-4] # strip 'menu_' and '_acb'
    elif '_cb' in name:
        return name[5:-3] # strip 'menu_' and '_cb'
    else:
        return name[5:] # strip 'menu_'


# print a menu entry indented according to level
def print_entry( entry, level=0 ):
    print( (' ' * ( 4 * level ) ) + entry )


def show_menu( this_menu, level ):
    menu = None
    for line in ui:
        # skip declaration lines
        if 'extern' in line:
            continue
        # find menu
        # format:  "const menuitem_t menu_config[] = {"
        if f'const menuitem_t {this_menu}[]' in line:
            menu = this_menu
            continue

        # parse menu entries
        #  { MT_SUBMENU, 0, "DISPLAY",   menu_display },
        if menu:
            if "MT_NONE" in line: # last entry -> back
                if level: # no "<- BACK" button in level 0
                    print_entry( '<- BACK', level )
                return
            if "MT_SUBMENU" in line \
            or "MT_CALLBACK" in line \
            or "MT_ADV_CALLBACK" in line:
                line = line.strip(' {},')
                what, param, text, next_menu = line.split( ',' )
                param = param.strip()
                text = text.strip()
                text_1 = text
                next_menu = next_menu.strip()
                menu_text = None

                if 'MT_CUSTOM_LABEL' == text:
                    #print( line )
                    if next_menu == '':
                        menu_text = ''
                    elif 'F_S11' in param:
                        next_menu = 'menu_marker_s11smith'
                        menu_text = 'SMITH'
                    elif 'F_S21' in param:
                        next_menu = 'menu_marker_s21smith'
                        menu_text = 'SMITH'
                    elif 'menu_save_acb' == next_menu:
                        menu_text = f'SAVE {param}'
                    elif 'menu_recall_acb' == next_menu:
                        menu_text = f'RECALL {param}'
                    elif 'menu_power_sel_acb' == next_menu:
                        menu_text = 'POWER'
                    elif 'menu_cal_range_acb' == next_menu:
                        menu_text = 'RESET CAL RANGE'
                    elif 'menu_keyboard_acb' == next_menu:
                        menu_text = 'JOG STEP'

                menu_name = strip_menu( next_menu )
                if '"' in text:
                    text_1 = text.split('"')[1]
                if 'MORE' in text:
                    menu_text = '-> MORE'
                elif 'VNA_MODE_SEARCH' == param:
                    menu_text = 'SEARCH MIN/MAX'
                elif 'MK_SEARCH_LEFT' == param:
                    menu_text = 'SEARCH <- LEFT'
                elif 'MK_SEARCH_RIGHT' == param:
                    menu_text = 'SEARCH -> RIGHT'
                elif 'marker_smith' == menu_name:
                    if param in ms_dict: # translation exists
                        menu_text = f'{ms_dict[ param ]}' # use it
                    elif param[0:3] == 'MS_': # reformat param 'MS_XYZ' -> 'XYZ'
                        menu_text = param[3:]
                    else: # other format, just use param
                        menu_text = param
                elif 'pause' == menu_name:
                    menu_text = 'PAUSE/RESUME SWEEP'
                elif 'format' in menu_name:
                    menu_text = text_1
                elif 'stored_trace' == menu_name:
                    menu_text = text_1 % 'STORE/CLEAR'
                elif '%d' in text_1 and param.isnumeric():
                    menu_text = text_1 % int( param )
                elif '%s' in text_1:
                    menu_text = text_1 % param
                if menu_text == None:
                    menu_text = text_1
                # remove '\n' and duplicate spaces
                menu_text = menu_text.replace( '\\n', ' ' ).replace( '  ', ' ' )
                print_entry( menu_text, level ) # print indented according level
                # recurse into next level
                show_menu( next_menu, level + 1 )

# start from top level menu
show_menu( 'menu_top', 0 )
