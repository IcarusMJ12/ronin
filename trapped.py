#!/usr/bin/env python
import pygame
from pygame.locals import *
from context import Context as Context
from grids import Location, Tile, SquareGrid
from objects import *

class MovableSprite(pygame.sprite.Sprite):
    def moveUp(self):
        self.rect=self.rect.move(0,-1*ctx.FONT_SIZE)
    
    def moveDown(self):
        self.rect=self.rect.move(0,1*ctx.FONT_SIZE)
    
    def moveLeft(self):
        self.rect=self.rect.move(-1*ctx.FONT_SIZE,0)
    
    def moveRight(self):
        self.rect=self.rect.move(1*ctx.FONT_SIZE,0)
    
def mainloop():
    ctx=Context.getContext()
    event = None
    while True:
        event = pygame.event.wait()
        print event
        if(event.type==KEYUP):
            if(event.mod==0):
                if(event.key==K_j):
                    ctx.pc.moveS()
                elif(event.key==K_k):
                    ctx.pc.moveN()
                elif(event.key==K_h):
                    ctx.pc.moveW()
                elif(event.key==K_l):
                    ctx.pc.moveE()
                ctx.group.clear(ctx.screen,ctx.background)
                ctx.group.draw(ctx.screen)
                pygame.display.update()
            if(event.key==K_q and (event.mod==KMOD_LCTRL or event.mod==KMOD_RCTRL)):
                pygame.display.quit()
                return

def init():
    ctx=Context.getContext()
    ctx.FONT_SIZE = 18
    ctx.font = pygame.font.Font(None, ctx.FONT_SIZE)
    ctx.screen = pygame.display.set_mode((800,600))
    ctx.screen.fill((0,0,0))
    ctx.group = pygame.sprite.RenderClear()
    ctx.background = ctx.screen.copy()

if __name__ == '__main__':
    pygame.init()
    init()
    ctx=Context.getContext()

    pygame.event.set_allowed(None)
    pygame.event.set_allowed([KEYUP])
    pygame.display.set_caption('test1')
    pygame.display.update()
    ctx.world=SquareGrid(0,9,9)
    for i in xrange(9):
        ctx.world.getTile(0,i).terrain=Wall()
        ctx.world.getTile(8,i).terrain=Wall()
    for i in xrange(7):
        ctx.world.getTile(i+1,0).terrain=Wall()
        ctx.world.getTile(i+1,8).terrain=Wall()
    ctx.pc=Human()
    tile=ctx.world.getTile(4,4)
    tile.actor=ctx.pc
    ctx.pc.parent=tile
    ctx.group.add(*ctx.world.getTiles())
    clean_count=0
    for i in ctx.world.getTiles():
        if i.dirty==0:
            clean_count+=1
    print clean_count
    ctx.group.draw(ctx.screen)
    pygame.display.update()
    mainloop()
