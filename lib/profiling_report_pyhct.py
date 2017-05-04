#import stats
#import matplotlib.pyplot as plt
from __future__ import division
import matplotlib
matplotlib.use("AGG")
import matplotlib.pyplot as plt
import math
import csv
from operator import itemgetter


import xml.etree.ElementTree as ET
import os, sys, re, string
BASE=os.path.join(os.path.dirname(__file__),'..')
sys.path.append(BASE)
from utils import utils, Confluence
from database.rel_profile import schema0
import pdb

class db_report(object):
    def __init__(self, params):
        self._db = schema0(params)

        self._dut_table_name=params['dut_backend']
        self._ref_table_name=params['ref_backend']
        self._dut_cl=params['dut_cl']
        self._ref_cl=params['ref_cl']        
    
    def gen_history_graphs(self):
        
        self._make_graph_report(self)
        print "Pass to make gragh"
        print self._disable_upload
        if (self._disable_upload is False) and (self._disable_paint is False) :
            self._add_graph_to_confluence()

    def _add_graph_to_confluence(self):
        try:
            self._c_session.set_page(self._confluence_page)
            self._c_session.attach(self._pic_filename)
            print "Pass to attach"
            #self._c_session.update_page(['!%s!' % self._pic_filename], 
            #                            overwrite=True)
        except Exception as e:
            raise db_report.ReportError, 'could not attach graph to Confluence:\n\tpage: %s\n\tfile: %s\n' % \
                (self._c_page, self._pic_filename)

        
    def _make_graph_report(self,
                          params):


        prj_data = []
        get_dr = lambda c: c[c.rfind('_') + 1:]
        #self._get_bin_history()
        #clss = []
        #vlss = []

        clss = [[1, 2, 3, 4], [1, 2, 4], [2, 3]]
        vss = [[100, 101, 99, 102], [130, 135, 132], [143, 145]]
        case_labels = [l for l in self._db_select.split(',') if l in self.label_list]
        clss = [[] for i in range(len(case_labels))]
        vlss = [[] for i in range(len(case_labels))]
        self._get_bin_history(clss, vlss, case_labels)
        prj_data = [(clss, vlss)]
        #case_labels = ['test case 1', 'test case 2', 'test case 3', 'test case 4']
        title = 'test graph generation'
        n_disp = 4
        fn = 'test_graph_generation.png'

        #write_graph_report_to_file(prj_data, case_labels, title, fn, n_disp)
        self._write_graph_report_to_file(prj_data,
                                         case_labels,
                                         self._output_path,
                                         self._pic_title,
                                         self._pic_filename)
        
   
    def _write_graph_report_to_file(self,
                                    prj_data,
                                    case_labels,
                                    output_path,
                                    title,
                                    filename):        
        
        def shift_color(color):
            scl = 7
            r = int(color[1:3],16)
            g = int(color[3:5],16)
            b = int(color[5:7],16)
            if self._cyc == 0:
                shft = lambda c: (c*scl)%0xFF
                r = shft(r)
                g = shft(g)
                b = shft(b)
            self._cyc = (self._cyc + 1) % 3
            i2h = lambda i: (len(hex(i)[2:]) == 1) and '0%s' % hex(i)[2:] or hex(i)[2:]
            return '#%s%s%s' % (i2h(g), i2h(b), i2h(r))

        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        os.chdir(output_path)

        ax_color = '#102018'
        seed = '#80C000'
        markers = ['d', 'o', '8', 'x']
        fig = plt.figure(figsize=(16.0, 5.0))
        ax1 = fig.add_subplot(111)
        ax1.set_adjustable('box-forced')
        plt.subplots_adjust(bottom=0.15)
        
        #get superset of all changelists and values
        all_cls = set()
        flat_vs = []
        
        for (clss, vss) in prj_data:
            for cls in clss:
                all_cls.update(cls)
            #concatenation of each changelist's associated set of values
            flat_vs += [v for vs in vss for v in vs]
        all_cls = sorted(list(all_cls))
        
        if len(flat_vs) == 0:
            print 'WARNING: no data available for graph: {0}'.format(title)
            return

        # set y-axis limits to be +/- 1% of max/min values
        min_y = min(flat_vs) - flat_vs[0]*0.01
        max_y = max(flat_vs) + flat_vs[0]*0.01
        plt.ylim(min_y, max_y)   

        idx=0
        #plot all cases for all projects

        for (clss, vss) in prj_data:
            #plot each case's values, accounting for the
            #possibility that not all cases have the same
            #number of changelist, value pairs
            clr = seed
            self._cyc = 0
            for cls, vs in zip(clss, vss):
                x = []
                
                # self._n_disp == 0 means display all results
                if self._n_disp == 0:
                    n_disp = len(all_cls)
                else:
                    n_disp = self._n_disp

                offset = len(all_cls) - n_disp
                
                if offset < 0:
                    offset = 0
                for cl in cls:
                    if all_cls.index(cl) >= offset:
                        x.append(all_cls.index(cl) - offset)

                ax1.plot(x, vs[-len(x):], color=clr, marker=markers[idx])
                clr = shift_color(clr)                
            idx += 1   
    
        steady_state_value = 0
        invalid_number = 0
        length_number = 0
        if case_labels != []: #There is at least one query value in the sql statement.
            
            if (self._specify_base_line is None) and (set(case_labels) == set(['min_value', 'avg_value'])):
       
                latest_cl = clss[-1][-1]
                latest_cl_value = dict(zip(clss[0],vss[0]))[latest_cl]
                #latest_cl_value = dict(zip(clss[1],vss[1]))[latest_cl]
                
                if self._gen_csv is None:
                    print 'No report files will be generated'
                    
                else: 
                    latest_cl_value_min = dict(zip(clss[0],vss[0]))[latest_cl]
                    latest_cl_value_avg = dict(zip(clss[1],vss[1]))[latest_cl]
                    print 'CSV changelist is %s' %latest_cl
                    
                    first_ele = int(latest_cl_value_min)
                    second_ele = 100 * (latest_cl_value_avg - latest_cl_value_min) / first_ele
                    
                    dest_file = self._table_name + '.csv'
                    csvfile = file(dest_file, 'a')
                    writer = csv.writer(csvfile)
                    
                    if self._gen_csv == 'fft':                
                        work = int(self._legend.split('_')[-1])
                        work_col = (5*work*math.log(work,2))
                        third_ele = first_ele / work_col
                        writer.writerow([self._legend, work_col, "{}   {}%   {}".format(first_ele, round(second_ele, 0), round(third_ele,2)), latest_cl])
                    
                    elif self._gen_csv == 'dct' or self._gen_csv == 'blkvec' or self._gen_csv == 'qmf':
                    
                        writer.writerow([self._legend, "{}   {}%".format(first_ele, round(second_ele, 0)), latest_cl])
                     
                    elif self._gen_csv == 'math':
                    
                        first_ele = int(round(first_ele / 100, 0))
                        writer.writerow([self._legend, "{}   {}%".format(first_ele, round(second_ele, 0)), latest_cl])
                        
                    csvfile.close()


            else:
                latest_cl = self._specify_base_line
                if latest_cl.isdigit() and int(latest_cl) in clss[-1]: 
                    latest_cl_value = dict(zip(clss[0],vss[0]))[int(latest_cl)]
                    #latest_cl_value = dict(zip(clss[1],vss[1]))[int(latest_cl)]
                else:
                    latest_cl_value = 0
                    print "Can not find the corresponding value in database, please check the changelist of specified_base_line %s" % (self._specify_base_line)
            if (self._base_line is None) and (set(case_labels) == set(['min_value', 'avg_value'])):
                #latest_cl = clss[-1][-1]
                #latest_cl_value = dict(zip(clss[1],vss[1]))[latest_cl]   
                if self._avg_line is None:
                    steady_state_cl = clss[-1][-2]
                    steady_state_value = dict(zip(clss[0],vss[0]))[int(steady_state_cl)]
                    #steady_state_value = dict(zip(clss[1],vss[1]))[int(steady_state_cl)]
                    
                else :
                    avg_line_cls = self._avg_line.split("-")
                    for avg_line_cl in clss[-1]:
                        if int(avg_line_cls[1]) >= int(avg_line_cl) >= int(avg_line_cls[0]):
                            steady_state_cl = avg_line_cl
                            steady_state_value += dict(zip(clss[0],vss[0]))[int(steady_state_cl)]
                            #steady_state_value += dict(zip(clss[1],vss[1]))[int(steady_state_cl)]
                            length_number += 1
                            
                    steady_state_value = steady_state_value / length_number
            
            else :
                #latest_cl = clss[-1][-1]
                #latest_cl_value = dict(zip(clss[1],vss[1]))[latest_cl]

                base_line_cls = self._base_line.split(",")
                for base_line_cl in base_line_cls:
                    if base_line_cl.isdigit() and int(base_line_cl) in clss[-1]:
                        steady_state_cl = base_line_cl
                        steady_state_value += dict(zip(clss[0],vss[0]))[int(steady_state_cl)]
                        #steady_state_value += dict(zip(clss[1],vss[1]))[int(steady_state_cl)]
                    else:
                        invalid_number = invalid_number + 1
                        continue

                steady_state_value = steady_state_value / (len(base_line_cls) - invalid_number)
                
            #elif self._base_line.isdigit():
            #    latest_cl = clss[-1][-1]
            #    steady_state_cl = self._base_line
            #    steady_state_value = dict(zip(clss[1],vss[1]))[int(steady_state_cl)]
            #    latest_cl_value = dict(zip(clss[1],vss[1]))[latest_cl]

                
                
            delta_warning = 100 * (latest_cl_value - steady_state_value) / steady_state_value
            
            if delta_warning > int(self._thresh_hold) or delta_warning < - int(self._thresh_hold):
                print "Table %s, Test %s :::: is Out of range: %d%% more or less than %s%% percent overshoot, need pay attention!!!" % (self._table_name, self._legend, delta_warning, self._thresh_hold)
                print "Table %s, Test %s :::: Latest changelist %s at value %s to compare with the reference %s at value %s" % (self._table_name, self._legend, latest_cl, latest_cl_value, steady_state_cl, steady_state_value)
                if delta_warning > 0:
                    self.warning_notification = 1
                else:
                    self.warning_notification = 0
            else :
                print "------- delta is %d%% in the range of tolerance." % delta_warning
                
            if self._disable_paint is True: 
                return
                
        #add axis labels
        ax1.set_xlabel(self._pic_x_label, color=ax_color)
        plt.xticks(range(0, n_disp), all_cls[-n_disp:], rotation=90)
        for t in ax1.get_xticklabels():
            t.set_color(ax_color)

        ax1.set_ylabel(self._pic_y_label, color=ax_color)
        for t in ax1.get_yticklabels():
            t.set_color(ax_color)
         
        #create legend
        leg = ax1.legend(case_labels, 
                         loc='upper left',
                         bbox_to_anchor=(1.1, 1),
                         fancybox=True,
                         shadow=True)
        leg.get_frame().set_facecolor('0.80')
        for t in leg.get_texts():
            t.set_fontsize('small')
             
        #create % delta twin y-axis
        ax2 = ax1.twinx()
        ax2.set_adjustable('box-forced')
        ax2.set_ylabel('% delta', color=ax_color)
        for t2 in ax2.get_yticklabels():
            t2.set_color(ax_color)

        #% delta of each value from first value in first set of first project
        pdelta = [100*(v-flat_vs[0])/float(flat_vs[0]) for v in flat_vs]   
        #set limits of twin y-axis
        min_y = min(pdelta) - 1
        max_y = max(pdelta) + 1
        plt.ylim(min_y, max_y)

        #add title and save
        if len(self._db_select.split(',')) == 5:
            title=self._legend
            filename=self._legend+'.png'
        plt.title(title)
        plt.savefig(filename, bbox_inches='tight',dpi=100)
        #clear state
        plt.clf()        
        if self.trigger_bs is True:
            self._trigger_binary_search_cmd(delta_warning, latest_cl, steady_state_cl)

    def _trigger_binary_search_cmd(self, delta_warning, latest_cl, steady_state_cl):

        if self.warning_notification is 1:
            context="%s;%s,%s;%s;%s;%s;%s" %(delta_warning, latest_cl, \
            steady_state_cl, self._table_name, self._legend,self._cfg_file, self._thresh_hold)
            os.environ['context'] = str(context)
            os.environ['case'] = str(self._legend)
            os.system('echo $context > $case.txt')
    def _get_bin_history(self, clss, vlss, case_labels):
        
        self._legend = self._legend.strip("'")
        self._legend = self._legend.strip('"')

        profileRecordID_q = ' '.join(['select %s from %s where' % (self._db_select, self._table_name),
                                      'changelist >= %d and' % self._di_fft_cl,
                                      'test_case_name like "%s"' % self._legend,
                                      ]
                                     )
        ID_CL_pairs = self._db.query(profileRecordID_q)
        
        unique_test = []
        unique_test_t = []
        unique_test_t_temp = []

        for test_case_dict in ID_CL_pairs:
            test_case_list = test_case_dict.values()
            unique_test.append(test_case_list[0])
            unique_test_t_temp.append(test_case_dict)
            #unique_test.append(test_case_list)
            #print sorted(unique_test)
        
        #acquire the latest updatetime if there are two or more same changelist
        change_lists = list(set(i['changelist'] for i in unique_test_t_temp)) #Get all the non-repeated changelists from the query result.
        for cl in change_lists:
            unique_test_t_same = [i for i in unique_test_t_temp if i['changelist'] == cl] #Get all the query results which have the same changelist.
            unique_test_t_same.sort(key=itemgetter('UNIX_TIMESTAMP(updatetime)')) #Sort these query results by updatetime in ascending order.
            unique_test_t.append(unique_test_t_same[-1]) #Record the latest one.
        
        unique_test_list = sorted(set(unique_test),key=unique_test.index) #Get the sorted test case names.
        unique_test_t = sorted(unique_test_t, key=lambda i : int(i['changelist'])) #Get the database records sorted by changelist.
        for u_test in unique_test_list:
            for u_test_t in unique_test_t:
                if u_test_t['test_case_name'] == u_test:
                    for index, label in enumerate(case_labels):
                        clss[index].append(int(u_test_t['changelist']))
                        vlss[index].append(u_test_t[label])

    def get_value(self, changelist, table_name, profile_value):
    
        import json
        #profile_value = 'min_value'
        compare_dict = {}
        
        #Get test case name dict
        test_case_tuple = self._db.query(r'select distinct test_case_name from %s' % (table_name))
        test_case_list = [i['test_case_name'] for i in test_case_tuple]
        remove_list = []
 
        compare_dict[changelist] = {}
        for test_case in test_case_list:
            #Get the latest database record for one test case.        
            queryStr = \
            r"select test_case_name,%s from %s where test_case_name='%s' and updatetime=(select MAX(updatetime) from %s where test_case_name='%s' and changelist='%s')" %\
            (profile_value, table_name, test_case, table_name, test_case, changelist)
            record_tuple = self._db.query(queryStr)
            if record_tuple == ():
                remove_list.append(test_case)
            else:
                record_dict = record_tuple[0]
                compare_dict[changelist][record_dict['test_case_name']] = float(record_dict[profile_value])
                
        return compare_dict[changelist]
    

    
    def compare_profiling_value(self, dict0, dict1):

        valid_test_case = list(set(dict0.keys()).intersection(set(dict1.keys())))
        total_test_case = len(valid_test_case)
        print total_test_case, valid_test_case
        # intersection of 2 changelist for test cases record in db
        m_50 = 0
        m_20 = 0
        m_5 = 0
        m_0 = 0
        m_f5 = 0
        m_f20 = 0
        m_f50 = 0
        m_20_key = 'Test case:'
        m_f20_key = 'Test case:'
        
        for key in valid_test_case:
            delta = (dict0[key] - dict1[key]) / dict1[key]
            print delta
            if delta > 0 and delta > 0.5:
                m_50 += 1
                print key
                continue
            if delta > 0 and delta > 0.2:
                m_20 += 1
                print key
                m_20_key = m_20_key + key + ' '
                continue 
            if delta > 0 and delta >= 0.05:
                m_5 += 1
                print key
                continue 
            if delta < 0.05 and delta > -0.05:
                m_0 += 1
                continue
            if delta < -0.05:
                m_f5 += 1
                continue
            if delta <0 and delta < -0.2:
                m_f20 += 1
                m_f20_key = key
                continue
        print {'better_than_20%': m_f20, 'better_than_5%': m_f5, 'same in 5%': m_0, 'worse_than_5%': m_5 , 'worse_than_20%':  m_20, 'worse_than_50%': m_50}
        #return {'better_than_20%': str(m_f20) + ' ' + m_f20_key, 'better_than_5%': m_f5, 'same in 5%': m_0, 'worse_than_5%': m_5 , 'worse_than_20%':  str(m_20) + ' ' + m_20_key, 'worse_than_50%': m_50}
        return {'better_than_20%': m_f20, 'better_than_5%': m_f5, 'same in 5%': m_0, 'worse_than_5%': m_5 , 'worse_than_20%':  m_20, 'worse_than_50%': m_50}
        
    def generate_statistic(self):
        
        '''
            For two different changelist values, get the specified profiling value from the given table and database. Compare
            the values of every same test case between these two changelists, then save the statistic to a file in json format.
            The file name is identical with the table name.
        '''
        #pdb.set_trace()
        dut_dict = self.get_value(self._dut_cl, self._dut_table_name, 'min_value')
        ref_dict = self.get_value(self._ref_cl, self._ref_table_name, 'min_value')
        
        profiling_percetage = self.compare_profiling_value(dut_dict, ref_dict)
        
        print profiling_percetage
        
        dut_dict_avg = self.get_value(self._dut_cl, self._dut_table_name, 'avg_value')
        
        
        for k,v in dut_dict_avg.items():
            if k in dut_dict.keys():
                dut_dict[k] = [dut_dict[k], dut_dict_avg[k]]
                #if dut_dict[k] > dut_dict_avg[k]:
                    #print k
                    #print dut_dict[k]
                
        for new_k, new_v in dut_dict.items():
        
            first_ele = new_v[0]
             
            second_ele = 100 * (new_v[1] - new_v[0]) / first_ele
            
            dest_file = 'report/' + self._dut_table_name + '.csv'
            csvfile = file(dest_file, 'a')
            writer = csv.writer(csvfile)
            
            if 'fft' in self._dut_table_name:                
                work = int(new_k.split('_')[-1])
                work_col = (5*work*math.log(work,2))
                third_ele = first_ele / work_col
                #writer.writerow([new_k, work_col, "{}   {}%   {}".format(first_ele, round(second_ele, 0), round(third_ele,2)), self._dut_cl])
                writer.writerow([new_k, "{}   {}%   {}".format(first_ele, round(second_ele, 0), round(third_ele,2)), self._dut_cl])
            
            elif  [ x for x in ['dct', 'blkvec','qmf']  if x in self._dut_table_name ]:
            
                writer.writerow([new_k, "{}   {}%".format(first_ele, round(second_ele, 0)), self._dut_cl])
             
            elif 'math' in self._dut_table_name:
            
                first_ele = int(round(first_ele / 100, 0))
                writer.writerow([new_k, "{}   {}%".format(first_ele, round(second_ele, 0)), self._dut_cl])
            print "File closed ", csvfile
            csvfile.close()        
        
        
        return profiling_percetage
        '''
        better_test_name = []
        worse_test_name = []
        
        for test_case in test_case_list:
            if compare_dict[self._base_line][test_case] - compare_dict[self._specify_base_line][test_case] > \
            compare_dict[self._base_line][test_case] * int(self._thresh_hold) / 100:
                better_case += 1
                total_case -= 1
                better_test_name.append(test_case)
                
            elif compare_dict[self._specify_base_line][test_case] - compare_dict[self._base_line][test_case] > \
            compare_dict[self._base_line][test_case] * int(self._thresh_hold) / 100:
                worse_case += 1
                total_case -= 1
                worse_test_name.append(test_case)
        
        file_content = [["better",better_case],["worse",worse_case],["no changes",total_case]]
        
        
        log = open(self._table_name + '.json', 'w')
        log.writelines(json.dumps(file_content))
        log.close()
        
        log_better_test_name = open(self._table_name + '_better.log', 'w')
        for i in better_test_name:
            log_better_test_name.write(i)
            log_better_test_name.write("\n")
        log_better_test_name.close()
        
        log_worse_test_name = open(self._table_name + '_worse.log', 'w')
        for i in worse_test_name:
            log_worse_test_name.write(i)
            log_worse_test_name.write("\n")
        log_worse_test_name.close()        
        
        
        output_json_file = "data2"
        output_json_filep = file("data2.json")
        s = json.load(output_json_filep)
        
        better = s[0][1]
        better_case += better
        
        worse = s[1][1]
        worse_case += worse
        
        no_change = s[2][1]
        total_case += no_change
        
        file_content = [["better",better_case],["worse",worse_case],["no changes",total_case]]
        log2 = open(output_json_file + '.json', 'w')
        log2.writelines(json.dumps(file_content))
        log2.close()
        '''
        