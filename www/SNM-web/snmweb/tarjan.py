#!/usr/bin/python

import json
import re
from os import walk
import os
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime as dt
import datetime
import pdb
import numpy
import json
import cPickle
    
class Tie:
    def __init__(self, v):
        self.v = v
    def __lt__(self, other):
        if (self.v["static"] < other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] < other["logical"]
        else:
           return False
    def __gt__(self, other):
        if (self.v["static"] > other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] > other["logical"]
        else:
           return False
    def __eq__(self, other):
        if (self.v["static"] == other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] > other["logical"]
        else:
           return False
    def toPair(self): return (self.v["static"], self.v["logical"])
    def fromPair(self, p): 
        self.v["static"] = p[0]
        self.v["logical"] = p[1]
   

def clusteringOrder(nodes, links):

    distinctIds = [l["id"] for l in nodes]
    distinctNames = [l["name"] for l in nodes]
    nLabels = nodes
    n = len(nLabels)
    lookup = { nLabels[i]["id"]: i for i in range(0,n) }
    dsm = numpy.zeros((n,n), dtype=('i4,i4'))

    for l in links:
       dsm[lookup[l["source"]], lookup[l["target"]]] = (l["value"]["static"], l["value"]["logical"])

    for i in range(0,n): dsm[i,i] = (500,500)
    g = Graph(dsm, distinctIds)

    g.sortByOutdegree()
    g.tarjan()
    
    #NB: something's horribly wrong with it's neck at this point
    # (g.nLabels has lots of duplicates at the front)
    #
    return sorted(nodes, key=lambda n: g.lookup[n["id"]])

class Graph:
    def __init__(self, dsm, nLabels):
        self.dsm = dsm
        self.nLabels = nLabels
        self.n = len(nLabels)
        self.mkLookup()

    def invariant(self):
        assert self.n == len(self.nLabels), "Not N labels"
        assert self.n == len(set(self.nLabels)), "Not N distinct labels"
 
    def mkLookup(self):
        self.lookup = { self.nLabels[i]: i for i in range(0,self.n) }

    def swapper(self, aname, bname):
        self.invariant()
        a = self.lookup[aname]
        b = self.lookup[bname]
        self.dsm[:, [a,b]] = self.dsm[:, [b,a]]
        self.dsm[[a,b], :] = self.dsm[[b,a], :]
        self.nLabels[a] = bname
        self.nLabels[b] = aname
        self.mkLookup()
        self.invariant()

    def reorderBy(self, newindexing):
        self.invariant()
        self.dsm[:, range(0,self.n)] = self.dsm[:, newindexing]
        self.dsm[range(0,self.n), :] = self.dsm[newindexing, :]
        self.nLabels = {nu: self.nLabels[newindexing[nu]] for nu in range(0,self.n)}
        #self.nLabels = {newindexing[old]: self.nLabels[old] for old in range(0,self.n)}
        self.mkLookup()
        self.invariant()

    def sortByOutdegree(self):
        self.invariant()
        neworder = self.nLabels[:]
        def outdegree(nodename):
            return len(numpy.extract(lambda l: l["static"] > 0 or l["logical"] > 0, self.dsm[self.lookup[nodename],:]))
        neworder = sorted(neworder, key=outdegree)
        self.reorderBy([self.lookup[lab] for lab in neworder])
        self.invariant()

    def strongconnect(self, v):
        n = self.n
        self.indices[v] = self.index
        self.lowlinks[v] = self.index
        self.index += 1
        self.s.append(v)
   
        for w in range(0,n):
            if self.dsm[v,w][0] > 0 or self.dsm[v,w][1] > 0:
                if w not in self.indices:
                    self.strongconnect(w)
                    self.lowlinks[v] = min(self.lowlinks[v], self.lowlinks[w])
                elif w in self.s:
                    self.lowlinks[v] = min(self.lowlinks[v], self.indices[w])
        if self.lowlinks[v] == self.indices[v]:
            self.scc1 = []
            while True:
                w = self.s.pop()
                self.scc1.append(w)
                self.neworder.append(w)
                if (w == v): break
            self.sccs.append(self.scc1) 
  

    def tarjan(self):
        n = self.n
        # Find a root
        
        self.invariant()
        self.indices = dict()
        self.lowlinks = dict()
        self.index = 0
        self.s = []
        self.sccs = []
        self.neworder = []
        for v in range(0,n):
            if v not in self.indices:
                self.strongconnect(v)
        
        self.reorderBy(self.neworder)
        self.invariant()


