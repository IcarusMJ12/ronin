# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import logging

logger=logging.getLogger(__name__)

class InputHandlerManager(object):
    def __init__(self, handler):
        self._input_handlers=[handler]
    
    def push(self, handler):
        self._input_handlers.insert(0,handler)
    
    def pop(self):
        assert(len(self._input_handlers)>1)
        self._input_handlers.pop(0)
    
    def handle(self,event):
        handler=self._input_handlers[0]
        (f,args,kw)=handler.getFunction(event.key, event.mod)
        if f:
            return f(*args, **kw)
        return None

class InputHandler(object):
    def __init__(self):
        self.funcs={}

    def addFunction(self, function, key, mods=(0,), *args, **kw):
        if key not in self.funcs.keys():
            self.funcs[key]={}
        self.funcs[key][mods]=(function, args, kw)
    
    def getFunction(self, key, mod):
        try:
            mod_map = self.funcs[key]
        except KeyError:
            return (None,None,None)
        logger.debug(str(mod_map))
        for k,f in mod_map.items():
            match=True
            cum_mod=0
            for m in k:
                cum_mod|=m
                if m and not m & mod:
                    match=False
                    break
            if mod & ~cum_mod:
                match=False
            if match:
                return f
        return (None,None,None)
