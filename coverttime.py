#!/usr/bin/env python
from time import sleep,time

class CovertChannel():
    """This object uses packet delays to modulate a covert channel over a cover channel (socket)."""
    def __init__(self):
        self.last=None
        self.biggest=None
        print 'starting up'
    def measure_jitter(self):
        """this function measures the time that has elapsed since the last time it was called"""
        now=time()
        if self.last != None:
            delay = now - self.last
            if self.biggest == None:
                self.biggest=delay
            elif self.biggest < delay:
                self.biggest=delay
            print delay, self.biggest
        self.last=now
    def induce_jitter(self):
        pass
