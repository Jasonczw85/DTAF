"""This module contains the definitions of Class Run_Compatibility_Test 

    Initializes corresponding data container    
    initialize_itaf_param(data_container)
        Parameter: <test_run_spec, test_case_spec, processing_stage_spec, input_output_file_spec>

"""

__copyright__ = """
This program is protected under international and U.S. copyright laws as
an unpublished work. This program is confidential and proprietary to the
copyright owners. Reproduction or disclosure, in whole or in part, or the
production of derivative works therefrom without the express permission of
the copyright owners is prohibited.

               Copyright (C) 2015 by Dolby Laboratories,
               Copyright (C) 2011-2015 by Dolby International AB.
                           All rights reserved.
"""

from ConfigParser import SafeConfigParser

import error
import os
import pdb
import platform as pf
import logging
import zipfile
import zlib
import shutil
import shlex
import time
import re
import sys
import random

sys.path.append("..")

from lib.Binary_Search_on_P4 import Bisec_Binary_Search_On_P4
from lib.test_send_mail import send_mail
from dap_test_analysis import dap_test_analysis
from lib.profiler_log_db_opr import Profiler
from lib.p4_opr import P4_Ops 
from base_test import Run_Test
from dmakelib.lib.builder.builder_plus import getBuilder
from lib.sysinfos import sysinfos_dict
from sqlops.buildtestEngine_plus import *
from lib.compat_parser import *
from lib.itaf_log_parser import parse_itaf_log
from sqlops.mysqlEngine import *


