#!/usr/bin/env python
from Queue import Queue

class BitQueue(Queue):
    """A trivial helper class that allows reading and writing bits OR bytes."""
    def __init__(self):
        Queue.__init__(self)

x=BitQueue()
print x
