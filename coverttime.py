#!/usr/bin/env python
from time import sleep,time
from Queue import Queue

class CovertChannel():
    """This object uses packet delays to send and receive data over a covert channel concealed in a cover channel (socket)."""
    def __init__(self):
        self.last=None
        self.delays=Queue()

    def measure_jitter(self):
        """This function measures the time that has elapsed since the last time it was called.  The delay is decoded as a signal."""
        now=time()
        if self.last != None:
            delay = now - self.last
            self.delays.put(delay)
        self.last=now

    def induce_jitter(self):
        """This function modulates a signal by delaying or not delaying outbound packets."""
        pass
