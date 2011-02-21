#!/usr/bin/env python
import pygame
from pygame.locals import *
from lie import input, messages, monofont, turns, ui
from lie.grids import Location, Tile, PseudoHexGrid
from lie.objects import *
import lie.globals
from context import Context as Context
from objects import *
import logging
from random import Random
import sys

#used by exit handler to quit the game
def quit():
    pygame.display.quit()
    sys.exit(0)

#player and enemy turn phases to here
def player_pre():
    ctx=Context.getContext()
    ctx.message_buffer.is_read=True
    ctx.world.FOV(ctx.pc.parent,6)
    ctx.world.draw()

def player_phase():
    ctx=Context.getContext()
    event=pygame.event.wait()
    logging.debug(event)
    ret=ctx.screen_manager.current.handlers.handle(event)
    logging.info(ret)
    if ret is not None:
        ctx.message_buffer.flush()
        ctx.world.draw()
        return True
    return False

def player_post():
    ctx=Context.getContext()
    if not len(ctx.enemies):
        ctx.message_buffer.addMessage("All oni have been slain and you emerged victorious!")
        victory_handler=input.InputHandler()
        victory_handler.addFunction(ctx.quit, K_RETURN)
        victory_handler.addFunction(ctx.quit, K_SPACE)
        ctx.screen_manager.current.handlers.push(victory_handler)

def enemies_phase():
    ctx=Context.getContext()
    for enemy in ctx.enemies:
        enemy.act()
    return True

#initializing everything
def init():
    #setup logger
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    ctx=Context.getContext()
    ctx.quit=quit
    #get random
    ctx.random = Random(0)

    #get PC -- important for functions below
    ctx.pc=PC()

    #setup event handler
    pygame.event.set_allowed(None)
    pygame.event.set_allowed([KEYDOWN])
    handler=input.InputHandler()
    handler.addFunction(ctx.pc.moveSE, K_j)
    handler.addFunction(ctx.pc.moveNW, K_k)
    handler.addFunction(ctx.pc.moveN, K_y)
    handler.addFunction(ctx.pc.moveW, K_u)
    handler.addFunction(ctx.pc.moveE, K_b)
    handler.addFunction(ctx.pc.moveS, K_n)
    handler.addFunction(ctx.pc.idle, K_PERIOD)
    handler.addFunction(ctx.quit, K_q, (KMOD_CTRL,))

    #setup screen manager
    ctx.screen_manager=ui.ScreenManager(ui.Screen(handler))

    ctx.message_buffer=messages.MessageBuffer(ctx.screen_manager.current)

    pygame.display.set_caption('trapped')
    pygame.display.update()

if __name__ == '__main__':
    lie.init('trapped.conf')
    init()
    ctx=Context.getContext()
    #populate world
    ctx.world=PseudoHexGrid(0,51,25)
    for i in xrange(25):
        ctx.world.getTile(0,i).terrain=Wall()
        ctx.world.getTile(50,i).terrain=Wall()
    for i in xrange(49):
        ctx.world.getTile(i+1,0).terrain=Wall()
        ctx.world.getTile(i+1,24).terrain=Wall()
    tile=ctx.world.getTile(26,13)
    tile.actor=ctx.pc
    ctx.pc.parent=tile
    ctx.world.center(tile.rect)
    for i in xrange(49):
        for j in xrange(23):
            if ctx.random.randint(0,5)==5:
                try:
                    ctx.world.getTile(i+1,j+1).terrain=Wall()
                except:
                    pass
    ctx.enemies=[]
    for i in xrange(49):
        for j in xrange(23):
            if ctx.random.randint(0,10)==10:
                try:
                    tile=ctx.world.getTile(i+1,j+1)
                    tile.actor=Oni()
                    tile.actor.parent=tile
                    ctx.enemies.append(tile.actor)
                except:
                    pass
    ctx.screen_manager.current.view.add(ctx.world)
    ctx.screen_manager.current.view.draw()
    #setup turn manager
    player_turn=turns.TurnPhase(player_phase)
    player_turn.pre=player_pre
    player_turn.post=player_post
    enemies_turn=turns.TurnPhase(enemies_phase)
    tm=turns.TurnManager()
    tm.add(player_turn)
    tm.add(enemies_turn)
    tm.run()