class Run_Compatibility_Test(Bisec_Binary_Search_On_P4, Run_Test):
    """This class contains the interface of running compatibility testing.
    Returns zero if no tests failed, otherwise 2.
    """
    
    def __init__(self, **kwargs):
        """Initializing all Run_Compatibility_Test data structures"""

        self.kwargs = kwargs
        Run_Test.__init__(self, **self.kwargs)

        # basic params    
        self._exceptional_kits = ['DV258', 'ds1ap', 'NGC', 'OAR_v2.0.0']
        self._runtime_exception = ['OARv2']
        self._out_of_box_list = 'DI_Out_of_Box_Success.log'
        self._build_test_arguments['func_name'] = self.build_code
        self._cmp_work = os.path.join(self._exec_dir, '..', '..', 'work')
        self._ref_changelist = kwargs['change_list']
        self._db_has_record = False
        self._abbre_runtime_config_section = kwargs['abbre_config_file_section']
        self._ret = 0

        # Initialize database infos
        self._db_name = kwargs['db_name']
        global db_eng_signal
        db_eng_signal = mysql_eng_signal.replace('db_name', self._db_name)
        self._db_infos = {x : dict() for x in self._build_test_arguments['executable']}
        ####

        # Constructing build infos
        self._build_infos = {x : dict() for x in self._build_test_arguments['executable']}
        for key in self._build_infos:

            self._build_infos[key]['config_section'] = self._abbre_runtime_config_section

            if pf.system() == 'Windows':
                self._build_infos[key]['build_target'] = key
            else:
                self._build_infos[key]['build_target'] = self._build_area.split('/')[-1] + '_' \
                + key
            
            self._build_infos[key]['sub_config'] = key.split('|')[0]

            self._build_infos[key]['backup_folder'] = os.path.join('Logs', \
                self._build_infos[key]['config_section'], self._build_infos[key]['sub_config'])

            self._build_infos[key]['itaf_log_name'] = os.path.join(self._exec_dir, \
                'itaf' + '_' + self._build_infos[key]['sub_config'] + '.log')

            if len(self._build_platform.split(';')) == 1:
                self._build_infos[key]['build_platform'] = self._build_platform
            else:
                index = self._build_test_arguments['executable'].index(key)
                self._build_infos[key]['build_platform'] = self._build_platform.split(';')[index]
            
            self._build_infos[key]['build_area'] = os.path.join(self._build_area, \
                self._build_infos[key]['build_platform'])

            self._build_infos[key]['build_log_name'] = os.path.join(self._build_infos[key]['build_area'],'build' + '_' + self._build_infos[key]['sub_config'] +'.log')
        ####
       
        if self._board_username and self._board_ip:
            os.putenv("board_username", self._board_username)
            os.putenv("board_ip", self._board_ip)
        
        if not self._binary_search == None:
            start_cl = int(self._binary_search.split(",")[0])
            end_cl = int(self._binary_search.split(",")[1])
            
            client_root = self._full_di_path
            
            self._di_p4_repo = "//depot/ger/dlb_intrinsics/main/..."
            args_di=dict()

            for x in self._exceptional_kits:
                if x in self._runtime_config_section :
                    self._di_p4_repo = "//depot/ger/dlb_intrinsics/main/dlb_intrinsics/..."

            
            args_di={ \
            'port': "Perforce-bjo.dolby.net:1666", \
            'user': "testlc", \
            'password': "taC%g17#", \
            'client_root': client_root, \
            'depot': self._di_p4_repo
            }
            
            Run_Test.init_p4_instance(self,args_di)
            #self._p4_test = P4_Ops(**args_di)    
            args_binary_search = {'start_cl': start_cl, 'end_cl': end_cl, \
            'p4_instance': self._p4_test}  
            
            self.logger.info("self._exec_cmd_post: %s" %self._exec_cmd_post) 
            self.logger.info("start_cl: %s, end_cl: %s" %(start_cl,end_cl)) 
            
            Bisec_Binary_Search_On_P4.__init__(self,args_binary_search)

    # @redirect_stdouts_warpper(out_file="console_redirects.txt")
    def run_core_test(self):

        if self._changelist:
            print ("Run TEST at Dut Changelist %s".center(78, '#')) %self._changelist
        else:
            print ("Not Specify Dut Changelist, Use Default Value".center(78, '#'))

        if self._kit_src_folder is not None:
            self._zip_repos = self._kit_src_folder
        os.putenv("zip_repos",self._zip_repos)
        
        if self._extract == 'zip':
            self.extract_src()
        elif self._extract == 'dir':
            zip_file_name = time.strftime("%Y_%m_%d_%H_%M_%S") + "_" + self._zip_packages
            zip_file_name = os.path.normpath(os.path.join(self._zip_repos, zip_file_name))
            zip_dir(self._zip_repos, zip_file_name)
            self.extract_src(zip_file_name)
            print "Remove zip source %s ..." % zip_file_name
            os.remove(zip_file_name)
        else:
            raise error.UserError("Not support to build from other archive!")

        for x in self._exceptional_kits:
            if x in self._runtime_config_section :
                self._replace_src_folder = \
                os.path.join(self._replace_src_folder, 'dlb_intrinsics')

        if not self._binary_search == None:
            self.binary_search_test()
        else:
            self.regression_test()

        return self._ret
    
    def binary_search_test(self):

        current_path = os.getcwd()
        self.logger.info("Sync to latest, current at: %s" %str(Run_Test.get_di_src_from_p4(self)))
        self.logger.info("Current path is: %s" % current_path)
        print "Current path is:", current_path        
        #exec_cmd = exec_cmd_post
        #os.chdir(self._full_di_path)
        #self.logger.info("Change working dir to: %s" %(self._full_di_path))        
 
        Bisec_Binary_Search_On_P4.sync_p4_src(self)
        self.logger.info("2, DI src sync p4: to %s" %(self._mid_cl))
        
        Changelist_bring_failure = \
        Bisec_Binary_Search_On_P4.run_binary_search(self)
        
        if self._email_notify is True:
            user_notification = \
            self._p4_test.get_author_of_p4_changelist(Changelist_bring_failure)
        
            mailto_list=user_notification        
            mail_msg= 'EMAIL Notification of the changelist %s, which made test %s failed' \
            % (Changelist_bring_failure, self._runtime_config_section)

            if send_mail(mailto_list[0],mail_msg,'','',''):
                print "Succeed to notify the changelist author:", mailto_list[0]

            else:
                print "Failed to notify the changelist author"
        else:
            print "Disable Email Notification \n"
            print "The changelist that brings failure is:", Changelist_bring_failure
        
        Run_Test.delete_client(self)

    def build_kit_to_pass(self):
    
        if self._is_modify_cmd == True:
            Run_Test.modify_code(self)
        print "Calculate the length from middle %i to end %i, " %(self._mid_cl, self._end_cl)

        for new_cl in Run_Test.find_earlier_cl(self, len(self._p4_test.get_p4_numbers_from_start_to_end(self._mid_cl, self._end_cl))):
            Run_Test.sync_p4_to_cl(self, new_cl)
            if self._is_modify_cmd == True:
                Run_Test.modify_code(self)
            if self.build_code():
                if new_cl == self._end_cl:
                    print "Not Found the changelist to pass the build"
                print "Build failed at ", new_cl
                build_kit_pass = 1
                continue
            else:
                print "Pass to build at changelist:", new_cl
                build_kit_pass = 0
                break
        self.logger.info("build_kit_to_pass, ret with %s at %d" %(build_kit_pass, int(new_cl)))
        return (int(new_cl), build_kit_pass)

    def run_kit_testing(self):

        self.exchange_dut()
        #test_folder_list = test_folder.split('/')
        self._exec_cmd=self._exec_cmd_post
        self.logger.info("run_kit_testing, start to run %s" %(self._exec_cmd))
        return Run_Test.exec_test(self)

    def regression_test(self):

        print("config_file_section = {0}".format(self._runtime_config_section))
        self.exchange_src()

        if self._is_modify_cmd == True: 
            Run_Test.modify_code(self)

        EventEngine = BuildTestEngine_plus(**self._build_test_arguments)
        EventEngine.register(self._build_test_arguments['type'], self.runtime_exec_test_wrapper)

        EventEngine.start()
        EventEngine.stop()
        
    def extract_src(self, zipfilename=''):

        zip_package = []

        if zipfilename:
            zip_package = [zipfilename]
        else:
            zip_package = [os.path.join(self._zip_repos, d.strip()) for d in self._zip_packages.split(";") if d != ""] 
       
        for zip_pac in zip_package:
            if os.path.exists(zip_pac):
                zipfiles=zipfile.ZipFile(zip_pac, 'r')   
                zipfiles.extractall(self._test_proj_folder)  
                zipfiles.close()   
                print("Unzip finished!")   
            else:
                raise error.UserError("Source Zip Package '%s' does not exist" % zip_pac) 
        self.logger.info("1, extract_src:%s" %(zip_package))
        
    def exchange_src(self):

        if self._di_folder == '':
            print "Null DI Folder and skip replacing di source code ..."
            self.logger.info("2, skip exchanging src.")
            return
        else:
            if os.path.exists(self._full_di_path):
                shutil.rmtree(self._full_di_path)
            shutil.copytree(self._replace_src_folder, self._full_di_path, True)
            self.logger.info("2, exchange_src: from %s to %s" \
            %(self._replace_src_folder, self._full_di_path))
                
    def modify_code(self):
        
        os.system(self._modify_cmd)
        self.logger.info("3, modify_code: %s" %self._modify_cmd)

    def build_code(self, executable):

        # Check whether dut changelist has record in db
        if self.kwargs['insert_db']:
            self._db_infos[executable]['project_name'], \
            self._db_infos[executable]['project_version'], \
            self._db_infos[executable]['project_release'] = \
            get_project_info(self._runtime_config_section)

            self._db_infos[executable]['latest_cl_db'] = \
            get_latest_cl_db(self._db_infos[executable]['project_name'], \
                self._db_infos[executable]['project_version'], \
                self._db_infos[executable]['project_release'])

            if self._db_infos[executable]['latest_cl_db']:
                if self._db_infos[executable]['latest_cl_db'] == self._changelist:
                    self._db_has_record = True
                    print ("RECORD FOR %s AT CHANGELIST %s EXISTED IN DATABASE".center(78, '#')) \
                    %(self._build_infos[executable]['config_section'], self._changelist)
                    print ("SKIP BUILD PROCESS".center(40, '#'))
            else:
                print ("NO RECORDS FOUND FOR %s in DATABASE".center(78, '#')) \
                %self._build_infos[executable]['config_section']
        
        if not self._db_has_record:
            build_full_path = os.path.join(self._test_proj_folder, \
                self._build_infos[executable]['build_area'])

            if pf.system() == 'Windows':
                platform = self._build_infos[executable]['build_platform'] + self._version + '_' \
                + self._build_tool
            else:
                platform = self._build_infos[executable]['build_platform'] + '_' + self._build_tool
            
            run_build = getBuilder(build_full_path, platform)

            print ("Build %s under %s".center(40, '#')) \
            % (self._build_infos[executable]['build_target'], build_full_path)
            build_success, stdout, stderr = \
            run_build.build(self._build_infos[executable]['build_target'], False, True, \
                parallel=0, background=True)
            self._build_infos[executable]['build_result'] = int(not build_success)
            
            old_build_log = os.path.join(self._build_infos[executable]['build_area'], \
                'build.log')
            build_log = open(old_build_log, 'w')
            build_log.write(stdout)
            build_log.write(stderr)
            build_log.close()

            if self._build_infos[executable]['build_result']:
                print "[Build Failed on %s!]" % self._build_infos[executable]['sub_config']
            else:
                print "[Build Passed on %s!]" % self._build_infos[executable]['sub_config']

            self._ret = self._ret or self._build_infos[executable]['build_result']
            
            print ("Complete Build %s".center(30, '#')) \
            % self._build_infos[executable]['build_target']

            self.build_logs_backup(executable)

            # Out-of-Box Check Branch - Build only without workaround applied
            if self._build_only == True:
                if self._is_modify_cmd == False:
                    print ("Build Only and Skip Run Time Test".center(78,'#'))
                    print "Do Out of Box Check ..."
                    self._ret = self.out_of_box_check(executable)

            return self._build_infos[executable]['build_result']
                   
    def exchange_dut(self, executable):

        if self._dut_exec == '':
            print "Null substituted dut and skip replacing dut"
            self.logger.info("6, skip exchanging dut")
            return
        else:    
            if pf.system() == "Windows":
                os.putenv('executable_folder', executable.split('|')[0])
                build_exec = os.path.join(executable.split('|')[0], self._cmd_path)
            else:
                build_exec = self._build_infos[executable]['build_target']

            built_exec = os.path.join(self._build_infos[executable]['build_area'], build_exec)
            shutil.copy(built_exec, self._dut_exec)

            cmd_writable = "chmod u+w " + self._dut_exec
            os.system(cmd_writable)    
            
        self.logger.info("6, exchange_dut:from %s to %s" %(built_exec, self._dut_exec))

    def exec_test(self):

        ret = os.system(self._exec_cmd)
        self.logger.info("7, execute test: %s" %(self._exec_cmd)) 
        return ret

    def modify_exec_cmd(self, executable, seperator, sign):

        exec_cmd_list = []

        for single_cmd in self._exec_cmd.split(seperator):
            if re.match(r'^\s*python', single_cmd):
                single_cmd = single_cmd + sign + self._build_infos[executable]['itaf_log_name']
            exec_cmd_list.append(single_cmd)

        return seperator.join(exec_cmd_list)

    def runtime_exec_test(self, executable):

        if self._db_has_record:
            print ("SKIP RUN TIME TEST PROCESS".center(78, '#'))
        else:
            os.putenv('each_build_area', self._build_infos[executable]['build_area'])
            os.putenv('each_executable', self._build_infos[executable]['build_target'])

            # Handle auto binary searching in some Technology
            if any(x in self._build_infos[executable]['config_section'] for \
                x in self._runtime_exception):
                if pf.system() == 'Windows':
                    search_line_pattern = \
                    re.compile('(\<PreprocessorDefinitions\>DLB_BACKEND\_)(\S{10,20})=1\;(\S+)', re.IGNORECASE)
                    filename = get_project_file(self._build_infos[executable]['build_area'], \
                        self._version)
                    target = executable.split('|')[0]
                else:
                    search_line_pattern = \
                    re.compile('(^DEFINES.*\-DDLB_BACKEND\_)(\S+)\=1\s(\S+)', re.IGNORECASE)
                    filename = os.path.join(self._build_infos[executable]['build_area'], \
                        'Makefile')
                    target = executable

                backend, flavor = get_backend_flavor(search_line_pattern, filename, target)
                os.putenv('each_backend', backend)
                os.putenv('each_flavor', flavor)

            # Build only with workaround applied
            if self._build_only == True:
                if self._is_modify_cmd:
                    print ("SKIP RUN TIME TEST PROCESS".center(78, '#'))
            else:
                print (time.strftime("started_time-%Y_%m_%d_%H_%M_%S"))
                start_time = int(time.time())

                print "Replacing DUT ..."
                self.exchange_dut(executable)
                exec_cmd = self.modify_exec_cmd(executable, \
                    sysinfos_dict[pf.system()]['seperator'], \
                    sysinfos_dict[pf.system()]['out_sign'])
                self._build_infos[executable]['test_result'] = Run_Test.exec_test(self, exec_cmd)

                if pf.system() == 'Windows':
                    with open(self._build_infos[executable]['itaf_log_name'], 'r') as f:
                        for line in f:
                            print line.strip()

                end_time = int(time.time())
                running_time = end_time - start_time
                print "Time duration is ", running_time
                print (time.strftime("finished_time-%Y_%m_%d_%H_%M_%S"))

                self.compare_result(executable)

    def runtime_exec_test_wrapper(self, event):

        print ("Run ITAF Test on %s".center(48, '#')) % self._build_infos[event._executable]['build_target'] 
        self.runtime_exec_test(event._executable)
        print ("Complete ITAF Test on %s".center(48, '#')) % self._build_infos[event._executable]['build_target']

    def compare_result(self, executable):

        self.compare_for_dap(executable)
        self.kit_logs_backup(executable)

        print "Parsing ITAF Log ...\n"
        self._db_infos[executable]['itaf_result'] = \
        parse_itaf_log(self._build_infos[executable]['itaf_log_name'])

        self._build_infos[executable]['test_result'], \
        self._build_infos[executable]['failed_cases'], \
        self._build_infos[executable]['unresolved_cases'] = \
        check_itaf_result(self._db_infos[executable]['itaf_result'].detail_results)

        if self._build_infos[executable]['failed_cases']:
            print "Failed ITAF Cases Existed: %s\n" \
            %self._build_infos[executable]['failed_cases']

        if self._build_infos[executable]['unresolved_cases']:
            print "Unresolved ITAF Cases Existed: %s\n" \
            %self._build_infos[executable]['unresolved_cases']

        if not self.kwargs['insert_db']:
            print "Disable Comparing ITAF Results with Database ...\n"
        else:
            self._db_infos[executable]['dut_cl'] = self._changelist
            self._db_infos[executable]['ref_cl'] = self._ref_changelist
            self._db_infos[executable]['updated_by'] = os.environ.get('RELEASE_TAG')
            self._db_infos[executable]['db_eng_signal'] = db_eng_signal

            compatdf_obj = CompatDataFrame(**self._db_infos[executable])

            if self._db_infos[executable]['latest_cl_db']:
                print "Update Latest Tag in Database ...\n"
                latest_tag_db = get_tag_db(self._db_infos[executable]['latest_cl_db'], \
                    self._db_infos[executable]['project_name'], \
                    self._db_infos[executable]['project_version'], \
                    self._db_infos[executable]['project_release'])

                if not latest_tag_db.startswith('v'):
                    print "Skip Since Latest Records in DB Has No Latest Tag!\n"
                else:
                    if latest_tag_db.endswith('release'):
                        print "Skip Since Latest Records in DB Has Release Tag!\n"
                    else:
                        print "Remove Tag at Latest Changelist in DB!\n"
                        compatdf_obj.remove_tag()

                print "Query Database for Ref Results at Changelist %s ...\n" %self._ref_changelist
                compatdf_obj.get_ref_result()

                print "Compare ITAF Between %s and %s to Generate Summary ...\n" \
                %(self._ref_changelist, self._changelist)
                self._build_infos[executable]['test_result'], \
                self._build_infos[executable]['compare_result'] = compatdf_obj.get_summary()

                if self._build_infos[executable]['test_result']:
                    if self._build_infos[executable]['compare_result'].diff_cases:
                        print "There are differences on common itaf cases compared with ref changelist!"
                        print "Diff ITAF cases are: %s\n" \
                        %self._build_infos[executable]['compare_result'].diff_cases
                    else:
                        print "There are no differences on common itaf results compared with ref changelist!"

                    if self._build_infos[executable]['compare_result'].new_cases.failed_cases:
                        print "But some new added ITAF cases failed: %s\n" \
                        %self._build_infos[executable]['compare_result'].new_cases.failed_cases

                    if self._build_infos[executable]['compare_result'].new_cases.unresolved_cases:
                        print "But some new added ITAF cases unresolved: %s\n" \
                        %self._build_infos[executable]['compare_result'].new_cases.unresolved_cases
                else:
                    print "There are no differences compared with ref changelist!\n"
            else:
                print "NO RECORDS FOR COMPARISON AND INSERT DATA INTO DATABASE DIRECTLY ...\n"

            argument = dict()
            argument['dataframe'] = compatdf_obj.get_df()
            argument['type'] = UPDATE_TO_SQL
            argument['strategyExec'] = 'MySql'
            argument['schemaName'] = ''
            ee = MySqlEngine(**argument)
            ee.register(UPDATE_TO_SQL, savetomysqlcompat)
            ee.start()
            time.sleep(1)
            ee.stop()

        if self._build_infos[executable]['test_result']:
            print "[Test Failed on %s!]\n" % self._build_infos[executable]['sub_config']
        else:
            print "[Test Passed on %s!]\n" % self._build_infos[executable]['sub_config']

        self._ret = self._ret or self._build_infos[executable]['test_result']

    def compare_for_dap(self, executable):
        
        if self._dap_analysis is True:
            dap_test_analysis.update_log(self._build_infos[executable]['itaf_log_name'], \
            os.path.join(self._cmp_work, \
            '..', '..', 'Test_Materials', 'Test_Specifications', 'specs'), \
            self._cmp_work)
            
        self.logger.info("8, detect if DAP project with dap_analysis option %s" \
        %self._dap_analysis)
        
    def kit_logs_backup(self, executable):
        
        if os.path.exists(self._build_infos[executable]['itaf_log_name']):
            shutil.copy(self._build_infos[executable]['itaf_log_name'], \
                self._build_infos[executable]['backup_folder'])

        core_log = 'core_test.txt'
        if os.path.exists(core_log):
            shutil.copy(core_log, self._build_infos[executable]['backup_folder'])
        
        dap_analysis_log = 'dap_test_analysis_result.txt'
        if os.path.exists(dap_analysis_log):
            shutil.copy(dap_analysis_log, self._build_infos[executable]['backup_folder'])
        
        regex = ['FAILED$', 'UNRESOLVED$']
        failed_list = findString(self._build_infos[executable]['itaf_log_name'], regex)

        if all(x not in self._test_proj_folder for x in ['DV258', 'OAR_v2.0.0']):   
            self.logger.info("work_path %s" % self._cmp_work)

            if failed_list:
                work_folder = os.path.join(self._build_infos[executable]['backup_folder'], 'failed_cases')
                os.makedirs(work_folder)
                self.logger.info("failed_cases_folder %s" % work_folder)

                for failed_case in failed_list:
                    for filename in os.listdir(os.path.join(self._cmp_work, failed_case)):
                        if '.ac3' in filename or '.wav' in filename:
                            os.remove(os.path.join(self._cmp_work, failed_case, filename))

                    failed_case_path = os.path.join(work_folder, failed_case)
                    shutil.move(os.path.join(self._cmp_work, failed_case), failed_case_path)
                   
        self.logger.info("kit_log %s" % self._build_infos[executable]['itaf_log_name'])
        
    def out_of_box_check(self, executable):

        knowledge_base_folder = sysinfos_dict[pf.system()]['KL_Base']

        comp_build_base = os.path.join(knowledge_base_folder, self._out_of_box_list)
        build_success_log = open(comp_build_base, 'r')
       
        find_success = False
        
        for eachLine in build_success_log:
            # work around for name shortcut on windows platform
            if 'msvs' in eachLine:
                eachLine = abbre_folder_name(eachLine)

            if re.search(self._build_infos[executable]['config_section'], eachLine):
                find_success = True
                if self._build_infos[executable]['build_result']:
                    print "[Out of Box Check Failed on %s: Build failed, should be successful]" \
                    %self._build_infos[executable]['sub_config']
                    build_success_log.close()
                    return 1
                    
        if not find_success and not self._build_infos[executable]['build_result']:
            print "[Out of Box Check Failed on %s: Build successful, should be failed]" \
            %self._build_infos[executable]['sub_config']
            build_success_log.close()
            return 1
        
        print "[Out of Box Check Passed on %s]" %self._build_infos[executable]['sub_config']
        build_success_log.close()
        return 0
    
    def build_logs_backup(self, executable):

        old_build_log = os.path.join(self._build_infos[executable]['build_area'], 'build.log')

        os.rename(old_build_log, self._build_infos[executable]['build_log_name'])
        
        backup_folder_build = os.path.join(self._build_infos[executable]['backup_folder'],'build_log')

        if not os.path.exists(backup_folder_build):
            os.makedirs(backup_folder_build)

        self.logger.info("5, build_back_up_folder %s" %backup_folder_build)

        # Backup build log if it existed
        if os.path.exists(self._build_infos[executable]['build_log_name']):
            shutil.copy(self._build_infos[executable]['build_log_name'], backup_folder_build)

        # Backup build binary if it existed
        if os.path.exists(os.path.join(self._build_infos[executable]['build_area'], \
            self._build_infos[executable]['build_target'])):
            shutil.copy(os.path.join(self._build_infos[executable]['build_area'], \
                self._build_infos[executable]['build_target']), backup_folder_build)


