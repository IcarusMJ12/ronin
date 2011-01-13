#!/usr/bin/env python
import pygame
from pygame.locals import *
from context import Context as Context
from grids import Location, Tile, SquareGrid
from objects import *
from random import Random

def mainloop():
    ctx=Context.getContext()
    event = None
    while True:
        event = pygame.event.wait()
        print event
        if(event.mod==0):
            if(event.key==K_j):
                ctx.pc.moveS()
            elif(event.key==K_k):
                ctx.pc.moveN()
            elif(event.key==K_h):
                ctx.pc.moveW()
            elif(event.key==K_l):
                ctx.pc.moveE()
            for m in ctx.enemies:
                m.move()
            ctx.group.clear(ctx.screen,ctx.background)
            ctx.group.draw(ctx.screen)
            pygame.display.update()
        if(event.key==K_q and (event.mod==KMOD_LCTRL or event.mod==KMOD_RCTRL)):
            pygame.display.quit()
            return
        if not len(ctx.enemies):
            print "You have slain all the vicious buggers!"
            return

def init():
    ctx=Context.getContext()
    ctx.FONT_SIZE = 24
    ctx.CELL_HEIGHT = ctx.FONT_SIZE
    ctx.CELL_WIDTH = ctx.FONT_SIZE*2/3
    ctx.font = pygame.font.Font('Courier New.ttf', ctx.FONT_SIZE)
    ctx.screen = pygame.display.set_mode((800,600))
    ctx.screen.fill((0,0,0))
    ctx.group = pygame.sprite.RenderClear()
    ctx.background = ctx.screen.copy()
    ctx.random = Random(0)

if __name__ == '__main__':
    pygame.init()
    init()
    ctx=Context.getContext()

    pygame.event.set_allowed(None)
    pygame.event.set_allowed([KEYDOWN])
    pygame.display.set_caption('test1')
    pygame.display.update()
    ctx.world=SquareGrid(0,25,25)
    for i in xrange(25):
        ctx.world.getTile(0,i).terrain=Wall()
        ctx.world.getTile(24,i).terrain=Wall()
    for i in xrange(23):
        ctx.world.getTile(i+1,0).terrain=Wall()
        ctx.world.getTile(i+1,24).terrain=Wall()
    ctx.pc=PC()
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
    ctx.group.add(*ctx.world.getTiles())
    clean_count=0
    for i in ctx.world.getTiles():
        if i.dirty==0:
            clean_count+=1
    print clean_count
    ctx.group.draw(ctx.screen)
    pygame.display.update()
    mainloop()
