#!/usr/bin/env python
from time import sleep,time
from collections import deque

class CovertChannel():
    """This object uses packet delays to send and receive data over a covert channel 
    concealed in a cover channel (socket)."""
    def __init__(self):
        self.packettimes=deque()

    def record_packet(self):
        """This function records the time that this packet was received."""
        self.packettimes.append(time())

    def induce_jitter(self):
        """This function modulates a signal by delaying or not delaying outbound 
        packets."""
        pass