def abbre_folder_name(runtime_config_section):

    project_name, project_version, project_release = get_project_info(runtime_config_section)

    update_project_release = ''.join([x[0] for x in project_release.split('_')])

    return '_'.join([project_name, project_version, update_project_release])

def get_project_info(runtime_config_section):

    name_components = runtime_config_section.split('_')
    version_index = 0
    for index,item in enumerate(name_components):
        if item.strip().startswith('v') or item.strip().startswith('V'):
            version_index = index

    project_name = '_'.join(name_components[:version_index])
    project_version = name_components[version_index]
    project_release = '_'.join(name_components[version_index+1:])

    return (project_name, project_version, project_release)

def findString(filePath, regex):

    fileList = []
    fileObj = open(filePath, 'r')
    for eachLine in fileObj:
        for key_word in regex:
            if re.search(key_word, eachLine):
                #print eachLine.split(' ')[1][:-3]
                fileList.append(eachLine.split(' ')[1][:-3])
    return fileList

def zip_dir(dirname, zipfilename):

    filelist = []
    
    fulldirname = os.path.abspath(dirname)
    fullzipfilename = os.path.abspath(zipfilename)

    print "Start to zip %s to %s ..." % (fulldirname, fullzipfilename)

    if not os.path.exists(fulldirname):
        raise error.UserError("Dir/File %s does not exist!" % fulldirname)

    #if os.path.exists(fullzipfilename):
    #    print "%s has already existed. Remove it." % fullzipfilename
    #    os.remove(fullzipfilename)

    if os.path.isfile(dirname):
        filelist.append(dirname)
    else:
        for root, dirs, files in os.walk(dirname):
            for filename in files:
                # Exclude zip files belong to other backend
                if not filename.endswith('.zip'):
                    filelist.append(os.path.normpath(os.path.join(root, filename)))

    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED, allowZip64 = True)
    for eachfile in filelist:
        destfile = eachfile[len(dirname):]
        zf.write(eachfile, destfile)
    zf.close()
    print "Zip folder succeed!"

