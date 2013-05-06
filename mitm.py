#!/usr/bin/env python
from netfilterqueue import NetfilterQueue
from time import sleep,time
from sys import exc_info
import threading
import subprocess
from atexit import register

globalconnspecnum=0

class ConnectionShim(NetfilterQueue):
    def __init__(self, queuename, ip, proto, port):
        global globalconnspecnum
        self.connspec=''
        self.func=None
        self.last=None
        self.biggest=None
        globalconnspecnum += 1
        self.connspecnum = globalconnspecnum
        self.connspec = queuename + ' -d ' + ip + '/32 -p ' + proto + ' --dport ' + port + ' -j NFQUEUE --queue-num ' + str(self.connspecnum)
        print '\niptables -I ' + self.connspec + '\n'
        p = subprocess.Popen('iptables -I ' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()
        self.bind(self.connspecnum, self.wrapper_func)

    def assign(self, func):
        self.func=func

    def wrapper_func(self, pkt):
        if self.func != None:
            self.func()
        pkt.accept()
        
    def cleanup(self):
        """This will tear down the nfqueue and issue the iptables command to stop interfering with the traffic."""
        global globalconnspecnum
        self.unbind()
        p = subprocess.Popen('iptables -D' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()
        self.connspec=''
        self.connspec=0
        globalconnspecnum-=1

    def __del__(self):
        """This destructor just calls the named cleanup function"""
        self.cleanup()

    def mitm(self):
        """Essentially just a wrapper for nfqueue.run()"""
        print 'starting mitm()'
        self.run()

class ConnectionManager():
    """Object to select an active socket connection and divert it to the netfilter queue"""

    def __init__(self):
        self.refresh()

    def refresh(self):
        """this function will refresh the connect listing."""
        p = subprocess.Popen('netstat -W -n -a -A inet | grep ESTABLISHED', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()
        self.connections=map(lambda line: line.rstrip(), p.stdout.readlines())
        
    def select(self):
        """This function will prompt the user for a locally terminated connection.  Once selected, the traffic will be redirected to a NFQUEUE."""
        lineNumber=1
        for line in self.connections:
            print str(lineNumber) + ': ' + line
            lineNumber+=1
        print "Select line number: "
        selectedLine=int(raw_input()) - 1
        #tcp        0      0 172.16.65.148:ssh       172.16.65.1:53698       ESTABLISHED
        proto, ignore1, ignore2, dst, src, ignore3 = self.connections[selectedLine].split()
        rip,rport = src.split(':')
        lip,lport = dst.split(':')

        print "remote host is " + rip
        # capture the traffic from the remote host
        outboundShim=ConnectionShim('INPUT',rip,proto,rport)

        # capture the traffic to the remote host
        print "local host is " + lip
        inboundShim=ConnectionShim('INPUT',lip,proto,lport)

        return inboundShim, outboundShim

class analyzer():
    def __init__(self):
        self.last=None
        self.biggest=None
        print 'starting up'
    def measure_jitter(self):
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
        print "and back again"

try:
    # create a connection manager 
    CM=ConnectionManager()

    # select a connection
    inboundShim, outboundShim = CM.select()

    # we explicitly clean up before destructors get called
    register(inboundShim.cleanup)
    register(outboundShim.cleanup)

    # create an analyzer object to listen to traffic
    a=analyzer()
    inboundShim.assign(a.measure_jitter)
    outboundShim.assign(a.induce_jitter)

    # launch a thread for each shim
    t1 = threading.Thread(target=inboundShim.mitm, args = ())
    t2 = threading.Thread(target=outboundShim.mitm, args = ())
    t1.daemon=True
    t2.daemon=True
    t1.start()
    t2.start()

    # this is where interactive input and output would be handled
    while 1:
        sleep(0.1)
        # stuff happens here

except KeyboardInterrupt:
    print "all done."
except:
    print "Unexpected error:", exc_info()[0]
    raise

# vi: set ts=4 sw=4 expandtab: 
