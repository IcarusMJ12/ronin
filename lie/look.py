#!/usr/bin/env python
#Copyright (c) 2011 Igor Kaplounenko
#This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

__all__=['lookMode']

from pygame.locals import *

from context import Context
import input_handling
import globals

def lookMode():
    def look():
        tile=worldview[loc[0]]
        backup[0]=tile.image
        tile.image=cursor
        if abs(loc[0][0]-previous_loc[0][0])>5 or abs(loc[0][1]-previous_loc[0][1])>5:
            worldview.center(worldview[loc[0]].rect)
            previous_loc[0]=loc[0]
        screen_manager.current.view.draw()
        message='\n'.join([contents[2] for contents in perception.examineTile(loc[0])])
        if globals.wizard_mode:
            message+='\n[cover: '+str(perception[loc[0]].cover)+']'
        message_buffer.addMessage(message)
    
    def quitLook():
        worldview[loc[0]].image=backup[0]
        worldview.center(worldview[original_loc].rect)
        screen_manager.current.handlers.pop()
        screen_manager.current.view.draw()
    
    def N():
        worldview[loc[0]].image=backup[0]
        loc[0]=(loc[0][0],max(0,loc[0][1]-1))
        look()
    
    def NW():
        worldview[loc[0]].image=backup[0]
        loc[0]=(max(0,loc[0][0]-1),max(0,loc[0][1]-1))
        look()

    def S():
        worldview[loc[0]].image=backup[0]
        loc[0]=(loc[0][0],min(height,loc[0][1]+1))
        look()

    def W():
        worldview[loc[0]].image=backup[0]
        loc[0]=(max(0,loc[0][0]-1),loc[0][1])
        look()

    def E():
        worldview[loc[0]].image=backup[0]
        loc[0]=(min(width,loc[0][0]+1),loc[0][1])
        look()

    def SE():
        worldview[loc[0]].image=backup[0]
        loc[0]=(min(width,loc[0][0]+1),min(height,loc[0][1]+1))
        look()

    ctx=Context.getContext()

    look_handler=input_handling.InputHandler()
    look_handler.addFunction(SE, K_j)
    look_handler.addFunction(NW, K_k)
    look_handler.addFunction(N, K_y)
    look_handler.addFunction(W, K_u)
    look_handler.addFunction(E, K_b)
    look_handler.addFunction(S, K_n)
    look_handler.addFunction(quitLook, K_q)
    look_handler.addFunction(quitLook, K_ESCAPE)
    ctx.screen_manager.current.handlers.push(look_handler)

    backup=[None]
    cursor=globals.font.render('X',True,(255,255,100))
    message_buffer=ctx.message_buffer
    perception=ctx.pc.perception
    loc=[ctx.pc.parent.loc]
    original_loc=ctx.pc.parent.loc
    previous_loc=[ctx.pc.parent.loc]
    worldview=ctx.worldview
    (width,height)=(worldview.width-1,worldview.height-1)
    screen_manager=ctx.screen_manager

    look()
