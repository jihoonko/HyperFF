import collections
import math
import os
import random
from random import shuffle
import time

import numpy as np
import tqdm

from hypergraph import Hypergraph

class blocks:        
    def createModel(g):
        for i in tqdm.trange(1, g.tspan+1): # assumes "tspan" additional new nodes
            amb = np.random.randint(0, g.n)
            g.n += 1
            g.nodet.append(i)
            g.firing(amb, i)
    
    def enlargeModel(g, morenodes):
        for i in range(g.n, g.n+morenodes):
            amb = np.random.randint(0, g.n)
            g.n += 1
            g.nodet.append(i)
            g.firing(amb, i)
    
    def acceptProb(g, newedge):
        current_size = len(g.e2n[newedge])
        return (current_size / (current_size + 1))**(g.q)
   
    def strongTies(g, node, option="strength"):
        adjs = g.weight_total[node]
        nbds = list(adjs.keys())
        if not nbds: return []
        if option == "random":
            shuffle(nbds)
            return nbds
        elif option == "strength":
            shuffle(nbds)
            return sorted(nbds, key=adjs.get, reverse=True)
    
    def addNode2Edge_noweight(g, node, edge):
        nodes = g.e2n[edge]
        g.n2e[node].append(edge)
        g.e2n[edge].append(node)

class HyperFF(Hypergraph):
    def __init__(self, forward, expan_param, time_span, random_seed = 1000):
        super(HyperFF, self).__init__('model', None)
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.p = forward
        self.q = expan_param
        self.tspan = time_span
        self.n, self.e = 1, 0
        self.n2e, self.e2n = [[]], []
        self.weight_total = [{}]
        self.nodet, self.edget = [0], []
        self.infec = [0]
        self.infec_counter = {}
        self.create()

        self.edges = [(t, edge) for t, edge in zip(self.edget, self.e2n)]
        self.idx2node = {i:i for i in range(self.n)}
        self.nodes = [(t, node) for t, node in zip(self.nodet, range(self.n))]
        self.node2edge = [sorted(indices) for indices in self.n2e]
        self.datatype = 'model'

    def nodenum(self): return self.n
    def edgenum(self): return self.e    
    def degree(self, node): return len(self.n2e[node])
    def create(self): blocks.createModel(self)
    def enlarge(self, morenodes): blocks.enlargeModel(self, morenodes)
    
    def firing(self, source, newnode):
        visit = set({source})
        queue = collections.deque([source])
        newedges = []
        self.weight_total.append({})
        self.n2e.append([])
        infection = 0
        
        while queue:
            s = queue.popleft()
            prev_len = len(queue)
            newedge = self.formEdge(s, newnode)
            self.e += 1
            self.edget.append(self.n-1)
            newedges.append(newedge)
            
            num = np.random.geometric(1-self.p)-1
            raw_candidates = blocks.strongTies(self, s)
            queue, visit = self.getCandidates_form(raw_candidates, num, s, newnode, queue, visit)    
            infection += len(queue) - prev_len
        self.infec_counter[infection] = self.infec_counter.get(infection, 0) + 1
        self.infec.append(infection)
        
        for edge in newedges:
            self.expandEdge_deter(edge)

    def getCandidates_form(self, cands, num, amb, newnode, queue, visit):
        counter = 0
        for nbr in cands:
            if nbr == newnode:
                continue
            if nbr not in visit:
                if counter >= num:
                    break
                counter += 1
                queue.append(nbr)
                visit.add(nbr)
        return queue, visit
    
    def formEdge(self, amb, newnode):
        self.weight_total[newnode][amb] = self.weight_total[newnode].get(amb, 0) + 1
        self.weight_total[amb][newnode] = self.weight_total[amb].get(newnode, 0) + 1
        self.n2e[amb].append(self.e)
        self.n2e[newnode].append(self.e)
        self.e2n.append([newnode, amb])
        return self.e
    
    def getCandidates_expand(self, cands, num, amb, newedge, newnode, queue, visit):
        counter = 0
        for nbr in cands:
            if nbr == newnode:
                continue
            if nbr not in visit:
                if counter >= num:
                    break
                counter += 1
                queue.append(nbr)
                visit.add(nbr)
                blocks.addNode2Edge_noweight(self, nbr, newedge)
        return queue, visit
    
    def expandEdge_deter(self, newedge):
        visit = set({self.e2n[newedge][0], self.e2n[newedge][1]})
        queue = collections.deque([self.e2n[newedge][1]])
        
        while queue:
            s = queue.popleft()
            num = np.random.geometric(1-self.q)-1
            raw_candidates = blocks.strongTies(self, s)
            queue, visit = self.getCandidates_expand(raw_candidates, num, s, newedge, self.e2n[newedge][0], queue, visit)

            
class CGAHDynamic(Hypergraph):
    def __init__(self, b, c1, c2, time_span, random_seed = 1000):
        super(CGAHDynamic, self).__init__('model', None)
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.b = b
        self.c1 = c1
        self.c2 = c2
        self.tspan = time_span
        self.h = 0
        self.n = 0
        self.nodes = []
        while True:
            if (self.b ** self.h) + self.n > self.tspan:
                break
            else:
                for i in range(self.b ** self.h):
                    self.nodes.append((self.h+1, self.n + i))
                    
                self.n += (self.b ** self.h)
                self.h += 1
        self.dists = np.zeros((self.n, self.n))
        for i in tqdm.trange(self.n):
            for j in range(i):
                self.dists[i,j] = self.dists[j,i]
            for j in range(i+1, self.n):
                _i, _j, _d = i, j, 0
                while _i ^ _j:
                    if _i > _j: _i, _d = (_i - 1) // self.b, _d + 1
                    else: _j, _d = (_j - 1) // self.b, _d + 1
                self.dists[i, j] = -(_d / 2.0)
        
        self.idx2node = {i:i for i in range(self.n)}
        self.node2edge = [[] for i in range(self.n)]
        self.edges = []
        
        now_h, cum = 0, 0
        until = [0 for _ in range(self.n)]
        node_time = [0 for _ in range(self.n)]
        
        for i in tqdm.trange(self.n):
            until[i] = cum
            node_time[i] = now_h + 1
            if i == cum:
                now_h += 1
                cum += (self.b ** now_h)
        
        for i in tqdm.trange(self.n):
            for j in range(until[i]+1):
                if i == j: continue
                if np.random.random() < (self.c1 ** self.dists[i, j]):
                    now_e = [i, j]
                    for k in range(until[j]+1):
                        if k == i or k == j: continue
                        if np.random.random() < (self.c2 ** self.dists[j, k]):
                            now_e.append(k)
                    edge_idx = len(self.edges)
                    self.edges.append((node_time[i], now_e))
                    for v in now_e:
                        self.node2edge[v].append(edge_idx)
        self.datatype = 'cgah'