def savetomysqlcompat(event):

    save_to_mysql_compat(event._df, db_eng_signal)

def get_latest_cl_db(project_name, project_version, project_release):

    column_dict = {
                    'project_name' : project_name,
                    'project_version' : project_version,
                    'project_release' : project_release
                    }

    df = read_mysql_select('CompatTestSummary', db_eng_signal, column_dict, 'intrinsic_version')

    if not df.empty:
        return str(df['intrinsic_version'].values.max())
    else:
        return ""

def get_tag_db(intrinsic_version, project_name, project_version, project_release):

    column_dict = {
                    'intrinsic_version' : intrinsic_version,
                    'project_name' : project_name,
                    'project_version' : project_version,
                    'project_release' : project_release
                    }

    df = read_mysql_select('CompatTestSummary', db_eng_signal, column_dict, 'updated_by')

    return str(df['updated_by'].values[0])

def get_backend_flavor(search_pattern, file, target):

    try:
        with open(file, 'r') as file:
            lines = file.readlines()
    except IOError as err:
        print str(err)

    all_backends = set()
    for line in lines:
        line = line.strip()

        line_mo = search_pattern.search(line)
        if line_mo:
            all_backends.add(line_mo.group(2).lower())

    for bk in all_backends:
        if bk.startswith('arm'):
            bk = bk.replace('arm', 'armv')
            
        if bk in target:
            backend = bk
            flavor = target.replace(bk, '')[1:]

    return (backend, flavor)

def get_project_file(path, msvs_version):

    project_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('vcxproj') and msvs_version in file:
                return os.path.join(root, file)

    return None

def check_itaf_result(itaf_dict):

    failed_cases = [x for x in itaf_dict.keys() if itaf_dict[x]=='failed']

    unresolved_cases = [x for x in itaf_dict.keys() if itaf_dict[x]=='unresolved']

    result = any(failed_cases) or any(unresolved_cases)

    return (int(result), failed_cases, unresolved_cases)









