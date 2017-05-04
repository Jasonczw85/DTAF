import re
from matplotlib import pyplot as plt
from numpy import ceil

import pdb
import os, sys
BASE = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(BASE)

from utils import utils

node_line = re.compile('.*Node Name\s*:\s*(\w+)')
max_line = re.compile('.*Max\s*:\s*([0-9]+)')
avg_line = re.compile('.*Avg\s*:\s*([0-9\.]+)')
min_line = re.compile('.*Min\s*:\s*([0-9]+)')
#ncalls_line = re.compile('.*Number of Calls\s*:\s*([0-9]+)')
pats = {'Max': max_line, 'Avg': avg_line, 'Min': min_line}#, 'NCalls': ncalls_line}

def parse_profile_report(log):
    report = {}
    report_key = {}
    node_set = False

    def store_if_match(pat, line, label):
        #pdb.set_trace()
        m = pat.match(line)
        if m is not None:
            report[cur_node][label] = float(m.group(1))
            #pdb.set_trace() 
            return True
        else:
            return False

    with open(log) as lf:
        for line in lf:
            m = node_line.match(line)
            if m is not None and m.group(1) != 'Root':
                cur_node = m.group(1)
                report[cur_node] = {}
                node_set = True
            if node_set:    
                for label in pats.keys():
                    if store_if_match(pats[label],
                                      line,
                                      label):
                        break

    return get_frame_stats(report, 'ddpi_enc_process')

def parse_environment_report(log):

    report = {}
    with open(log) as lf:
        for line in lf:
            line_list = line.split('=')
            # delete the '\n' in the end of the line_list[1]
            report[line_list[0]] = line_list[1][:-1]

    return report

def get_frame_stats(report, frame_node):
    #pdb.set_trace()
    if report.has_key(frame_node) and len(report) > 1:
        new_rep = {}
        total_frames = report[frame_node]['NCalls']
        new_rep[frame_node] = {}
        new_rep[frame_node].update(report[frame_node])
        for key in report:
            if not report[key].has_key('NCalls'):
                continue
            if key != frame_node:
                new_rep[key] = {}
                if total_frames < report[key]['NCalls']:
                    scale = ceil(report[key]['NCalls'] / total_frames)
                else:
                    scale = 1
                new_rep[key]['Max'] = report[key]['Max'] * scale
                new_rep[key]['Min'] = report[key]['Min'] * scale
                new_rep[key]['Avg'] = report[key]['Avg'] * scale
        return new_rep
    else:
        return report


def make_master_report(logs):
    master_report = {}
    stat_dict = lambda: {'Max':[],'Avg':[],'Min':[]}

    for log in logs:
        if log[-4:] != '.log':
            continue
        report = parse_profile_report(log)
        for node, stats in report.items():
            if node not in master_report:
                master_report[node] = stat_dict()
            for stat, value in stats.items():
                if stat in stat_dict():
                    master_report[node][stat].append(value)
    
    return master_report

def get_min_stats(logs, node, fps):
    rep = make_master_report(logs)
    fmt = lambda v: round(fps * v / 1000000.0, 2)
    minmax = fmt(min(rep[node]['Max'])) 
    minavg = fmt(min(rep[node]['Avg'])) 
    minmin = fmt(min(rep[node]['Min'])) 
    return (minmax, minavg, minmin)

def get_all_min_stats(logs, fps):
    fmt = lambda v: round(fps * v / 1000000.0, 2)
    rep = make_master_report(logs)
    all_stats = {}
    for node in rep:
        minmax = fmt(min(rep[node]['Max']))
        minavg = fmt(min(rep[node]['Avg']))
        all_stats[node] = (minmax, minavg) 
    return all_stats