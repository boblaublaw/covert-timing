#!/usr/bin/env python
from netfilterqueue import NetfilterQueue
from time import sleep,time
from sys import exc_info
import threading
import subprocess
from atexit import register

# packet methods
dox="""
>>> dir (netfilterqueue.Packet)
['__class__', '__delattr__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__new__', '__pyx_vtable__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'accept', 'drop', 'get_payload', 'get_payload_len', 'get_timestamp', 'hook', 'hw_protocol', 'id', 'payload', 'set_mark']
>>> dir (netfilterqueue.NetfilterQueue)
['__class__', '__delattr__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'bind', 'run', 'unbind']
>>> print (netfilterqueue.NetfilterQueue.__doc__)
Handle a single numbered queue.
>>> print (netfilterqueue.Packet.__doc__)
A packet received from QueueHandler.
>>> print (netfilterqueue.Packet.accept.__doc__)
Accept the packet.
>>> print (netfilterqueue.Packet.drop.__doc__)
Drop the packet.
>>> print (netfilterqueue.NetfilterQueue.run.__doc__)
Begin accepting packets.
>>> print (netfilterqueue.NetfilterQueue.bind.__doc__)
Create and bind to a new queue.
>>> print (netfilterqueue.NetfilterQueue.unbind.__doc__)
Destroy the queue."""

class ConnectionShim(NetfilterQueue):
    """Object to select an active socket connection and divert it to the netfilter queue"""

    def __init__(self):
        self.connspec=''
        self.last=None
        self.biggest=None
        self.refresh()

    def refresh(self):
        """this function will refresh the connect listing."""
        p = subprocess.Popen('netstat -W -n -a -A inet | grep ESTABLISHED', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()
        self.connections=map(lambda line: line.rstrip(), p.stdout.readlines())
        
    def select(self):
        """This function will prompt the user for a connection.  Once selected, the traffic will be redirected to a NFQUEUE."""
        lineNumber=1
        for line in self.connections:
            print str(lineNumber) + ': ' + line
            lineNumber+=1
        print "Select line number: "
        selectedLine=int(raw_input()) - 1
        #tcp        0      0 172.16.65.148:ssh       172.16.65.1:53698       ESTABLISHED
        proto, ignore1, ignore2, src, dst, ignore3 = self.connections[selectedLine].split()
        sip,sport = src.split(':')
        dip,dport = dst.split(':')
        if self.connspec == '':
            self.connspec = 'INPUT -d ' + sip + '/32 -p ' + proto + ' --dport ' + sport + ' -j NFQUEUE --queue-num 1'
            p = subprocess.Popen('iptables -I' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval=p.wait()
            self.bind(1, self.print_and_accept)

    def cleanup(self):
        """This will tear down the nfqueue and issue the iptables command to stop interfering with the traffic."""
        self.unbind()
        if self.connspec != '':
            p = subprocess.Popen('iptables -D' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval=p.wait()
            self.connspec=''
   
    def __del__(self): 
        """This destructor just calls the named cleanup function"""
        self.cleanup()

    def print_and_accept(self,pkt):
        """This is the callback function for nfqueue"""
        now=time()
        if self.last != None:
            delay = now - self.last
            if self.biggest == None:
                self.biggest=delay
            elif self.biggest < delay:
                self.biggest=delay
        self.last=now
        print pkt, delay, self.biggest
        pkt.accept()

    def mitm(self):
        """Essentially just a wrapper for nfqueue.run()"""
        self.run()

try:
    # create a connection manager 
    CS=ConnectionShim()
    # we explicitly clean up before destructors get called
    register(CS.cleanup)
    # select a connection
    CS.select()
    # start receiving the INPUT packets for the selected connection
    CS.mitm()
except KeyboardInterrupt:
    print "all done."
except:
    print "Unexpected error:", exc_info()[0]
    raise

# vi: set ts=4 sw=4 expandtab: 
