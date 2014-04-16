#!/usr/bin/python

import csv
import pprint

class ZaberASCIISettingSugar(object):
    _base = None

    def __init__(self,base=''):
        self._base = base

    def __str__(self):
        return self._base

    def __setattr__(self,k,v):
        if k == '_base': 
            return object.__setattr__(self,k,v)
        pass

    def __getattr__(self,k):
        node_str = self._base + "." + k if self._base else k
        return ZaberASCIISettingSugar(node_str)

c = ZaberASCIISettingSugar()
print c.foo.bar
c.foo.bar = "hoser"

class ZaberASCIISettingTreeNode(object):

    def __init__(self,node,base=None):
        self._node = node
        self._base = base
        self._lookup = {}

    def __str__(self):
        return self._base

    def __getattr__(self,k):
        if k in self._lookup:
            return self._lookup[k]

        if k in self._node:
            node_str = self._base + "." + k if self._base else k
            node = ZaberASCIISettingTreeNode(self._node[k],node_str)
            self._lookup[k] = node
            return node

        raise AttributeError()

in_fh = csv.DictReader(open("ascii-settings.csv"))
root_base = {}
for r in in_fh:
    rows = r['setting'].split('.')

    index = root_base
    for c in rows:
        index.setdefault(c,{})
        index = index[c]

pprint.pprint( root_base.keys() )

n = ZaberASCIISettingTreeNode(root_base)

print n.comm.protocol

