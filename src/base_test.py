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

               Copyright (C) 2011 by Dolby Laboratories,
               Copyright (C) 2011-2012 by Dolby International AB.
                           All rights reserved.
"""

from ConfigParser import SafeConfigParser
from error import UserError
import os
import sys
import pdb
import platform
import logging
import zipfile
import shutil
import shlex
import time
import re
import subprocess
from subprocess import CalledProcessError


from lib.p4_opr import P4_Ops 

class Run_Test(object):
    """This class contains the interface of running profiling testing.
    Returns zero if no tests failed, otherwise 2.
    """
    
    def __init__(self, **kwargs):
        """Initializing all run_profiling_test data structures"""            
        
        self.kwargs = kwargs
        self._test_proj_folder=kwargs["test_proj_folder"]
        self._extract=kwargs["extract"]
        self._replace_src_folder=kwargs["replace_src_folder"]
        self._is_modify_cmd=kwargs["is_modify_cmd"]
        self._knowledge_base_folder=kwargs["knowledge_base_folder"]
        self._kit_logs_folder=kwargs["kit_logs_folder"]
        self._kit_src_folder=kwargs["kit_src_folder"]
        self._dap_analysis=kwargs["dap_analysis"]
        self._binary_search=kwargs["binary_search"]
        self._exec_cmd_post=kwargs["exec_cmd_post"]
        self._board_username=kwargs["board_username"]
        self._board_ip=kwargs["board_ip"]
        self._shelve_id=kwargs["shelve_id"]
        self._initialize_db=kwargs["initialize_db"]
        self._email_notify=kwargs["email_notify"]
        self._build_only = kwargs["build_only"]
        self._build_area=kwargs["build_area"]
        self._zip_packages=kwargs["zip_packages"]
        self._p4_repo=kwargs["p4_repo"]
        self._zip_repos=kwargs["zip_repos"]
        self._executable=kwargs["executable"]
        self._build_platform=kwargs["build_platform"]
        self._build_tool=kwargs['build_tool']
        self._cmd_path=kwargs["cmd_path"]
        self._di_folder=kwargs["di_folder"]
        self._dut_exec=kwargs["dut_exec"]
        self._modify_cmd=kwargs["modify_cmd"]
        self._make_flag=kwargs["make_flag"]
        self._version=kwargs["version"]
        self._exec_cmd=kwargs["exec_cmd"]
        self._exec_dir=kwargs["exec_dir"]
        self._runtime_config_section=kwargs["config_file_section"]
        self._changelist = kwargs["di_cl"]
        self._test_only = kwargs ['test_only']
        self._copy_path = kwargs['copy_path']


        self._build_test_arguments = {
                                        'type' : 'BUILD_AND_RUN_TEST',
                                        'schemaName' : 'build_and_run_test', 
                                        'executable' : [i for i in self._executable.split(';')]
                                     }

        
        self._full_di_path = os.path.join(self._test_proj_folder, self._di_folder)
        self._executable_folder = os.path.join(self._test_proj_folder, self._build_area) 
        os.chdir(self._test_proj_folder)
        print ("Change to project directory %s" %self._test_proj_folder)
 
        
        self.logger = logging.getLogger('Core Test Started')
        self.logger.setLevel(logging.INFO)
        # pt specified
        fh = logging.FileHandler(os.path.join(os.getcwd(),'core_test.txt'),'w')
        fh.setLevel(logging.INFO)
        
        formatter = logging.Formatter(\
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.info("Change dir to test project: %s" %self._test_proj_folder)
        
        for (key, value) in kwargs.items():
            self.logger.info("key:%s value: %s" %(key, value))

    def init_p4_instance(self, args):  
        
        self._p4_test = P4_Ops(**args)

    def modify_code(self):
        
        os.system(self._modify_cmd)
        self.logger.info("3, modify_code: %s" %self._modify_cmd)
    
    def exec_test(self, exec_cmd):
        # deprecated: 15th-Apr. 2016
        #system(exec_cmd, echo=True)
        # ret = os.system(self._exec_cmd)

        # updated: 15th-Apr. 2016, Kevin Li
        self.logger.info("6, execute test: %s" % exec_cmd)
        subp = subprocess.Popen(exec_cmd, shell=True,
                                stdout=subprocess.PIPE)
        # out, err = process.communicate()
        while subp.poll() is None:
            print subp.stdout.readline().strip()
            subp.stdout.flush()
        return subp.returncode

    def delete_client(self):

        self._p4_test.cleanup_remote_client()
    
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