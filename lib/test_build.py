import os
import posixpath
import ntpath
import sys
import platform
import subprocess
import shutil
import re
import stat
import pdb
from optparse import OptionParser

  

from test_profiler import Profiler

def test_profile():
    parser = OptionParser()
    parser.add_option("-f", "--log--", dest="logfile1", help="execution log")
    parser.add_option("-e", "--env--", dest="logfile2", help="environment log")
    parser.add_option("-t", "--table--", dest="table_name", help="database table name")
    
    (options, args) = parser.parse_args()
    args={'logfile1': options.logfile1, 'logfile2' : options.logfile2, 'table_name' : options.table_name} 

    profiler = Profiler(args)
    success = profiler.run()

if __name__ == '__main__':
    test_profile()




