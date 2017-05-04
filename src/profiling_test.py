"""This module contains the definitions of Class run_compatibility_test 

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
import platform
import logging
import zipfile
import shutil
import shlex
import time
import re
import pandas as pd
from math import floor

from lib.Binary_Search_on_P4 import Bisec_Binary_Search_On_P4
from lib.test_send_mail import send_mail
from dap_test_analysis import dap_test_analysis
from lib.profiler_log_db_opr import Profiler
from lib.p4_opr import P4_Ops 
from database.rel_profile import schema0
from base_test import Run_Test
from lib.parse_log import ParsedProfilingReport
from sqlops.mysqlEngine import *
from lib.profiler_log_stats import parse_environment_report
from sqlops.buildtestEngine import *
from dmakelib.lib.builder.builder_plus import getBuilder
from lib.build_frontend import build_frontend_dict


class Run_Profiling_Test(Bisec_Binary_Search_On_P4, Run_Test):
    """This class contains the interface of running profiling testing.
    Returns zero if no tests failed, otherwise 2.
    """
    
    def __init__(self, **kwargs):
        """Initializing all Run_Profiling_Test data structures"""            
        
        self.kwargs = kwargs
        Run_Test.__init__(self, **self.kwargs)
        
        # profiling test ini specified
        self._is_transform_csv=kwargs["is_transform_csv"]
        self._insert_db=kwargs["insert_db"]
        self._loop_times=kwargs["loop_times"]
        self._changelist_config=kwargs["change_list"]
        self._profiling_logs=kwargs["profiling_logs"]
        self._db_table_name=kwargs["db_table_name"]
        self._skip_with_record=kwargs["skip_with_record"]
        self._worst_behaviour=kwargs["worst_behaviour"]
        self._codec_behaviour=kwargs["codec_behaviour"]
        self._disable_rebuild=kwargs["disable_rebuild"]
        self._build_backend=kwargs['build_backend']
        self._di_cl = kwargs['di_cl']
        self._build_frontend = dict()
        self._build_executable = dict()
        global db_eng_signal
        self._db_name = kwargs['db_name']
        db_eng_signal = mysql_eng_signal.replace('db_name', self._db_name)
        #self._platform = '_'.join([self._build_platform, self._build_tool])
        self._build_info = {
                            'build_platform' : self._build_platform,
                            'build_tool' : self._build_tool,
                            'build_backend' : self._build_backend
                            }

        self._build_base = os.path.join(self._test_proj_folder, self._build_area, self._di_folder)

        if self._worst_behaviour and self._codec_behaviour:
            raise error.UserError("Not support enable worst_behaviour and codec_behaviour simultaneously")

        self._build_test_arguments['func_name'] = self.build_to_pass_wrapper

        if not self._db_table_name:
            algorithms = [i.split('_')[2] for i in self._executable.split(';')]
            self._db_table_name = ';'.join([self._runtime_config_section.replace('bench', i+'_bench') for i in algorithms])

        self._build_test_arguments['db_table_name'] = [i for i in self._db_table_name.split(';')]
        ######
        
        # specify board ip and username
        if self._board_username and self._board_ip:
            os.putenv("board_username", self._board_username)
            os.putenv("board_ip", self._board_ip)
        #####

        # Wrapper parameters specified
        self._db_host=kwargs["db_host"]
        self._db_login=kwargs["db_login"]
        self._db_params = \
        {
            'db_host' : self._db_host,
            'db_login' : self._db_login,
            'db_name' : self._db_name
        }
        
        self._p4_port=kwargs["p4_port"]
        self._p4_login=kwargs["p4_login"]
        self._meas_val=kwargs["meas_val"]
        ######

        args_p4=dict()
        args_p4['port'] = self._p4_port
        
        if len(self._p4_repo.split(':')) > 1:
            args_p4['depot'] = self._p4_repo.split(':')[0]
            args_p4['depot_excluded'] = self._p4_repo.split(':')[1]
        else:
            args_p4['depot'] = self._p4_repo

        if self._p4_login:
            [p4_user, p4_pwd] = self._p4_login.split(';')
            args_p4['user'] = p4_user
            args_p4['password'] = p4_pwd

        if self._extract == 'zip': 
            raise error.UserError("Not support to build zip source of DI!")
        
        elif self._extract == 'P4':

            client_root = os.path.join(self._test_proj_folder, self._build_area) 
            args_p4['client_root'] = client_root
            
            Run_Test.init_p4_instance(self,args_p4)

            print "Initial: P4 instance, [Sync] to latest, current at:", str(Run_Test.get_di_src_from_p4(self))

        elif self._extract == 'P4zip':

            print "Initial: Unzip IDK Source Packages ..."
            self.extract_src()

            client_root = os.path.normpath(os.path.join(self._test_proj_folder, self._build_area, "Dolby_Intrinsics_Imp/Source_Code"))
            args_p4['client_root'] = client_root

            Run_Test.init_p4_instance(self,args_p4)

            print "Initial: P4 instance, [Sync] to latest, current at:", str(Run_Test.get_di_src_from_p4(self))

        elif self._extract == 'copy':
            if not self._copy_path:
                raise error.UserError("Please Specify Path to Test Resources")

            print "Copy Test Resources from %s to %s ..." \
            % (self._copy_path, os.path.join(self._test_proj_folder, self._build_area))

            copyFiles(self._copy_path, os.path.join(self._test_proj_folder, self._build_area))

        if not self._binary_search == None:
        
            start_cl = int(self._binary_search.split(",")[0])
            end_cl = int(self._binary_search.split(",")[1])           
            
            args_binary_search = {'start_cl': start_cl, 'end_cl': end_cl, \
            'p4_instance': self._p4_test}  
            
            self.logger.info("self._exec_cmd_post: %s" %self._exec_cmd_post) 
            self.logger.info("start_cl: %s, end_cl: %s" %(start_cl,end_cl)) 
            
            Bisec_Binary_Search_On_P4.__init__(self,args_binary_search)
                
        
    def run_core_test(self):
        
        os.putenv("executable", self._executable)
        os.putenv("di_folder", self._di_folder)
        framework_path = os.getcwd()
        print "The framework_path is :", framework_path
        os.chdir(os.path.join(self._test_proj_folder, self._build_area))
        current_path = os.getcwd()
        print current_path      
        
        if not self._binary_search == None:
            self.binary_search_test()
        else:
            self.regression_test()
            
        if self._extract.startswith('P4'):
            Run_Test.delete_client(self) 
    
        
        return 0
    
    def binary_search_test(self):

        self.logger.info("exec_cmd: %s" %self._exec_cmd)
        pat_obj=re.compile(r'[^/]*\.cfg')
        test_case_name_list = pat_obj.findall(self._exec_cmd_post)
        self._test_case_name =test_case_name_list[0].split('.')[0]
        
        skip_to_run = 0
        
        # Sync to the middle point
        Bisec_Binary_Search_On_P4.sync_p4_src(self)
        self.logger.info("2, DI src sync p4: to %s" %(self._mid_cl))
        
        Changelist_bring_failure = \
        Bisec_Binary_Search_On_P4.run_binary_search(self)
          
        if self._email_notify is True:
            user_notification = \
            self._p4_test.get_author_of_p4_changelist(Changelist_bring_failure)
        
            mailto_list=user_notification
        
            self._algorithm = self._runtime_config_section.split('_')[-3]
            
            db_params = \
            {
                'db_host' : '10.204.7.188',
                'db_login' : "root;root",
                'db_name' : 'test1'
            }

            db = schema0(db_params)

            table_column = "( \
            test_case char(128), \
            backend char(40),  \
            board char(40) default null,\
            primary key(test_case, backend, board), \
            author char(40) , \
            algorithm char(40) , \
            comment char(255) default null \
            )"

            table_name='xcl' + str(Changelist_bring_failure)
            #db.create_table(table_name, table_column)
            
            self._board = self._runtime_config_section.split('_')[0]
            self._backend = "_".join([i for i in self._executable.split('_')[4:-2]])

            cl_details = \
            {
                'test_case': self._test_case_name,
                'backend': self._backend,
                'board': self._board,
                'author': user_notification[0],
                'algorithm': self._algorithm,
                'changelist': str(Changelist_bring_failure)
            }
            

            db = schema0(db_params)
            #db.insert_cl_value(table_name, cl_details)

            #table_name_email = "Failed_CL_EmailNotification"
            changelist = str(Changelist_bring_failure)
            author = user_notification[0]
            db = schema0(db_params)
            #db.insert_email_table(changelist, author)

            mail_sub= 'Performance Issue on the %s of changelist %s' \
            % (self._test_case_name, Changelist_bring_failure)
            mail_content = "Hi %s \n \
            The changelist %s, which failed on the test: %s , the reproduce steps: %s failed %s\n" \
            % (user_notification, Changelist_bring_failure, self._test_case_name, self._exec_cmd, self._exec_cmd_post)
            mailto = 'hxzhan'
            if send_mail(mailto, mail_sub, mail_content,'/tmp/ranking_list.txt','/tmp/attach.png'):
                print "Succeed to notify the changelist author:", mailto_list[0]
                print "The test_case_name:", self._test_case_name
            else:
                print "Failed to notify the changelist author"     

        else:
            print "Disable Email Notification \n"
            print "The changelist that brings failure is :", Changelist_bring_failure
			
    # pt specific                        
    def build_kit_to_pass(self):
    
        Run_Test.modify_code(self)
        self.logger.info("modify_cmd: %s" %self._modify_cmd)    
        print "Calculate the length from middle %i to end %i, " %(self._mid_cl, self._end_cl)
        
        # Current cl is at middle point.
        for new_cl in Run_Test.find_earlier_cl(self, len(self._p4_test.get_p4_numbers_from_start_to_end(self._mid_cl, self._end_cl))):
                      
            print "Start to test new_cl", new_cl
            self.logger.info("Start to query the db in build testing")
            connect_db = schema0(self._db_params)
            profileRecordID_q = ' '.join(['select test_case_name from %s where' % (self._db_table_name),
                  'changelist = %d and' % int(new_cl),
                  'test_case_name like \"%s\"' % self._test_case_name,
                  ]
                 )
            has_record = connect_db.query(profileRecordID_q)
            
            self.logger.info("Finished to query the db for %s in build testing" %new_cl)
            self.logger.info("Current skip_with_record: %s" %self._skip_with_record)
            self.logger.info("The test_case_name is %s" %self._test_case_name)
            print "has_record :", has_record
            if self._skip_with_record is True and has_record is not ():

                build_kit_pass = 0
                skip_to_run = 1	
                print "Found the record in database, so skip to build", new_cl
                self.logger.info("Found record of %s in db, skip to build" %new_cl)
                self.logger.info("Return new_cl %s in db, return build result %d" %(new_cl, build_kit_pass))
                
                # If build failed trigger this, before return, make sure this current cl 
                #of p4test instance has been updated. But it really add the sync time.
                Run_Test.sync_p4_to_cl(self, new_cl)
                
                return (int(new_cl), build_kit_pass)
            else:    
                self.logger.info("Not found record of %s in db, start to build" %new_cl)
                Run_Test.sync_p4_to_cl(self, new_cl)
                self.logger.info("p4_test._cur_cl_number %s" %self._p4_test._cur_cl_number) 
                Run_Test.modify_code(self)
                self._build_to_pass_cl = new_cl   
                build_result = self.build_to_pass(new_cl)   
                #build_result = 0
                self.logger.info("%s %s %s %s %s %s %s" %(new_cl, self._p4_test, \
                self._test_proj_folder, self._di_folder, self._build_area, self._executable, self._modify_cmd))
                self.logger.info("build_result %s" %build_result)
                
                if build_result:
                    if new_cl == self._end_cl:
                        print "Not Found the changelist to pass the build"
                    print "Build failed at ", new_cl  
                    self.logger.info("build_result %s" %build_result) 
                    self.logger.info("Failed to build at  %s" %new_cl)                            
                    build_kit_pass = 1
                    continue
                else:    
                    print "Pass to build at changelist:", new_cl
                    self.logger.info("Pass to build at  %s" %new_cl)
                    build_kit_pass = 0
                    break
        return (int(new_cl), build_kit_pass)
           
    def run_kit_testing(self):
    
        self.logger.info("self._exec_cmd: %s" %self._exec_cmd)
        self.logger.info("self._exec_cmd_post: %s" %self._exec_cmd_post)
        print "DEBUG: current dir ", os.getcwd()
        print " Current P4 changelist after build", self._p4_test._cur_cl_number
        
        connect_db = schema0(self._db_params)
        profileRecordID_q = ' '.join(['select test_case_name from %s where' % (self._db_table_name),
              'changelist = %d and' % int(self._p4_test._cur_cl_number),
              'test_case_name like \"%s\"' % self._test_case_name,
              ]
             )
        has_record = connect_db.query(profileRecordID_q)
        
        self.logger.info("Finished to query the db in run testing")
        self.logger.info("Current skip_with_record: %s" %self._skip_with_record)
        
        if self._skip_with_record is True and has_record is not ():
            print "Found record in database"
            self.logger.info("Found record of in db, skip to run")
            
        else:          
            print "Not found the record in database, start to run."
            self.exec_runtime_test(self._p4_test._cur_cl_number)
            print "DEBUG: current dir", os.getcwd()
                     
        tmp_path = os.getcwd()
        exec_cmd_post_cmp = self._exec_cmd_post + ' ' + self._p4_test._cur_cl_number  
        self.logger.info("Current path: %s" %tmp_path)                
        self.logger.info("exec_cmd_post_cmp: %s" %exec_cmd_post_cmp)
        print "================ Binary Search ============ exec_cmd_post_cmp:", exec_cmd_post_cmp
        self.logger.info("p4_test._cur_cl_number: %s" %self._p4_test._cur_cl_number)
        return exec_test(exec_cmd_post_cmp)                    
                            
    def build_to_pass(self, commit_id, executable):

        Run_Test.modify_code(self)
        
        # Unshelve Code change to latest changelist and only valid on latest changelist
        if self._extract == 'P4' or self._extract == 'P4zip':
            if self._shelve_id:
                Run_Test.unshelve_di_from_p4(self, self._shelve_id)
            else:       
                print "Start to [sync] to change list:", commit_id
                Run_Test.sync_p4_to_cl(self, commit_id)
                Run_Test.modify_code(self)
        
        build_ret, self._build_frontend[executable], self._build_executable[executable] = build_di(commit_id, self._di_folder, self._build_base, executable, self._build_info)

        print "Finish build DI with return value", build_ret
        self.logger.info("build_to_pass, return: %s" %build_ret)
        return build_ret

    def build_to_pass_wrapper(self, commit_id, executable):

        if self._test_only:
            self._build_frontend[executable] = os.path.join(self._di_folder, self._build_platform)
            self._build_executable[executable] = executable

            print "==================== Skip Build Process ===================="
            print "==================== Use %s as Executable ====================" \
            % os.path.join(self._build_frontend[executable], self._build_executable[executable])

            build_result = 0
        else:
            build_result = self.build_to_pass(commit_id, executable)

            if build_result:
                print "build failed on current commit_id:", commit_id

                if not self._disable_rebuild:
                    for new_cl in Run_Test.find_earlier_cl(self, 5):
                        if new_cl == commit_id:
                            continue
                        else:
                            print "try to build on former commit_id:", new_cl
                            build_result = self.build_to_pass(new_cl, executable)
                            if build_result:
                                continue
                            else:
                                print "build succeed on commit_id:", commit_id
                                break

                    if build_result:
                        print "No commit_id can pass on build"
                        raise error.UserError("Build Fail!")
                    else:
                        print "start following test!"
            else:
                print "start following test!"

        return build_result

    def exec_runtime_test_wrapper(self, event):

        event._build_frontend = self._build_frontend[event._executable]
        event._build_executable = self._build_executable[event._executable]

        print "==================== Run benchmarking tests on %s under %s ====================" % (event._build_executable, event._build_frontend)

        self.exec_runtime_test(event._changelist, event._build_frontend, event._build_executable, event._db_table_name)

        print "==================== Complete Benchmarking tests on %s under %s ====================" % (event._build_executable, event._build_frontend)
        
    def exec_runtime_test(self, commit_id, build_frontend, build_executable, db_table_name):
        
        self.run_to_pass(build_frontend, build_executable)
        
        if self._is_transform_csv:
            transform_log_2_csv(self._test_proj_folder, \
            self._build_area, build_frontend, commit_id)
            
        get_profile_log(build_frontend, commit_id, build_executable, db_table_name, self._insert_db, self._df_insert)
        self.logger.info("exec_runtime_test, success return") 

    def run_to_pass(self, build_frontend, build_executable):
        
        old_name = os.path.join(build_frontend, 'profile_report.log')

        if self._extract == 'copy':
            _cur_cl = self._changelist
        else:
            _cur_cl = self._p4_test._cur_cl_number
        
        if  build_frontend or build_executable:
            os.putenv('each_di_folder', build_frontend)
            os.putenv('each_executable', build_executable)

        for i in range(self._loop_times):
            os.system(self._exec_cmd)
            new_name = os.path.basename(old_name).split('.')[0] + '_' + _cur_cl + '_' + str(i+1) + '.log'
            new_name = os.path.join(build_frontend, new_name)
            os.rename(old_name, new_name) 

        if self._codec_behaviour:
            self._df_insert = merge_compare(build_frontend, self._loop_times, self._meas_val, _cur_cl, 'codec')
        elif self._worst_behaviour:
            self._df_insert = merge_compare(build_frontend, self._loop_times, self._meas_val, _cur_cl, 'worst')
        else:
            self._df_insert = merge_compare(build_frontend, self._loop_times, self._meas_val, _cur_cl, 'default')

        backup_folder = os.path.join(self._test_proj_folder, self._build_area, build_frontend)

        # Fix here: Log could not be backed up on windows
        # Log should be backed up on EC instead of local machine or even nfs mount. refer to compatibility for example
        if platform.system() != "Windows":
            logs_backup(backup_folder, self._test_proj_folder, self._build_area, self._profiling_logs, _cur_cl, build_executable)

        print "Start writing system info into environment.log ..."

        target_os_cmd = {'Windows' : 'VER | findstr Microsoft > ./${each_di_folder}/target_os.log',
                         'Linux'   : '''cat /etc/issue | awk '{print $1 "-" $2}' > ./${each_di_folder}/target_os.log'''}

        arch_cmd = {'Windows' : 'wmic os get osarchitecture | findstr bit > ./${each_di_folder}/arch.log',
                    'Linux'   : "echo 'arch.log existed'"}

        glibc_cmd = {'Windows' : "echo 'invalid' > ./${each_di_folder}/glibc.log",
                     'Linux'   : "getconf -a | grep GNU_LIBC_VERSION | awk '{print $2$3}' > ./${each_di_folder}/glibc.log"}

        sys = platform.system()

        os.system(target_os_cmd[sys])
        with open(os.path.join(build_frontend, 'target_os.log')) as f1:
            target_os = f1.readlines()[0].strip()

        os.system(arch_cmd[sys])
        with open(os.path.join(build_frontend, 'arch.log')) as f2:
            arch = f2.readlines()[0].strip()

        os.system(glibc_cmd[sys])
        with open(os.path.join(build_frontend, 'glibc.log')) as f3:
            glibc = f3.readlines()[0].strip()

        board = self._runtime_config_section.split('_')[0] if self._runtime_config_section.split('_')[0] not in ['Linux', 'Windows'] else 'invalid'

        #backend = "_".join([i for i in build_executable.split('_')[4:-2]]) if self._dut_exec == 'null' else self._dut_exec
        backend = build_executable

        #target = build_frontend.replace('\\', '//').split('/')[-1] if build_frontend.replace('\\', '//').split('/')[-1] else 'invalid'
        target = self._build_platform

        with open(os.path.join(build_frontend, "environment.log"), 'w') as f1:
            print >> f1, "cmd=./%s\nbackend=%s\nboard=%s\ntarget=%s\nos=%s\narch=%s\nchangelist=%s\ncompiler=armcc-5.0.1\nglibc=%s\n" \
            % (build_executable, backend, board, target, target_os, arch, \
            _cur_cl, glibc)

        if platform.system() != 'Windows':
            environment_log = os.path.join(build_frontend, "environment.log")
            os.environ['environment_log'] = str(environment_log)
            command = "sed -i '/^$/ d' $environment_log"
            os.system(command)
        
    def regression_test(self):

        if self._extract == 'copy':
            self._build_test_arguments['changelist'] = self._changelist
        else:
            latest_change = Run_Test.get_latest_di_cl_from_p4(self)
            print "latest changelist is:", latest_change

            if not self._changelist_config:
                print "Changelist is Null, set it to latest changelist"
                self._build_test_arguments['changelist'] = latest_change
            else:
                change = self._changelist_config
                print "Got the changelist to be tested from ini:", change
                if not change.isdigit():
                    print "Null changelist existed , set it to latest changelist"
                    change = latest_change

                print "Updated changelist is:", change

                self._build_test_arguments['changelist'] = change

        EventEngine = BuildTestEngine(**self._build_test_arguments)
        EventEngine.register(self._build_test_arguments['type'], self.exec_runtime_test_wrapper)

        EventEngine.start()

        EventEngine.stop()

        if platform.system() != "Windows":
            for key,value in self._build_frontend.items():
                backup_folder = os.path.join(self._test_proj_folder, self._build_area, value)
                logs_backup(backup_folder, self._test_proj_folder, self._build_area, self._profiling_logs, 'regression', key)

    def extract_src(self, zipfilename=''):
        zip_packages = []

        if zipfilename:
            zip_packages = [zipfilename]
        else:
            zip_packages = [os.path.join(self._zip_repos, d.strip()) for d in self._zip_packages.split(";") if d != ""]

        for zip_pac in zip_packages:
            if os.path.exists(zip_pac):
                zipfiles = zipfile.ZipFile(zip_pac, 'r')
                zipfiles.extractall(os.path.normpath(os.path.join(self._test_proj_folder, self._build_area)))
                zipfiles.close()
                print "Unzip finished!" 
            else:
                raise error.UserError("Source Zip Package '%s' does not exist" % zip_pac)
    
    def find_earlier_cl(self, numbers):

        return self._p4_test.get_current_p4_numbers(numbers)
        
    def sync_p4_to_cl(self, commit_id):

        print "Start to [sync] P4 to ............. : ", commit_id
        self._p4_test.connect_svr_sync_depot(commit_id)

    def get_di_src_from_p4(self):
        
        success = self._p4_test.connect_svr_sync_depot()
        return success[0]

    def unshelve_di_from_p4(self, shelve_id):

        self._p4_test.connect_svr_unshelve_depot(shelve_id)

    def get_latest_di_cl_from_p4(self):

        return self._p4_test.get_latest_p4_cl()        
    

def build_di(commit_id, di_folder, build_base, executable, build_info):

    if build_frontend_dict.has_key(executable):
        build_frontend = build_frontend_dict[executable]
    else:
        build_frontend = ''

    build_full_path = os.path.normpath(os.path.join(build_base, build_frontend, build_info['build_platform']))

    platform = '_'.join([build_info['build_platform'], build_info['build_tool']])
    run_build = getBuilder(build_full_path, platform)
    build_executable = filter_target(build_info['build_backend'], run_build.get_targets()[1])

    print "==================== Build %s under %s ====================" % (build_executable, build_full_path)
    build_success, stdout, stderr = run_build.build(build_executable, False, True, parallel=0, \
        background=True)
    print "==================== Build complete ===================="
    
    build_result = int(not build_success)

    build_frontend = os.path.join(di_folder, build_frontend, build_info['build_platform'])

    old_build_log = os.path.join(build_frontend, 'build.log')
    build_log =  open(old_build_log, 'w')
    build_log.write(stdout)
    build_log.write(stderr)
    build_log.close()
    
    new_build_log = os.path.join(build_frontend,'build'+'_'+commit_id+'.log')
    os.rename(old_build_log, new_build_log)

    return (build_result, build_frontend, build_executable)

def exec_test(exec_cmd):
    #system(exec_cmd, echo=True)
    ret = os.system(exec_cmd)
    print ret 
    return ret
    
def transform_log_2_csv(test_folder, build_area, build_frontend, commit_id):
    # full_path = os.path.join(test_folder, build_area, build_frontend)
    # current_path = os.getcwd()
    # os.chdir(full_path)
    # shutil.copy('/mnt/DI_TEST/Source/benchmark/log2csv.sh', '.')
    # command = "./log2csv.sh profile_report.log > profile_report.csv"
    # os.system(command)
    #
    # new_csv = "profile_report.csv"
    # new_csv_list = new_csv.split(".")
    # new_csv = new_csv_list[0] + "_" + commit_id + '.csv'
    # os.environ['new_csv'] = str(new_csv)
    # command = "mv profile_report.csv $new_csv"
    # os.system(command)
    
    # os.chdir(current_path)
    pass
    
def get_profile_log(build_frontend, commit_id, build_executable, db_table_name, insert_db, df_insert):

    old_environment = os.path.join(build_frontend, "environment.log")

    if insert_db:
        values = parse_environment_report(old_environment)
        df_insert['unitperf'] = 'cycle'
        df_insert['cmd'] = values['cmd']
        df_insert['backend'] = values['backend']
        df_insert['board'] = values['board']
        df_insert['target'] = values['target']
        df_insert['os'] = values['os']
        df_insert['arch'] = values['arch']
        df_insert['changelist'] = values['changelist']
        df_insert['compiler'] = values['compiler']
        df_insert['technology'] = 'di'
        argument = dict()
        argument['schemaName'] = db_table_name
        argument['dataframe'] = df_insert
        argument['type'] = UPDATE_TO_SQL
        argument['strategyExec'] = 'MySql'
        ee = MySqlEngine(**argument)
        def savetomysqlwrap(event):
            save_to_mysql_profiling(event._df, event._schemaName, db_eng_signal)       
        ee.register(UPDATE_TO_SQL, savetomysqlwrap)
        ee.start()
        time.sleep(1)
        ee.stop()

    if platform.system() != "Windows":
    
        backup_bin = build_executable + '_' + commit_id
        shutil.copy(os.path.join(build_frontend, build_executable), os.path.join(build_frontend, backup_bin))
            
        new_environment = os.path.basename(old_environment).split(".")[0] + "_" + commit_id + ".log"
        new_environment = os.path.join(build_frontend, new_environment)
        os.rename(old_environment, new_environment)
    
def merge_compare(build_frontend, loop_times, meas_val, current_changelist, behaviour):

    log_name = os.path.join(build_frontend, "profile_report.log")
    node_lists = []
    for i in range(loop_times):
        new_name = os.path.basename(log_name).split('.')[0] + '_' + current_changelist + '_' + str(i+1) + '.log'
        new_name = os.path.join(build_frontend, new_name)
        node_lists.append(ParsedProfilingReport(new_name).parse())
   
    #Get the index
    
    df_alltc = pd.DataFrame()
    behaviour_mapping = {'default' : 'median', 'codec' : 'min', 'worst' : 'max'}
    for row in zip(*node_lists):
        if row[0].name.key == 'Root-Node':
            continue

        values = {'max_value' : 'max', 'min_value' : 'min', 'avg_value' : 'avg'}

        df_tc = pd.DataFrame([row[0].name.key],columns=['test_case_name'])
 
        #Find the middle of min value list to make sure it reproducible and not a noise
        for key, value in values.items():
        
            data = map(lambda i : getattr(i, value).key, row)
            df = pd.DataFrame(data, columns=[key])
            # Round down cycle numbers
            df_tc=df_tc.join(pd.DataFrame([floor(getattr(df, behaviour_mapping[behaviour])())]))
        
        df_alltc = df_alltc.append(df_tc)
   
    return df_alltc

    
def logs_backup(backup_folder, test_folder, build_area, profiling_logs, current_changelist, algorithm):
    #profiling_logs = kit_logs_folder + '/../profiling_logs'
    profiling_log_folder = profiling_logs + test_folder + '/' + build_area + '/' + current_changelist + '/' + algorithm
    print profiling_log_folder
    #os.mkdir('profiling_log_folder')

    # handle exception due to same profiling_log_folder name for fft and fft_mem
    try:
        shutil.copytree(backup_folder, profiling_log_folder)
    except OSError as e:
        print "Back up folder already exists. Skip!"
        pass

def filter_target(backend, target_lists):

    for target in target_lists:
        if backend in target:
            return target

    return None

def copyFiles(src, dst):

    for file in os.listdir(src):
        source_file = os.path.join(src, file)
        target_file = os.path.join(dst, file)

        if os.path.isfile(source_file):
            if not os.path.exists(dst):
                os.makedirs(dst)

            if not os.path.exists(target_file):
                open(target_file, "wb").write(open(source_file, "rb").read())

        if os.path.isdir(source_file):
            copyFiles(source_file, target_file)









