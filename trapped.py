#!/usr/bin/env python
import pygame
from pygame.locals import *
from context import Context as Context
from grids import Location, Tile, SquareGrid
from objects import *
import messages
from random import Random
import logging
import ui
import monofont
import sys


def mainloop():
    ctx=Context.getContext()
    event = None
    while True:
        event = pygame.event.wait()
        logging.debug(event)
        ctx.message_buffer.flush()
        ret=ctx.screen_manager.current.handlers.handle(event)
        if not len(ctx.enemies):
            print "You have slain all the vicious buggers!"
            return
        if ret is not None:
            for m in ctx.enemies:
                m.move()
        ctx.screen_manager.current.view.update()

def init():
    #setup logger
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    ctx=Context.getContext()
    #setup initial configuration settings
    ctx.FONT_SIZE = 24
    ctx.MESSAGE_BUFFER_HEIGHT = 4
    ctx.font = monofont.MonoFont('Andale Mono.ttf', ctx.FONT_SIZE)
    (ctx.CELL_WIDTH,ctx.CELL_HEIGHT) = (ctx.font.w, ctx.font.h)
    ctx.GRID_OFFSET = ctx.CELL_HEIGHT*(ctx.MESSAGE_BUFFER_HEIGHT+1)
    ctx.SCREEN_WIDTH = 25*ctx.CELL_WIDTH

    #initialize display
    ctx.screen = pygame.display.set_mode((25*ctx.CELL_WIDTH,25*ctx.CELL_HEIGHT+ctx.GRID_OFFSET))
    ctx.screen.fill((0,0,0))
    ctx.background = ctx.screen.copy()

    #get random
    ctx.random = Random(0)

    #get PC -- important for functions below
    ctx.pc=PC()

    #setup event handler
    pygame.event.set_allowed(None)
    pygame.event.set_allowed([KEYDOWN])
    handler=ui.InputHandler()
    handler.addFunction(ctx.pc.moveS, K_j)
    handler.addFunction(ctx.pc.moveN, K_k)
    handler.addFunction(ctx.pc.moveW, K_h)
    handler.addFunction(ctx.pc.moveE, K_l)
    handler.addFunction(exit, K_q, (KMOD_CTRL,))

    #setup screen manager
    ctx.screen_manager=ui.ScreenManager(ui.Screen(handler,ctx))

    ctx.message_buffer=messages.MessageBuffer(pygame.rect.Rect(0,0,ctx.SCREEN_WIDTH, ctx.MESSAGE_BUFFER_HEIGHT*ctx.font.h), ctx.font, ctx.screen_manager.current)

def exit():
    pygame.display.quit()
    sys.exit()

if __name__ == '__main__':
    pygame.init()
    init()
    ctx=Context.getContext()

    pygame.display.set_caption('test1')
    pygame.display.update()
    #populate world
    ctx.world=SquareGrid(0,25,25)
    for i in xrange(25):
        ctx.world.getTile(0,i).terrain=Wall()
        ctx.world.getTile(24,i).terrain=Wall()
    for i in xrange(23):
        ctx.world.getTile(i+1,0).terrain=Wall()
        ctx.world.getTile(i+1,24).terrain=Wall()
    tile=ctx.world.getTile(13,13)
    tile.actor=ctx.pc
    ctx.pc.parent=tile
    for i in xrange(23):
        for j in xrange(23):
            if ctx.random.randint(0,5)==5:
                try:
                    ctx.world.getTile(i+1,j+1).terrain=Wall()
                except:
                    pass
    ctx.enemies=[]
    for i in xrange(23):
        for j in xrange(23):
            if ctx.random.randint(0,10)==10:
                try:
                    tile=ctx.world.getTile(i+1,j+1)
                    tile.actor=Mogwai()
                    tile.actor.parent=tile
                    ctx.enemies.append(tile.actor)
                except:
                    pass
    ctx.screen_manager.current.view.add(*ctx.world.getTiles())
    ctx.screen_manager.current.view.update()
    mainloop()
