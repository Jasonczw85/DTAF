"""This module defines and validates the command line options"""

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

import itaf_params
from error import UserError 
#import filtering
from optparse import OptionParser, IndentedHelpFormatter, OptionGroup

import multiprocessing
import textwrap
import re
import sys
import os
import pdb

class OptionParserReturn1(OptionParser):
    """Same as OptionParser, but exits with 1 on error"""

    def error(self, msg):
        self.print_usage(sys.stderr)
        self.exit(1, "%s: error: %s\n" % (self.get_prog_name(), msg))

class PlainHelpFormatter(IndentedHelpFormatter):
    
    def format_option(self, option):
        """
        This custom formatter allows for "\n" to be used in the option help dialog.
        """
        result = []
        opts = self.option_strings[option]        
        opt_width = self.help_position - self.current_indent - 2
        
        if len(opts) > opt_width:
            opts = "%*s%s\n" % (self.current_indent, "", opts)
            indent_first = self.help_position
        else: # start help on same line as opts
            opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
            indent_first = 0
        result.append(opts)
            
        if option.help:
            help_text = self.expand_default(option)

            # custom formatting (start)
            help_lines = []
            for para in help_text.split("\n"):
                help_lines.extend(textwrap.wrap(para, self.help_width))
            # custom formatting (end)

            result.append("%*s%s\n" % (
                                   indent_first, "", help_lines[0]))
            result.extend(["%*s%s\n" % (self.help_position, "", line)
                       for line in help_lines[1:]])
        elif opts[-1] != "\n":
            result.append("\n")
        return "".join(result) + "\n" 

