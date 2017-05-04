import time
import os
import subprocess
import copy
import sys
import pdb

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import profiler_log_stats
from param_dict import profiling_params
from database.rel_profile import schema0


class ProfilerDebug(object):
    @staticmethod
    def calc_time(start, end):
        '''track how long the profiling session takes to complete'''
        end_sec = end.tm_hour * 3600 + end.tm_min * 60 + end.tm_sec
        if end.tm_hour >= start.tm_hour:
            tot_sec = end_sec - (start.tm_hour * 3600 + \
                                     start.tm_min * 60 + \
                                     start.tm_sec)
        else:
            tot_sec = end_sec + ((23 - start.tm_hour) * 3600 + \
                                     (59 - start.tm_min) * 60 + \
                                     (60 - start.tm_sec))
        h = 0
        m = 0
        if tot_sec > 60:
            if tot_sec > 3600:
                h = tot_sec / 3600
            m = (tot_sec - h*3600) / 60
        s = (tot_sec - h*3600 - m*60)
        return (h, m, s)

    @staticmethod
    def print_measurements(case, ms):
        max_len = 0
        for node in ms:
            if len(node) > max_len:
                max_len = len(node)
        spacing = 10
        print '*\n*\n*\t\tNODE%sAVG \tMAX\n*' % (' ' * (max_len - 4 + spacing))
        for node in sorted(ms):
            print '*\t\t%s%s%.2f\t%.2f' % (node, ' '*(max_len - len(node) + spacing), ms[node][1], ms[node][0])
        print '*\n*\n*'
                                 
    def __init__(self, args):
        # parse configuration files and create param dictionary
        self._params = profiling_params(args['cases_fn'], 
                                        args['bin'],
                                        args['buildconfig'],
                                        args['bkndtgt'],
                                        args['n_trials'],
                                        args['project'],
                                        0,
                                        '')

        print '\n' + '*'*30 + ' Profile ' + '*'*30

        # only supporting prof_ssh session type for now
        self._session = sessions.prof_ssh(self._params, args['verbose'])

        
    def run(self):        
        start = time.localtime()
            
        try:
            noerror = True
            # execute all cases
            bin = self._params['exename']
            #if 'multicore' in self._params['project']:
                #self._session.set_num_threads(1)
            for label, fps, case in self._params['cases']:
                print '*\tcommand-line:\n*\t\t{0} {1}'.format(bin, case)
                try:
                    self._session.execute('{0} {1}'.format(bin, case))
                except Exception as e:
                    print '\nError while executing case:\n\t' + str(e)
                    noerror = False

                # derive absolute log paths
                logs = ['%s/%s' % \
                            (self._params['local_res_dir'], log) \
                            for log in os.listdir(self._params['local_res_dir'])]
                # get measurement stats from logs
                measurements = stats.get_all_min_stats(logs,
                                                       fps)
                ProfilerDebug.print_measurements(case, measurements)
        finally:
            self._session.exit()

        # calculate total profiling time
        end = time.localtime()
        print '*\ttotal time to profile: %02d:%02d:%02d' % \
            ProfilerDebug.calc_time(start, end)
        print '*'*70
        return noerror

class Profiler(ProfilerDebug):
    
    
    def __init__(self, args):
        self._params = args
        #self._params = profiling_params(args['cases_fn'], 
        #                                args['bin'],
        #                                args['buildconfig'],
        #                                args['bkndtgt'],
        #                                args['n_trials'],
        #                                args['project'], 
        #                                args['changelist'],
        #                                args['node'])
                
        self._db = schema0(self._params)

    def run(self):
        # nested function for handling insertion of max and avg values
        def insert_values(test_table_name, values):

            for key, value in values.items():
                test_case_name = key
                max_value = value['Max']
                min_value = value['Min']
                avg_value = value['Avg']
                unitperf = "cycle"
                cmd = value['cmd']
                backend = value['backend']
                board = value['board']
                target = value['target']
                os = value['os']
                arch = value['arch']
                changelist = value['changelist']
                compiler = value['compiler']
                glibc = value['glibc']

                try:
                    self._db.insert_profile_table(test_table_name, test_case_name, max_value, min_value, avg_value, unitperf, cmd, backend, board, target, os, arch, changelist, compiler, glibc)
                except Exception as e:
                    print 'Error inserting measurement into database:\n\t' + str(e)
                    return False
                        
        try:
            noerror = True
            
            # derive absolute log paths
            log_file1 = self._params['logfile1']
            log_file2 = self._params['logfile2']
            values2 = profiler_log_stats.parse_environment_report(log_file2)
            values1 = profiler_log_stats.parse_profile_report(log_file1)
            for key, value in values1.items():
                value.update(values2)
            test_table_name = self._params['table_name']

            # add node measurement to database
            #values = stats.get_min_stats(logs,
            #                             self._params['node'],
            #                             fps
            #                             )

            if insert_values(test_table_name, values1) is False:
                noerror = False
            return noerror
        finally:
            return True
