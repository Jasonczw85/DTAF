"""This module contains the definitions of all ITAF parameters


    Initializes corresponding data container    
    initialize_itaf_param(data_container)
        Parameter: <test_run_spec, test_case_spec, processing_stage_spec, input_output_file_spec>

    Setting data container element with passed in value
    set_itaf_param(data_container, key, value)
        Parameters: 
            data_container = <test_run_spec, test_case_spec, processing_stage_spec, input_output_file_spec>
            key = < element name > element name ranges and differs for each corresponding data container
            value = < set value >

    Get data container element value 
    get_itaf_param(data_container, key)
        Parameters: 
            data_container = <test_run_spec, test_case_spec, processing_stage_spec, input_output_file_spec>
            key = < element name > element name ranges and differs for each corresponding data container
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
from error import UserError
import os
import pdb
import platform

_config_filename = None        # global variable
_config_dict = None            # global variable
_test_run_spec = None          # global variable

config_options = [("p4_repo", "",
                   "';'-separated list of additional executable search paths. "
                   "to the system PATH environment variable"),
                  
                  ("version", "",
                   "';'-separated list of test specs top-level directories"),
                  
                  ("build_area", "",
                   "Top-level working directory"),
                  
                  ("executable", "",
                   "','-separated list of reporter back-ends"),

                  ("build_platform", "",
                   "Combination of os, processor and toolchain. E.g. linux_x86_gnu"),

                  ("build_tool", "",
                   "Build action. E.g. make/msvs2015"),

                  ("build_backend", "",
                   "Combination of backend and flavour. E.g. generic_float32_release"),
                  
                  ("exec_dir", "",
                   "Name of the package that uses ITAF. This option is used only for the generation of test case documentation"),
                  
                  ("exec_cmd", "",
                   "Name of the package that uses ITAF. This option is used only for the generation of test case documentation"),
                  
		              ("make_flag", "",
		               "Additional options for binary make"),
				  
                  ("cmd_path", "",
                   "Name of the package that uses ITAF. This option is used only for the generation of test case documentation"),
                  
                  ("plugin_dirs", "",
                   "Name of the package that uses ITAF. This option is used only for the generation of test case documentation"),

                  ("system_path", "",
                   "Name of the package that uses ITAF. This option is used only for the generation of test case documentation"),
                  
                  ("doc_dir", "test_doc",
                   "Test case static documentation output directory"),

                  ("zip_repos", "",
                   "Test case static documentation output directory"),

                  ("zip_packages", "",
                   "Test case static documentation output directory"),

                  ("di_folder", "",
                   "Test case static documentation output directory"),

                  ("dut_exec", "",
                   "Test case static documentation output directory"),

                  ("modify_cmd", "",
                   "Test case static documentation output directory"),
                   
                  ("db_table_name", "",
                   "Data base table"),

                  ("change_list", "",
                   "the list that needed to run")

                  ]


class ITAF_Params:
    """This class contains all ITAF data container and functions to get, set and initialize all data members"""
    
    def __init__(self):
        """Initializing all ITAF data structures"""

        global _test_run_spec

        self.test_run_spec = dict()
        # Initializing ITAF data container #
        self.initialize_itaf_param("test_run_spec")
        _test_run_spec = self.test_run_spec
        
    def initialize_itaf_param(self, data_container):
        """Initializes the corresponding data container"""
        try : 
            # Converts the string type into an actual dictionary type #
            data_container_dict = getattr(self, data_container)
        except NameError:
            raise Exception("Invalid data container type: " + str(data_container_dict))

        if data_container == "test_run_spec" :
            # This dictionary contains all test run specific parameters/data #
            self.test_run_spec = { 
                                   # (string) Indicates which verbosity mode to run [QUIET, ERROR, WARNING, INFO, DEBUG] #
                                   'verbosity_mode' : "INFO",
                                   # (string) configuration file
                                   'config_file' : None,
                                   # (string) configuration file
                                   'config_file_section' : None,
                                   # (string) extract selection
                                   'extract' : None,
                                   # (string) replace_src_folder 
                                   'replace_src_folder' : None,
                                   # (string) knowledge_base_folder
                                   'knowledge_base_folder' : None,
                                   # (string) kit_logs_folder
                                   'kit_logs_folder' : None,
                                   # (string) kit_src_folder
                                   'kit_src_folder' : None,
                                   # (string) profiling_logs
                                   'profiling_logs' : None,
                                   # (boolean) dap_analysis
                                   'dap_analysis' : False,
                                   # (boolean) whether email notify flag
                                   'email_notify' : True,
                                   # (boolean) whether build only flag
                                   'build_only' : False,
                                   # (string) binary_search
                                   'binary_search' : None,
                                   # (string) exec_cmd_post
                                   'exec_cmd_post' : None,                                   
                                   # (string) extract selection
                                   'test_exec_folder' : None,
                                   # (boolean) transform to csv format flag #
                                   'is_transform_csv' : False,
                                   # (string) insert_db
                                   'insert_db' : False,
                                   # (int) loop_times
                                   'loop_times' : 1,
                                   # (boolean) whether modify command flag #
                                   'is_modify_cmd' : True,
                                   # (boolean) whether skip test when database has record #
                                   'skip_with_record' : False, 
                                   # (string) specify remote board username
                                   'board_username' : None,
                                   # (string) specify remote board ip
                                   'board_ip' : None,
                                   # (string) specify shelve id for preflight feature
                                   'shelve_id' : None,
                                   # (boolean) whether doing initialize data
                                   'initialize_db' : False,
                                   # (string) DI changelist number
                                   'di_cl' : None,
                                   # Apply min[AVG] as final result
                                   'codec_behaviour' : False,
                                   # Apply max[MAX] as final result
                                   'worst_behaviour' : False,
                                   # Disable automatically rebuilding former 5 changelists
                                   'disable_rebuild' : False,
                                   # Skip build process and build only
                                   'test_only' : False,
                                   # Path to copt test resources from
                                   'copy_path' : None,
                                   # (string) specify the database name #
                                   'db_name' : 'test1',
                                   # (string) specify the database host #
                                   'db_host' : '10.204.7.188',
                                   # (string) specify the username and password of database, divided by ';'. #
                                   'db_login' : "root;root",
                                   # (string) specify the Perforce server #
                                   'p4_port' : "Perforce-bjo.dolby.net:1666",
                                   # (string) specify the username and password of Perforce, divided by ';' #
                                   'p4_login' : "testlc;taC%g17#",
                                   # (string) specify the interested measurement value, divided by ';' #
                                   'meas_val' : "min;min;min"
                }
        else :
            raise Exception("Invalid data container type: " + str(data_container_dict))

    def set_itaf_param(self, data_container, key, value):
        """Sets the corresponding data container element(key) with passed in value(value)"""
        try : 
            # Converts the string type into an actual dictionary type #
            data_container_dict = getattr(self, data_container)
        except Exception, e:
            raise Exception("Invalid data container type: " + str(data_container_dict))
        
        # Checks if "data_container_obj" is an actual dictionary #
        if isinstance(data_container_dict, dict) :
            # Checks if "data_container_obj" dictionary has valid key #
            if key in data_container_dict :
                # Checks if "data_container_obj[key]" is an List #
                if isinstance(data_container_dict[key], list):
                    data_container_dict[key].append(value)
                else :
                    data_container_dict[key] = value
            else :
                raise Exception("Invalid key : " + str(key) + " Invalid data container: " + str(data_container))
        else :
            raise Exception("Invalid data container type: " + str(data_container_dict))

    def get_itaf_param(self, data_container, key):
        """Gets the corresponding data container element(key)"""
        try : 
            # Converts the string type into an actual dictionary type #
            data_container_dict = getattr(self, data_container)
        except Exception, e:
            raise Exception("Invalid data container: " + str(data_container))
        
        # Checks if "data_container_obj" is an actual dictionary #
        if isinstance(data_container_dict, dict):
            # Checks if "data_container_obj" dictionary has valid key #
            if key in data_container_dict :
                return data_container_dict[key]
            else :
                raise Exception("Invalid key : " + str(key) + " In valid data container:" + str(data_container))
        else :
            raise Exception("Invalid data container type: " + str(data_container_dict))



class AddSectionHeader(object):
    """This class wraps a file pointer, and behaves like a file pointer.
    
    It has the effect of adding the line "[section]\n"
    to the beginning of the file.

    This class exists because python's ConfigParser wants to have
    the "[section]" but we do not require that line in the itaf.config file.
    """
    def __init__(self, fp):
        self.fp = fp
        self.first_line = True
        
    def readline(self):
        if self.first_line:
            self.first_line = False
            return '[section]\n'
        else:
            return self.fp.readline()

itaf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
def get_config(config_file, config_file_section):
    """Reads in configuration options from configuration file
    Returns dictionary of options names and values

    config_file: path to configuration file, or None in which case
           the default values are returned
    """
    all_options = dict([(c[0], c[1]) for c in config_options])

    parser = SafeConfigParser(defaults=all_options)
    if not config_file is None:
        config_file = os.path.abspath(config_file)
        if not os.path.isfile(config_file):
            raise UserError("Configuration file '%s' does not exist. "
                            "Use the --config-file option to specify a non-default configuration file path. ")
        try:
            parser.readfp(AddSectionHeader(open(config_file, "rU")))
            items = parser.items(config_file_section)
        except Exception, e:
            raise UserError("%s: %s" % (config_file, str(e)))

    result = dict(items)

    for option in result:
        if not option in all_options and not option.startswith("user_"):
            raise UserError('%s: Unrecognized option "%s". '
                            'The recognized options are %s. '
                            'User-defined options must start with "user_".' % \
                            (config_file, option, all_options.keys()))

    # Interpret relative paths as relative to the config file
    # convert "C:\some\thing" to "C:/some/thing" because the config file uses forward slashes
    if platform.system() != "Windows":
        config_file_dir = os.path.abspath(os.path.dirname(config_file)).replace("\\", "/")
    else:
        config_file_dir = os.path.abspath(os.path.dirname(config_file))
    
    for option in ["doc_dir"]:
        result[option] = os.path.join(config_file_dir, result[option])

    #print result.items()
    for option in ["modify_cmd", "executable", "exec_cmd"]:
        if result[option] is '':
            raise UserError('option %s: mandatory option.' % option)
    
    return result

def get_config_variables():
    """Returns dictionary of configuration variables for this session"""
    return _config_dict

def get_filename():
    return _config_filename
