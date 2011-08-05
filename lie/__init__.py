# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import pygame
from conf import Conf
import globals
import monofont

def init(f):
    Conf.load(f)
    conf=Conf.getConf()
    monofont.init()
    pygame.display.init()
    globals.font_size=conf.getint('lie','font_size')
    globals.font=monofont.MonoFont(conf.get('lie','font'),globals.font_size)
    globals.scale_horizontally=conf.getint('lie','scale_horizontally')
    globals.darkest_gray=conf.getfloat('lie','darkest_gray')
    (globals.cell_width,globals.cell_height)=(globals.font.w, globals.font.h)
    (globals.screen_width, globals.screen_height)=(conf.get('lie','screen_width'),conf.get('lie','screen_height'))
    if globals.screen_width[-2:]=='px':
        globals.screen_width=int(globals.screen_width[0:-2])
    else:
        globals.screen_width=globals.cell_width*int(globals.screen_width)
    if globals.screen_height[-2:]=='px':
        globals.screen_height=int(globals.screen_height[0:-2])
    else:
        globals.screen_height=globals.cell_height*int(globals.screen_height)
    globals.message_buffer_height = conf.get('lie','message_buffer_height')
    if globals.message_buffer_height[-2:]=='px':
        globals.message_buffer_height=int(globals.message_buffer_height[0:-2])
    else:
        globals.message_buffer_height=int(globals.message_buffer_height)*globals.cell_height
    globals.grid_offset = globals.message_buffer_height
    globals.screen = pygame.display.set_mode((globals.screen_width, globals.screen_height))
    globals.screen.fill((0,0,0))
    globals.background = globals.screen.copy()
    globals.savefile_location = conf.get('lie','savefile_location')
