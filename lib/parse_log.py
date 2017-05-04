#!/usr/bin/env python

import re

_search_node_name = re.compile(r'Node Name.+\: (.+)$')
_search_total     = re.compile(r'Total .+\: (.+) ')
_search_max       = re.compile(r'Max .+\: (.+) ')
_search_min       = re.compile(r'Min .+\: (.+) ')
_search_avg       = re.compile(r'Avg .+\: (.+) ')
_search_num_calls = re.compile(r'Number of Calls.+\: (.+)$')
    
class ParsedProfilingReport(object):
    def __init__(self,file_path):
        self.file_path = file_path

    def proper_value(self, str_val):
        if ('.' in str_val) or ('e' in str_val):
            return float(str_val)
        else:
            return int(str_val)
        
    def parse(self):
        with open(self.file_path,'r') as fp:
            lines = fp.readlines()

        node = None
        node_list = []
        for l in lines:
            name_mo  = _search_node_name.search(l)
            total_mo = _search_total.search(l)
            max_mo   = _search_max.search(l)
            min_mo   = _search_min.search(l)
            nc_mo    = _search_num_calls.search(l)
            avg_mo   = _search_avg.search(l)
            if name_mo:
                name = name_mo.group(1)
                node = ProfilingNode(name,l)
                node_list.append(node)
            elif node:
                if total_mo:
                    total = int(total_mo.group(1))
                    node.set_total(total,l)
                elif max_mo:
                    m = self.proper_value(max_mo.group(1))
                    node.set_max(m,l)
                elif min_mo:
                    m = self.proper_value(min_mo.group(1))
                    node.set_min(m,l)
                elif nc_mo:
                    nc = int(nc_mo.group(1))
                    node.set_num_calls(nc,l)
                elif avg_mo:
                    avg = self.proper_value(avg_mo.group(1))
                    node.set_avg(avg,l)
                else:
                    node.set_space(l)
                
        return node_list

class ProfilingNode(object):

    _template = "{name}{total}{max}{min}{avg}{calls}{space}"

    def __init__(self,name,line):
        self.name  = ItemofNode(name,line)

        self.total     = None
        self.max       = None
        self.min       = None
        self.num_calls = None
        self.avg       = None
        self.space     = None

    def set_total(self,total,line):
        self.total = ItemofNode(total,line)
    def set_max(self,m,line):
        self.max = ItemofNode(m,line)
    def set_min(self,m,line):
        self.min = ItemofNode(m,line)
    def set_num_calls(self,nc,line):
        self.num_calls = ItemofNode(nc,line)
    def set_avg(self,avg,line):
        self.avg = ItemofNode(avg,line)
    def set_space(self,space):
        self.space = space
        
    def __str__(self):
        return ProfilingNode._template.format(
        name = self.name.line,
        total = self.total.line,
        max = self.max.line,
        min = self.min.line,
        avg = self.avg.line,
        calls = self.num_calls.line,
        space = self.space
        )

class ItemofNode(object):
    def __init__(self, key, line):
        self.key = key
        self.line = line
        