def usage(run_type="external", args=None):
    """Creates the help usage dialog, command line options and corresponding default values.
    This function parses the command line options set by the user.

    run_type: indicates whether this is an internal or external version of the framework. [internal, external]
    args: The command line to parse (e.g. sys.argv)

    Returns: instance of itaf_params.ITAF_params containing the parameter values.
    """
    
    if isinstance(args, basestring):
        args = args.split()

    formatter = PlainHelpFormatter()
    formatter.set_long_opt_delimiter(" ")

    parser = OptionParserReturn1(formatter=formatter, add_help_option=False)

    if run_type == "internal":
        extra = " Cannot be used in combination with the following options: " + \
            "--verify-xml, --generate-documentation"
    else:
        extra = ""

    parser.add_option("-h", 
                      "--help", 
                      default=False, 
                      action="store_true", 
                      help="Show this message and exit.\n"
                      "(default = OFF)\n"
                      )
    parser.add_option("-v", 
                      "--verbosity",
                      default="INFO", 
                      help="The verbosity LEVEL controls how much information about the current test run is displayed:\n"
                      "QUIET = Displays no information.\n"
                      "ERROR = Displays only error messages.\n"
                      "WARNING = Displays all warnings and errors.\n"
                      "INFO = Displays all information, except debug messages.\n"
                      "DEBUG = Displays all debug information.\n"
                      "(default = INFO)\n"
                      )


    # Advanced Options
    advanced_group = OptionGroup(parser, "Advanced options")
    advanced_group.add_option("-p", 
                              "--help-plugin",
                              metavar="NAME",
                              help="Display the documentation of the plug-in with the given NAME.%s "
                              "\n" % extra
                              )
    advanced_group.add_option("-l", 
                              "--list-plugins", 
                              default=False, 
                              action="store_true", 
                              help="Display a list of all processing plug-ins available to the test framework.%s "
                              "\n(default = OFF)" % extra
                              )
    advanced_group.add_option("-e",
                              "--extract-source",
                              metavar="CATEGORY",
                              default="zip",
                              dest="extract",
                              help="Comma-separated list of extract to use.\n"
                              "\n(default = zip)"
                              )

    advanced_group.add_option("-c", 
                              "--config-file",
                              metavar="FILE",
                              dest="config_file",
                              help="Path to the configuration file."
                              "\n(default = itaf/../itaf.config)"
                              )

    advanced_group.add_option("-s",
                              "--config-file-section",
                              metavar="TAG",
                              dest="config_file_section",
                              default=None, 
                              help="Path to the configuration file."
                              "\n(default = None)"
                              )

    advanced_group.add_option("-b",
                              "--test-execution-folder",
                              metavar="TAG",
                              dest="test_exec_folder",
                              help="Folder to execute the test."
                              "\n(default = ~/)"
			      )

    advanced_group.add_option("-i",
                              "--dolby-intrinsics-folder",
                              dest="replace_src_folder",
                              help="Folder to execute the test."
                              "\n(default = ~/)",
                              default="~/"
                              )
    
    advanced_group.add_option("-t",
                              "--transform-to-csv",
                              metavar="TAG",
                              dest="is_transform_csv",
                              action="store_true",
                              default=False,
                              help="Specify whether transform to csv format."
                              "\n(default = False)"
                             )

    advanced_group.add_option("-T",
                              "--insert-db",
                              metavar="TAG",
                              dest="insert_db",
                              action="store_true",
                              default=False,
                              help="Specify whether insert to data base."
                              "\n(default = False)"
                             )                             
                             
    advanced_group.add_option("-m",
                              "--loop-times",
                              metavar="",
                              dest="loop_times",
                              default=1,
                              type=int,
                              help="Specify how many times to run for DI profiling."
                              "\n(default = 1)"
                             )
			     
    advanced_group.add_option("-K",
                              "--knowledge-base-folder",			      
                              metavar="TAG",
                              dest="knowledge_base_folder",
                              help="Specify what's the path of knowledge base."
                              "\n(default = /mnt/DI_TEST/KL_File)",
                              default="/mnt/DI_TEST/KL_File"
                             )

    advanced_group.add_option("-L",
                              "--kit-logs-folder",			      
                              metavar="TAG",
                              dest="kit_logs_folder",
                              help="Specify what's the path of backup kit tests logs ."
                              "\n(default = /mnt/DI_TEST/Logs/kit_logs)",
                              default="/mnt/DI_TEST/Logs/kit_logs"
                             )
			     
    advanced_group.add_option("-S",
                              "--kit-src-folder",			      
                              metavar="TAG",
                              dest="kit_src_folder",
                              help="Specify what's the path of kit source zip packages ."
                              "\n(default = None)",
                              default=None
                             )                 
                 
    advanced_group.add_option("-P",
                              "--profiling_logs",			      
                              metavar="TAG",
                              dest="profiling_logs",
                              help="Specify what's the path of backup profiling tests logs ."
                              "\n(default = /mnt/DI_TEST/Logs/profiling_logs)",
                              default="/mnt/DI_TEST/Logs/profiling_logs"
                             )	
                             
    advanced_group.add_option("-k",
                              "--no-modify-cmd",
                              metavar="TAG",
                              dest="is_modify_cmd",
                              action="store_false",
                              default=True,
                              help="Specify whether modify command."
                              "\n(default = True)"
                             )
                             
    advanced_group.add_option("--skip-with-record",
                              metavar="TAG",
                              dest="skip_with_record",
                              action="store_true",
                              default=False,
                              help="skip_with_record."
                              "\n(default = False)"
                             )
                             
    advanced_group.add_option("-D",
                              "--dap-analysis",
                              metavar="TAG",
                              dest="dap_analysis",
                              action="store_true",
                              default=False,
                              help="Enable DAP test analysis tool."
                              "\n(default = False)"
                             )
    
    advanced_group.add_option("-A",
                              "--binary-search",
                              metavar="",
                              dest="binary_search",
                              default=None,
                              help="Enable binary search."
                              "\n(default = None)"
                             )

    advanced_group.add_option("--exec-cmd-post",
                              metavar="TAG",
                              dest="exec_cmd_post",
                              default=None,
                              help="insert exec post cmd."
                              "\n(default = None)"
                             )
    
    advanced_group.add_option("-N",
	                          "--no-email-notify",
                              metavar="EMAIL",
                              dest="email_notify",
                              action="store_false",
                              default=True,
                              help="Specify whether email notify."
                              "\n(default = True)"
                             )

    advanced_group.add_option("-B",
                              "--Build-only",        
                              metavar="BUILD",
                              dest="build_only",
                              action="store_true",
                              default=False,
                              help="Build without exec test."
                              "\n(default = False)"                              
                             )

    advanced_group.add_option("--db-name",
                              metavar="TAG",
                              dest="db_name",
                              default='test1',
                              help="Specify the name of database."
                              "\n(default = %default)"
                             )      
                             
    advanced_group.add_option("--board-username",
                              metavar="TAG",
                              dest="board_username",
                              default=None,
                              help="Specify remote board username."
                              "\n(default = %default)"
                             )
    
    advanced_group.add_option("--board-ip",
                              metavar="TAG",
                              dest="board_ip",
                              default=None,
                              help="Specify remote board ip."
                              "\n(default = %default)"
                             )
    
    advanced_group.add_option(
                             "--shelve-ID",
                             metavar="TAG",
                             dest="shelve_id",
                             default=None,
                             help="Specify shelve ID for preflight feature."
                             "\n(default = %default)"
                             )
    
    advanced_group.add_option(
                             "--initialize-db",
                             metavar="TAG",
                             dest="initialize_db",
                             action="store_true",
                             default=False,
                             help="Insert data into database when doing kit testing the first time."
                             "\n(default = %default)"
                             )

    advanced_group.add_option(
                             "--di-cl",
                             metavar="TAG",
                             dest="di_cl",
                             default=None,
                             help="Specify DI Changelist that is being tested currently."
                             "\n(default = %default)"
                             )

    advanced_group.add_option("--disable-rebuild",
                              metavar="TAG",
                              dest="disable_rebuild",
                              action="store_true",
                              default=False,
                              help="Disable automatically rebuilding former 5 changelists."
                              "\n(default = %default)"
                              )

    advanced_group.add_option(
                              "--test-only",
                              metavar="TAG",
                              dest='test_only',
                              action='store_true',
                              default=False,
                              help="Skip build process and run test only."
                              "\n(default = %default)"
                              )

    advanced_group.add_option(
                              "--copy-path",
                              metavar="TAG",
                              dest='copy_path',
                              default=None,
                              help='Specify path to copy test resources from.'
                              "\n(default = %default)"
                              )

    advanced_group.add_option("--db-host",
                              metavar="TAG",
                              dest="db_host",
                              default='10.204.7.188',
                              help="Specify the host of database."
                              "\n(default = %default)"
                             )
                             
    advanced_group.add_option("--db-login",
                              metavar="TAG",
                              dest="db_login",
                              default="root;root",
                              help="Specify the username and password of database, divided by ';'."
                              "\n(default = %default)"
                             )
    
    advanced_group.add_option("--p4-port",
                              metavar="TAG",
                              dest="p4_port",
                              default="Perforce-bjo.dolby.net:1666",
                              help="Specify the Perforce server."
                              "\n(default = %default)"
                             )     
    
    advanced_group.add_option("--p4-login",
                              metavar="TAG",
                              dest="p4_login",
                              default="testlc;taC%g17#",
                              help="Specify the username and password of Perforce, divided by ';'."
                              "\n(default = %default)"
                             )

    advanced_group.add_option("--codec-behaviour",
                              metavar="TAG",
                              dest="codec_behaviour",
                              action="store_true",
                              default=False,
                              help="Apply min[AVG] as final result for Dolby's Technology with various code routines."
                              "\n(default = %default)"
                              )

    advanced_group.add_option("--worst-behaviour",
                              metavar="TAG",
                              dest="worst_behaviour",
                              action="store_true",
                              default=False,
                              help="Apply max[MAX] as final result for evaluating chip set of Dolby Technology's behavior on DSP/TI Simulator."
                              "\n(default = %default)"
                              )

    advanced_group.add_option("--meas-val",
                              metavar="TAG",
                              dest="meas_val",
                              default="min;min;min",
                              help="Specify the interested measurement value, divided by ';', and the form is \
                              '<max|min>;<max|min>;<max|min>'. The first section represents the highest computational \
                              complexity (the value of 'Max' in the profile log file), the second one represents \
                              the average computational complexity (the value of 'Avg' in the profile log file), \
                              and the third one represents the lowest computational complexity(the value of 'Min' in the profile log file)."
                              "\n(default = %default)"
                             )    
                             
    parser.add_option_group(advanced_group)
    

    # Now, parse the parameters as defined above
    if args is None:
        (options, remainder) = parser.parse_args()  # Not equivalent to passing sys.argv
    else:
        (options, remainder) = parser.parse_args(args)
    
    remainder = [s for s in remainder if len(s.strip()) > 0]
    if len(remainder) > 0:
        raise UserError('Unrecognized arguments: "%s"' % " ".join(remainder))
    
    if options.help:
        parser.print_help()
        sys.exit(0)

    itaf_params_obj = itaf_params.ITAF_Params()
    
    if not options.verbosity in ["QUIET", "ERROR",  "WARNING", "INFO", "DEBUG"]:
        raise UserError("Invalid command line option value: '%s'" % options.verbosity)
    else: 
        itaf_params_obj.set_itaf_param("test_run_spec", "verbosity_mode", options.verbosity)
        
    # Set extract selection
    
    # If the option is given, verify that it consists of comma-separated
    # categories which contain only alphanumerics and underscore.
    for c in options.extract:
        if not re.match("[0-9A-Za-z_,]", c):
            raise UserError("Executor categories string '%s' contains an illegal character '%s'" % \
                                (options.extract, c))

    if options.extract not in ["zip", "dir", "P4", "P4zip", 'copy']:
        raise UserError("Unknown source code extract from: '%s'" % options.extract)
    itaf_params_obj.set_itaf_param("test_run_spec", "extract", options.extract)

    # Setting corresponding test run parameters #
    itaf_params_obj.set_itaf_param("test_run_spec", "config_file", options.config_file)
    itaf_params_obj.set_itaf_param("test_run_spec", "config_file_section", options.config_file_section)
    itaf_params_obj.set_itaf_param("test_run_spec", "knowledge_base_folder", options.knowledge_base_folder)
    itaf_params_obj.set_itaf_param("test_run_spec", "kit_logs_folder", options.kit_logs_folder)
    itaf_params_obj.set_itaf_param("test_run_spec", "kit_src_folder", options.kit_src_folder)
    itaf_params_obj.set_itaf_param("test_run_spec", "dap_analysis", options.dap_analysis)
    itaf_params_obj.set_itaf_param("test_run_spec", "profiling_logs", options.profiling_logs)
    itaf_params_obj.set_itaf_param("test_run_spec", "replace_src_folder", options.replace_src_folder)
    itaf_params_obj.set_itaf_param("test_run_spec", "is_transform_csv", options.is_transform_csv)
    itaf_params_obj.set_itaf_param("test_run_spec", "insert_db", options.insert_db)
    itaf_params_obj.set_itaf_param("test_run_spec", "loop_times", options.loop_times)
    itaf_params_obj.set_itaf_param("test_run_spec", "binary_search", options.binary_search)
    itaf_params_obj.set_itaf_param("test_run_spec", "exec_cmd_post", options.exec_cmd_post)
    itaf_params_obj.set_itaf_param("test_run_spec", "is_modify_cmd", options.is_modify_cmd)
    itaf_params_obj.set_itaf_param("test_run_spec", "skip_with_record", options.skip_with_record)
    itaf_params_obj.set_itaf_param("test_run_spec", "email_notify", options.email_notify)
    itaf_params_obj.set_itaf_param("test_run_spec", "build_only", options.build_only)

    itaf_params_obj.set_itaf_param("test_run_spec", "db_name", options.db_name)
    itaf_params_obj.set_itaf_param("test_run_spec", "db_host", options.db_host)
    itaf_params_obj.set_itaf_param("test_run_spec", "db_login", options.db_login)
    itaf_params_obj.set_itaf_param("test_run_spec", "p4_port", options.p4_port)
    itaf_params_obj.set_itaf_param("test_run_spec", "p4_login", options.p4_login)
    itaf_params_obj.set_itaf_param("test_run_spec", "meas_val", options.meas_val)
    itaf_params_obj.set_itaf_param("test_run_spec", "board_username", options.board_username)
    itaf_params_obj.set_itaf_param("test_run_spec", "board_ip", options.board_ip)
    itaf_params_obj.set_itaf_param("test_run_spec", "shelve_id", options.shelve_id)
    itaf_params_obj.set_itaf_param("test_run_spec", "initialize_db", options.initialize_db)
    itaf_params_obj.set_itaf_param("test_run_spec", "di_cl", options.di_cl)
    itaf_params_obj.set_itaf_param("test_run_spec", "worst_behaviour", options.worst_behaviour)
    itaf_params_obj.set_itaf_param("test_run_spec", "codec_behaviour", options.codec_behaviour)
    itaf_params_obj.set_itaf_param("test_run_spec", "disable_rebuild", options.codec_behaviour)
    itaf_params_obj.set_itaf_param("test_run_spec", "test_only", options.test_only)
    itaf_params_obj.set_itaf_param("test_run_spec", "copy_path", options.copy_path)

    if options.test_exec_folder is None:
        itaf_params_obj.set_itaf_param("test_run_spec", "test_exec_folder", "~/")
    else:
        if not os.path.exists(options.test_exec_folder):
            os.makedirs(options.test_exec_folder)
        itaf_params_obj.set_itaf_param("test_run_spec", "test_exec_folder", options.test_exec_folder)
    
    return itaf_params_obj
