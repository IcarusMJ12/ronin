#!/usr/bin/env python
import pygame
from pygame.locals import *
from lie import input, messages, monofont, turns, ui, savefile
from lie.gridview import HexGridView, computeTileColor
from lie.mapgen import CellularAutomata
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

def reallyQuit():
    """Quit without saving."""
    s=savefile.SaveFile(SAVE_FILE)
    try:
        s.delete()
    except OSError:
        pass
    pygame.display.quit()
    sys.exit(0)

def dontQuit():
    ctx=Context.getContext()
    ctx.message_buffer.is_read=True
    ctx.message_buffer.flush()
    ctx.screen_manager.current.handlers.pop()

def quit():
    """Quit without saving."""
    ctx=Context.getContext()
    ctx.message_buffer.addMessage("Commit seppuku? [y/N]")
    quit_handler=input.InputHandler()
    quit_handler.addFunction(dontQuit, K_RETURN)
    quit_handler.addFunction(dontQuit, K_SPACE)
    quit_handler.addFunction(dontQuit, K_n)
    quit_handler.addFunction(reallyQuit, K_y)
    ctx.screen_manager.current.handlers.push(quit_handler)

def save():
    """Save the game and exit."""
    ctx=Context.getContext()
    s=savefile.SaveFile(SAVE_FILE)
    s.save({'ctx':ctx})
    pygame.display.quit()
    sys.exit(0)

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
        ctx.quit=reallyQuit
        #populate world
        generator=CellularAutomata(Random(1), Floor, Wall)
        ctx.world=generator.generateLevel(51,25)
        tile=ctx.world[26,16]
        tile.actor=ctx.pc
        ctx.pc.parent=tile
        ctx.pc.perception=PGrid(ctx.world, ctx.pc)
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
        for tile in ctx.world.tiles:
            tile.dirty=1
    ctx.worldview=HexGridView(ctx.world, ctx.pc.perception)
    ctx.worldview.center(ctx.worldview[ctx.pc.parent.loc].rect)
    ctx.screen_manager.current.view.add(ctx.worldview)
    ctx.screen_manager.current.view.draw()
    ctx.turn_manager.run()
