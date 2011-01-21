import pygame.font

__all__=['MonoFont']

def init():
    pygame.font.init()

class MonoFont(pygame.font.Font):
    def __init__(self, *args):
        pygame.font.Font.__init__(self, *args)
        assert(self.size('@')==self.size('i'))
        (self._w,self._h)=self.size('@')
    
    def getW(self):
        return self._w

    w=property(getW,None)

    def getH(self):
        return self._h

    h=property(getH,None)
