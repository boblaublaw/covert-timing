#!/usr/bin/env python
from netfilterqueue import NetfilterQueue, COPY_META
import threading
from time import sleep
import subprocess
from atexit import register

globalconnspecnum=0

class NetfilterQueueWrapper(NetfilterQueue):
    """NetfilterQueueWrapper is an object used to set up and tear down NFQUEUE iptables rules."""

    def __init__(self, table='INPUT', proto='tcp', dip='127.0.0.1', dport='6667', sip='127.0.0.1', sport='6668', callback=None):
        super(NetfilterQueueWrapper,self).__init__()
        global globalconnspecnum
        self.connspec=''
        globalconnspecnum += 1
        self.connspecnum = globalconnspecnum
        self.callback=callback

        # create the rule specification
        self.connspec = table + ' -p ' + proto
        self.connspec = self.connspec + ' -d ' + dip + '/32 --dport ' + dport 
        self.connspec = self.connspec + ' -s ' + sip + '/32 --sport ' + sport
        self.connspec = self.connspec + ' -j NFQUEUE --queue-num ' + str(self.connspecnum)

        # run the appropriate iptables command and make sure it finishes
        cmd = 'iptables -I ' + self.connspec
        #print cmd
        #sleep(10)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval=p.wait()
        #print str(retval) + ' '
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
        """This will tear down the nfqueue and issue the iptables command to stop interfering 
        with the traffic."""
        if self.connspecnum != None:
            cmd = 'iptables -D' + self.connspec
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            retval=p.wait()
            self.connspec=''
            self.connspecnum=None
            super(NetfilterQueueWrapper,self).unbind()

# vi: set ts=4 sw=4 expandtab: 
