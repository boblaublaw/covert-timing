#!/usr/bin/env python
from netfilterqueue import NetfilterQueue, COPY_META
from time import sleep,time
from sys import exc_info
import threading
import subprocess
from atexit import register

globalconnspecnum=0

class NetfilterQueueWrapper(NetfilterQueue):
    """NetfilterQueueWrapper is an object used to set up and tear down NFQUEUE iptables rules."""

    def __init__(self, table='INPUT', ip='127.0.0.1', proto='tcp', port='6667', callback=None):
        super(NetfilterQueueWrapper,self).__init__()
        global globalconnspecnum
        self.connspec=''
        globalconnspecnum += 1
        self.connspecnum = globalconnspecnum
        self.callback=callback

        # create the rule specification
        self.connspec = table + ' -d ' + ip + '/32 -p ' + proto + ' --dport ' + port + ' -j NFQUEUE --queue-num ' + str(self.connspecnum)

        # run the appropriate iptables command and make sure it finishes
        p = subprocess.Popen('iptables -I ' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()

        # associate the NFQUEUE number with the wrapper function 
        self.bind(self.connspecnum, self.wrapper_func, mode=COPY_META)

        # we explicitly clean up before destructors get called
        register(self.cleanup)

        # launch a thread to listen for the callback method
        t = threading.Thread(target=self.run, args = ())

        # we have no way to stop these threads once they are launched, so we mark them as daemons
        t.daemon=True
        t.start()

    def wrapper_func(self, pkt):
        """This function ensures that we dont forget to accept the intercepted packet."""
        if self.callback != None:
            self.callback()
        pkt.accept()

    def cleanup(self):
        """This will tear down the nfqueue and issue the iptables command to stop interfering with the traffic."""
        if self.connspecnum != None:
            p = subprocess.Popen('iptables -D' + self.connspec, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval=p.wait()
            self.connspec=''
            self.connspecnum=None
            super(NetfilterQueueWrapper,self).unbind()

class analyzer():
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

def netstatSelect():
    """This function will prompt the user for a locally terminated connection using netstat."""
    p = subprocess.Popen('netstat -W -n -a -A inet | grep ESTABLISHED', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval=p.wait()
    connections=map(lambda line: line.rstrip(), p.stdout.readlines())

    if len(connections) == 0:
        print 'No active connections detected.'
        return

    # show the netstat output as numbered lines
    lineNumber=1
    for line in connections:
        print str(lineNumber) + ': ' + line
        lineNumber+=1

    print "Select line number: "
    selectedLine=int(raw_input()) - 1

    #tcp        0      0 172.16.65.148:ssh       172.16.65.1:53698       ESTABLISHED
    proto, ignore1, ignore2, dst, src, ignore3 = connections[selectedLine].split()
    rip,rport = src.split(':')
    lip,lport = dst.split(':')

    # create two dictionaries and return them
    remote={ 'table':'OUTPUT', 'ip':rip, 'proto':proto, 'port':rport }
    local= { 'table':'INPUT',  'ip':lip, 'proto':proto, 'port':lport }
    return local, remote

try:
    # create an analyzer object 
    a=analyzer()

    # use the netstatSelect method to select a locally terminated connection
    local, remote = netstatSelect()

    # assign the callback Functions
    local['callback'] = a.measure_jitter
    remote['callback'] = a.induce_jitter

    localShim = NetfilterQueueWrapper(**local)
    remoteShim = NetfilterQueueWrapper(**remote)

    # this is where interactive input and output would be handled
    while 1:
        sleep(0.1)
        # interactive stuff happens here

except KeyboardInterrupt:
    print "all done."

# vi: set ts=4 sw=4 expandtab: 
