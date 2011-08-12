# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

class TurnManager(object):
    def __init__(self):
        self._phases=[]
        self._completed_phases=[]
    
    def run(self):
        while True:
            try:
                phase=self._phases[0]
            except IndexError:
                self._phases=self._completed_phases
                continue
            phase.run()
            self._completed_phases.append(self._phases.pop(0))
    
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
        self._current=0
    
    def run(self):
        if self._current==0:
            if self._pre is not None:
                self._pre()
            self._current+=1
        if self._current==1:
            while not self._phase():
                pass
            self._current+=1
        if self._current==2:
            if self._post is not None:
                self._post()
            self._current=0
    
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
