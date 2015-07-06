#!/usr/bin/env python
from time import sleep,time
from collections import deque

class CovertChannel():
    """This object uses packet delays to send and receive data over a covert channel 
    concealed in a cover channel (socket)."""
    def __init__(self):
        self.packetTimes=deque()
        self.lastPacketTime=None
        self.delays=deque()
        self.index=0

    def record_packet(self):
        """This function records the time that this packet was received."""
        self.packetTimes.append( [ self.index, time() ] )
        self.index = self.index + 1

    def induce_jitter(self):
        """This function modulates a signal by delaying or not delaying outbound 
        packets."""
        #sleep(1.0)
        pass

    def calculate_delays(self):
        """This function measures the time between packets."""
        if len(self.packetTimes) > 1:
            if self.lastPacketTime == None:
                self.lastPacketTime = self.packetTimes.popleft()[1]

        count=0
        while len(self.packetTimes) > 1:
            count=count+1
            thisPacket = self.packetTimes.popleft() 
            self.delays.append( [ thisPacket[0], thisPacket[1], thisPacket[1] - self.lastPacketTime ] )
            self.lastPacketTime = thisPacket[1]
        return count
        
