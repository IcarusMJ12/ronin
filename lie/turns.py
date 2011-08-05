# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

class TurnManager(object):
    def __init__(self):
        self._phases=[]
    
    def run(self):
        while True:
            for phase in self._phases:
                phase.run()
    
    def add(self, phase):
        assert(isinstance(phase,TurnPhase))
        self._phases.append(phase)

class TurnPhase(object):
    def __init__(self, phase):
        assert(phase is not None)
        assert(hasattr(phase,'__call__'))
        self._pre=None
        self._phase=phase
        self._post=None
    
    def run(self):
        if self._pre is not None:
            self._pre()
        while not self._phase():
            pass
        if self._post is not None:
            self._post()
    
    def setPre(self, pre):
        if pre is not None:
            assert(hasattr(pre,'__call__'))
        self._pre=pre
    
    pre=property(None, setPre)
    
    def setPost(self, post):
        if post is not None:
            assert(hasattr(post,'__call__'))
        self._post=post

    post=property(None, setPost)
