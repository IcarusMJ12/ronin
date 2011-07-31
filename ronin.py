#!/usr/bin/env python
import pygame
from pygame.locals import *
from lie import input, messages, monofont, turns, ui, savefile
from lie.gridview import HexGridView, computeTileColor
from lie.reality import Level
from lie.perception import PGrid
from lie.objects import *
import lie.globals
from lie.context import Context as Context
from objects import *
import logging
from random import Random
import sys
#import profile

#import psyco
#psyco.full()

SAVE_FILE='save'

def quit():
    """Quit without saving."""
    pygame.display.quit()
    sys.exit(0)

def save():
    """Save the game and exit."""
    ctx=Context.getContext()
    s=savefile.SaveFile(SAVE_FILE)
    s.save({'ctx':ctx})
    quit()

def load():
    """Loads the game if available."""
    s=savefile.SaveFile(SAVE_FILE)
    ret=s.load()
    if not ret:
        return ret
    Context.ctx=ret['ctx']
    return Context.getContext()

#player and enemy turn phases to here
def player_pre():
    ctx=Context.getContext()
    ctx.message_buffer.is_read=True
    ctx.pc.perception.calculateFOV()
    ctx.worldview.draw()

def player_phase():
    ctx=Context.getContext()
    event=pygame.event.wait()
    logging.debug(event)
    ret=ctx.screen_manager.current.handlers.handle(event)
    logging.info(ret)
    if ret is not None:
        ctx.message_buffer.flush()
        ctx.worldview.draw()
        return True
    return False

def player_post():
    ctx=Context.getContext()
    if not len(ctx.enemies):
        ctx.message_buffer.addMessage("All oni have been slain and you emerged victorious!")
        victory_handler=input.InputHandler()
        victory_handler.addFunction(quit, K_RETURN)
        victory_handler.addFunction(quit, K_SPACE)
        ctx.screen_manager.current.handlers.push(victory_handler)

def enemies_phase():
    ctx=Context.getContext()
    for enemy in ctx.enemies:
        enemy.act()
    return True

#initializing everything
def init():
    #setup logger
    logging.basicConfig(level=logging.DEBUG)
    #logging.basicConfig(level=logging.INFO)

    ctx=Context.getContext()
    #get random
    if not ctx.random:
        ctx.random = Random(0)

    #get PC -- important for functions below
    if not ctx.pc:
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
    handler.addFunction(quit, K_q, (KMOD_CTRL,))
    handler.addFunction(save, K_s, (KMOD_SHIFT,))

    #setup screen manager
    ctx.screen_manager=ui.ScreenManager(ui.Screen(handler))

    if not ctx.message_buffer:
        ctx.message_buffer=messages.MessageBuffer(ctx.screen_manager.current)

    pygame.display.set_caption('Ronin')
    pygame.display.update()

if __name__ == '__main__':
    lie.init('ronin.conf')
    ctx=load()
    init()
    if ctx == None:
        ctx=Context.getContext()
        ctx.quit=quit
        #populate world
        ctx.world=Level(51,25)
        ctx.worldview=HexGridView(51,25)
        for i in xrange(25):
            ctx.world[0,i].terrain=Wall()
            ctx.world[50,i].terrain=Wall()
        for i in xrange(49):
            ctx.world[i+1,0].terrain=Wall()
            ctx.world[i+1,24].terrain=Wall()
        tile=ctx.world[26,13]
        tile.actor=ctx.pc
        ctx.pc.parent=tile
        ctx.pc.perception=PGrid(ctx.world, ctx.pc)
        ctx.worldview.pc=ctx.pc
        ctx.worldview.level=ctx.world
        ctx.worldview.center(ctx.worldview[ctx.pc.parent.loc].rect)
        for i in xrange(49):
            for j in xrange(23):
                if ctx.random.randint(0,5)==5:
                    try:
                        ctx.world[i+1,j+1].terrain=Wall()
                    except:
                        pass
        ctx.enemies=[]
        for i in xrange(49):
            for j in xrange(23):
                if ctx.random.randint(0,10)==10:
                    try:
                        tile=ctx.world[i+1,j+1]
                        tile.actor=Oni()
                        tile.actor.parent=tile
                        ctx.enemies.append(tile.actor)
                    except:
                        pass
        ctx.screen_manager.current.view.add(ctx.worldview)
        ctx.screen_manager.current.view.draw()
        #setup turn manager
        player_turn=turns.TurnPhase(player_phase)
        player_turn.pre=player_pre
        player_turn.post=player_post
        enemies_turn=turns.TurnPhase(enemies_phase)
        tm=turns.TurnManager()
        tm.add(player_turn)
        tm.add(enemies_turn)
        ctx.turn_manager=tm
        #profile.run("tm.run()",'ronin.prof')
    else:
        ctx.worldview=HexGridView(51,25)
        ctx.worldview.pc=ctx.pc
        ctx.worldview.level=ctx.world
        ctx.worldview.center(ctx.worldview[ctx.pc.parent.loc].rect)
        ctx.screen_manager.current.view.add(ctx.worldview)
        for tile in ctx.worldview.level.tiles:
            tile.dirty=1
        ctx.screen_manager.current.view.draw()
    ctx.turn_manager.run()
