#!/usr/bin/env python

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

import log
import platform
import sys
import time
import os
import random

from compatibility_test import Run_Compatibility_Test, abbre_folder_name, get_project_info
from profiling_test import Run_Profiling_Test

#
# Warn about a wrong python version, before executing any code which would
# cause the ill-versioned interpreter to fail with a less obvious error message.
#
log.init("INFO", "DEBUG", time.strftime("log-%Y_%m_%d_%H_%M_%S" + str(random.randrange(0,1001)) + ".txt"))
log.debug(" ".join(sys.argv))
    
major, minor, patchlevel = platform.python_version_tuple()
if int(major) < 2 or int(major) == 2 and int(minor) < 6:
    log.warning("Python version (%s) is too old. Python version 2.6.x or 2.7.x is required. Interpreter used is '%s' (from sys.executable)" % (platform.python_version(), sys.executable))
if int(major) > 2:
    log.warning("Python version (%s) is too new. Python version 2.6.x or 2.7.x is required. Interpreter used is '%s' (from sys.executable)" % (platform.python_version(), sys.executable))

src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.append(src_dir)

import itaf_params
#import itaf
import usage
import error
import pdb

def main(mode="external"):
    # This is the main logic model of Test Automation Framework.
    
    # Parses command line options:
    # 1, define framework parameters objective.
    # 2, initialise the data container test_run_spec as a dictionary, 
    # 3, assign the objective.    
    itaf_param_obj = usage.usage(mode)
    
    # Set verbosity log level
    log.set_verbosity(itaf_param_obj.get_itaf_param("test_run_spec", "verbosity_mode"))
    
    # Traverse this dictionary 
    cmdline_param_dict = itaf_param_obj.test_run_spec
    
    # Parameters Check
    parameters_validation_check(cmdline_param_dict)
        
    config_options = itaf_params.get_config(cmdline_param_dict['config_file'], \
    cmdline_param_dict['config_file_section'])

    # Merge the cmdline options and ini configs
    config_param_merge=cmdline_param_dict.copy()
    config_param_merge.update(config_options)

    # Abbreviate root test folder due to length issue on windows platform
    config_param_merge['abbre_config_file_section'] = config_param_merge['config_file_section']
    if platform.system() == 'Windows':
        config_param_merge['abbre_config_file_section'] = \
        abbre_folder_name(config_param_merge['config_file_section'])

    # Logs to stdout
    for (key, value) in config_param_merge.items():
        log.info(key, "=", value)

    if "bench" in config_param_merge['config_file_section'] :
    
        timestamp = 'pt-' + time.strftime("%Y_%m_%d_%H_%M_%S")
        #p4_repo = [d for d in config_options["p4_repo"].split(";") if d != ""]        
        test_folder = config_param_merge['test_exec_folder'] + '/' + \
        config_param_merge['config_file_section'] + '/' + timestamp
        
        if not os.path.exists(test_folder):
            os.makedirs(test_folder)
        log.debug("Test top level project folder", test_folder)
        
        config_param_merge['test_proj_folder'] = test_folder
        #config_param_merge['p4_repo'] = p4_repo
        print config_param_merge
        
        Run_test = Run_Profiling_Test(**config_param_merge)
        
        return Run_test.run_core_test()
        
    else:
    
        timestamp = 'ct-' + time.strftime("%Y_%m_%d_%H_%M_%S")
        p4_repo = [d for d in config_options["p4_repo"].split(";") if d != ""]        
        #test_folder = config_param_merge['test_exec_folder'] + '/' + \
        #config_param_merge['config_file_section'] + '/' + timestamp
        
        test_folder = os.path.normpath(os.path.join(config_param_merge['test_exec_folder'], \
        config_param_merge['abbre_config_file_section'], timestamp))

        if not os.path.exists(test_folder):
            os.makedirs(test_folder)
        log.debug("Test top level project folder", test_folder)
        
        config_param_merge['test_proj_folder'] = test_folder
        config_param_merge['p4_repo'] = p4_repo
        print config_param_merge
        
        Run_test = Run_Compatibility_Test(**config_param_merge)
       
        return Run_test.run_core_test()
        

def mkdir_test_toplevel_folder(test_type="pt-"):
    
    timestamp = test_type + time.strftime("%Y_%m_%d_%H_%M_%S")
    test_folder = test_exec_folder + '/' + config_file_section + '/' + timestamp
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
    log.debug("Test top level project folder", test_folder)
    
    
def parameters_validation_check(cmdline_param_dict):

    if cmdline_param_dict['config_file_section'] is None:
        raise error.UserError("Configuration file section can not be Null")

    if cmdline_param_dict['config_file'] is None:
        cmdline_param_dict['config_file'] = os.path.join(os.path.dirname(__file__), \
        "..", "kit_cfg", "linux64.ini")
        # This is allowed to not exist, in which case default values are assumed
    else:
        cmdline_param_dict['config_file'] = os.path.join(os.path.dirname(__file__), \
        "..", "kit_cfg", cmdline_param_dict['config_file'])
        if not os.path.exists(cmdline_param_dict['config_file']):
            raise error.UserError("Configuration file does not exist")

    for (key, value) in cmdline_param_dict.items():
        log.info(key, "=", value)

