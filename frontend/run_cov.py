#!/usr/bin/env python

import os
import sys
import re
import optparse
import subprocess
import shutil
from p4_opr import P4_Ops
import re
import filecmp
import difflib

class code_coverage:
    """A class that generate the api coverage of di.

    """

    def __init__(self):

        self.cov_info_file = ""
        self.time = 0    
        self.merge_cov_final = "ut-merge-cov_final.info"
        self.merge_report = "merge_report_final"
        self.full_api = "di_api_full_list"
        self.executed_api = "di_api_executed_list"
        self.not_executed_api = "di_api_not_executed_api"
        self.exclude_called_marco = "di_api_nei_exclude_called_by_macro"
        self.api_nei_ecm_marco_list = "di_api_nei_ecm_macro_list"
        self.api_nei_ecm_em_list = "di_api_nei_ecm_em_list"
        self.not_covered_list = "di_not_covered_list"
    
    def add_options(self, makefile, flag, options):

        makefile_back = makefile + '_back'
        file_read = open(makefile, 'r')
        file_write = open(makefile_back, 'w')
        try:
            stringsave=""
            stringread=file_read.readline()
            while stringread:
                if stringread.startswith(flag):
                    stringsave = stringread[:-1] + " " + options + "\n"        
                else:
                    stringsave = stringread
                file_write.writelines(stringsave)
                stringread = file_read.readline()
        finally:
            file_read.close()
            file_write.close()
        os.rename(makefile_back, makefile)

    def replace_options(self, makefile, options, replaced_options):
        
        makefile_back = makefile + '_back'
        file_read = open(makefile, 'r')
        file_write = open(makefile_back, 'w')
        try:
            stringsave=""
            stringread=file_read.readline()
            while stringread:
                if re.search(options, stringread):
                    stringsave=re.sub(options, replaced_options, stringread)
                        
                else:
                    stringsave=stringread
                file_write.writelines(stringsave)
                stringread=file_read.readline()
        finally:
            file_read.close()
            file_write.close()
        os.rename(makefile_back, makefile)

    def build(self, platform, backend):
        command = "make " + "PLATFORM=" + platform + " BACKEND=" + backend
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)    
        stdout, stderr = proc.communicate()
        
        #command = "./../../test/scripts/all_tests.py" + " -p" + platform + "_make" + " -b" + backend
        command = "./all_tests.py" + " -p" + platform + " -b" + backend
        print command
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()

    def cook_gcda(self, base_dir, src_dir):
        
        cov_src_dir = src_dir.split(";")
        cov_base_dir = base_dir.split(";")

        for i in cov_base_dir:
            for j in cov_src_dir:
                self.time = self.time + 1
                command = "lcov" + \
                            " --base-directory " + i + \
                            " --directory " + j + \
                            " --output-file " + "ut-cov" + str(self.time) + ".info" + \
                            " --gcov-tool " + "/usr/bin/gcov" + \
                            " --ignore-errors "    + "source" + \
                            " --capture "
                print command
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                stdout, stderr = proc.communicate()
                cov_log = "ut-cov" + str(self.time) + "-info.log"
                
                f1 = open(cov_log, "w")
                f1.write(stdout)        
                f1.write(str(stderr))
                f1.close()
                self.cov_info_file = self.cov_info_file + " -a " + "ut-cov"+ str(self.time) +".info"    
    
    def lcov_merge(self):

        command = "lcov " + self.cov_info_file    
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout = proc.communicate()
        f1 = open(self.merge_cov_final, 'w')
        for line in stdout:
            if isinstance(line, str):
                f1.write(line)
            else:
                f1.write(str(line))
        f1.close()

    def gen_merge_report(self):
        
        command = "genhtml " + "--output-directory " + self.merge_report + " --show-details " + self.merge_cov_final    
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)

    def get_api(self, cov_file):
    
        f_input = open(cov_file, 'r')
        f_output = open(self.full_api, 'w')    
        api = []
        for line in f_input:
            if 'poison' in line:
                line = re.sub('#pragma GCC poison DLB_DI_LOWLEVEL_OPS DLB_DI_HIGHLEVEL_OPS', '', line)
                line = re.sub('/\* .*? ?\*/', '', line)
                for i in line.split(" "):
                    if i != '' and i != '\n' and i not in api:
                        api.append(i) 

        for i in sorted(api):
            f_output.writelines(i + '\n')

        f_input.close()
        f_output.close()
            
    def get_executed_api(self):
        
        f_cov = open(self.merge_cov_final, 'r')
        f_full_api = open(self.full_api, 'r')
        f_executed_api = open(self.executed_api, 'w')
        f_not_executed_api = open(self.not_executed_api, 'w')
        
        cov_list = []
        for line in f_cov:
            cov_list.append(line)

        f_cov.close()
        fnda_list = []
        
        full_api = []
        for line in f_full_api:
            full_api.append(line)
            for i in cov_list:
                #add ',' to avoid to match this kind of api dith_DLB_X_A    
                if re.search(','+line, i) and re.search('FNDA:[1-9]', i) and i.split(',')[1] not in fnda_list:
                    fnda_list.append(i.split(',')[1])
                    
        for i in sorted(fnda_list):
            f_executed_api.writelines(i)

        lines_nm=0
        for line in full_api:
            if line not in fnda_list:
                f_not_executed_api.writelines(line)
                lines_nm += 1

        f_full_api.close()
        f_executed_api.close()
        f_not_executed_api.close()
        print "Get the executed API List, by FNDA in gcda::::", len(fnda_list)
        print "Get the not executed API List:::: ", lines_nm 

    def find_match_files(self, path, pattern, c_h_file):
        if os.path.isdir(path):
            files = os.listdir(path)    
            for f in files:
                sub_path = os.path.join(path, f)
                if os.path.isdir(sub_path):
                    self.find_match_files(sub_path, pattern, c_h_file)
                elif re.search(pattern, sub_path):
                    c_h_file.append(os.path.join(path, f))
        elif re.search(pattern, path):
            c_h_file.append(path)    

    def get_nei_exclude_called_marco(self):
        
        f_not_executed_api = open(self.not_executed_api, 'r')
        f_exclude_marco = open(self.exclude_called_marco, 'w')
        html_file = []
        path = 'merge_report_final'
        pattern = '.*\.html'
        self.find_match_files(path, pattern, html_file)
        temp = []
        for api in f_not_executed_api:
            is_linecov = False
            is_api = False
            for item in html_file:
                f_item = open(item, 'r')
                for i in f_item:
                    # api[:-1] get rid of '\n'
                    # [^_] get rid of this kind of api: dith_DLB
                    # '[ |(]' the end of api should be blank space or left bracket or the end of the line
                    # '\(' get rid of this kind of situation:  DLB_aligned_ptr(DLB_ALIGNMENT_SIZE
                    if re.search('[^_]' + api[:-1] + '[ |(]', i) or re.search('[^_]' + api[:-1] + '$', i) or re.search('\(' + api[:-1] + ',', i): 
                        is_api = True
                        if re.search('.*lineCov.*', i):
                            is_linecov = True
                            break
                f_item.close()
                if is_api and is_linecov:
                    break
            if ((not is_api) or (is_api and not is_linecov)) and (api not in temp):
                temp.append(api)

        for item in temp:
            f_exclude_marco.writelines(item)
        f_not_executed_api.close()
        f_exclude_marco.close()
        
        print "Get the not executed API List::::,", len(temp), "in total, which either excluded the called Macro APIs counted by Gcov=lineCov."
    
    def get_nei_ecm_macro_list(self):

        define_line = re.compile(r'^#define\s+')
        c_h_file = []
        path1 = ['../../dlb_dsplib/backend/generic/', '../../dlb_headroom.h', '../../dlb_derived_ops.h', '../../backend/generic/']
        path2 = '../../dlb_dsplib'
        
        def find_match_files2(path, c_h_file):
            if os.path.isdir(path):
                files = os.listdir(path)
                for f in files:
                    sub_path = os.path.join(path, f)
                    if sub_path.endswith('.h'):
                        c_h_file.append(sub_path)

        pattern = '.*\.c|\.h'
        for path in path1:
            self.find_match_files(path, pattern, c_h_file)
        find_match_files2(path2, c_h_file)    
                
                        
        f_api = open(self.exclude_called_marco, 'r')
        f_nei_ecm_marco = open(self.api_nei_ecm_marco_list, 'w')
        temp = []
        for line in f_api:
            for item in c_h_file:
                f_item = open(item, 'r')
                for i in f_item:
                    if re.search(r'^#define +' + line[:-1] + '[ |(]', i) or re.search(r'^#define +' + line[:-1] + '$', i):
                        if line not in temp:
                            temp.append(line)
                f_item.close()
        
        for i in temp:
            f_nei_ecm_marco.writelines(i)
        f_api.close()
        f_nei_ecm_marco.close()
        print "Get the not executed API List, only macro APIs::::", len(temp), "either excluded the called Macro APIs counted by Gcov=lineCov."

    def get_not_executed_function_api(self):

        f_exclude_called_marco = open(self.exclude_called_marco, 'r')
        f_nei_ecm_marco = open(self.api_nei_ecm_marco_list, 'r')
        f_nei_function = open(self.api_nei_ecm_em_list, 'w')    
        marco = []
        for line in f_nei_ecm_marco:
            marco.append(line)    
        f_nei_ecm_marco.close()

        line_nm = 0
        for line in f_exclude_called_marco:
            if line not in marco:
                line_nm += 1
                f_nei_function.writelines(line)                

        f_exclude_called_marco.close()
        f_nei_function.close()
        print "Get the not executed API List, only function APIs:::::", line_nm, "include deprecated APIs."

    def get_not_covered_api(self):

        f_nei_function = open(self.api_nei_ecm_em_list, 'r')
        shutil.copy('/mnt/DI_TEST/di_api_nei_deprecated_list', os.getcwd())
        f_deprecated = open('di_api_nei_deprecated_list', 'r')
        f_not_coverd = open(self.not_covered_list, 'w')
        deprecated = []
        for line in f_deprecated:
            deprecated.append(line)
        f_deprecated.close()

        line_nm = 0
        for line in f_nei_function:
            if line not in deprecated:
                line_nm += 1
                f_not_coverd.writelines(line)

        f_deprecated.close()
        f_nei_function.close()
        print "Finally, found the not covered API List", line_nm, "in total"

    def comp_with_reference(self, reference_file):
        if filecmp.cmp(self.not_covered_list, reference_file):
            print "There are no differences with the reference file"
        else:
            print "There are some differences with the reference file"
            file_dut = open(self.not_covered_list, 'r')
            lines_dut = file_dut.readlines()
            file_ref = open(reference_file, 'r')
            lines_ref = file_ref.readlines()
            
            d = difflib.Differ()
            diff_result = list(d.compare(lines_ref, lines_dut))
            sys.stdout.writelines(diff_result)

            file_dut.close()
            file_ref.close()
            exit(1)
        
            
def get_di_src_from_p4(p4_repo, p4_test):
    success = p4_test.connect_svr_sync_depot()
    return success[0]

def delete_client(p4_test):    
    p4_test.cleanup_remote_client()

def main():
    usage = \
    """
    %prog [options] arg1 arg2
    Example:
        %python run_cov.py -p ~/di -m dlb_intrinsics/dlb_dsplib/test
    """
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-p", "--path", dest="base_path", metavar="",
                        action="store", default='',
                        help="The path of the di")
    parser.add_option("-m", "--make_path", dest="make_path", metavar="",
                        action="store", default='',
                        help="The path of the make folder")
    parser.add_option("-r", "--refernce_file", dest="reference_file", metavar="",
                        action="store", default='',
                        help="The reference file of not covered api")

    options, args = parser.parse_args()
    client_root = options.base_path    
    make_path = options.make_path    
    reference_file = options.reference_file

    if not os.path.exists(client_root):
        os.makedirs(client_root)
    else:
        print "------Clean up the source code folder------"
        shutil.rmtree(client_root)
        os.makedirs(client_root)
        
    p4_repo = "//depot/ger/dlb_intrinsics/main/..."
    args_di = dict()
    args_di = { \
        'port': "perforce-bjo.dolby.net:1666", \
        'user': "hxzhan", \
        'password': "Dolby.123456", \
        'client_root': client_root, \
        'depot': p4_repo \
    }

    p4_test = P4_Ops(**args_di)
    get_di_src_from_p4(p4_repo, p4_test)
    delete_client(p4_test)
    
    basepath = os.path.join(client_root, 'dlb_intrinsics/make')
    makepath = []    

    a = code_coverage()
    option_for_cflags = '-fprofile-arcs -ftest-coverage'
    a.find_match_files(basepath, 'linux_x86_gnu/Makefile', makepath)
    for makefile in makepath:
        if re.match('.*make/test/[_0-9a-z]*/linux_x86_gnu', makefile):    
            a.add_options(makefile, 'CFLAGS', option_for_cflags)
            a.add_options(makefile, 'LDFLAGS', '-lgcov -fprofile-arcs')        
            a.replace_options(makefile, '-O3', '')    
        else:
            a.replace_options(makefile, '-O3', '')

    a.add_options(os.path.join(basepath, 'dlb_intrinsics/linux_x86_gnu/Makefile'), 'CFLAGS', option_for_cflags)

    dlb_compiler_keyword_gcc=os.path.join(client_root, 'dlb_intrinsics/compiler/gcc/dlb_compiler_keyword_gcc.h')
    a.replace_options(dlb_compiler_keyword_gcc, '^#define dlb_forceinline inline .*', '#define dlb_forceinline inline')

    build_path = os.path.join(client_root, make_path)
    os.chdir(build_path)

    a.build('linux_x86_gnu', 'generic_float32')

    base_dir = "../../make/test/dlb_dsplib_dct_test/linux_x86_gnu/"
    src_dir = "../../dlb_dsplib/test/;../../test/"
    base_dir_lib= "../../make/dlb_intrinsics/linux_x86_gnu/"
    src_dir_lib= "../../dlb_dsplib/backend/"

    a.cook_gcda(base_dir, src_dir)
    a.cook_gcda(base_dir_lib, src_dir_lib)
    a.lcov_merge()
    a.gen_merge_report()
    a.get_api('../../instrument/coverage/dlb_instrument_coverage.h')
    a.get_executed_api()
    a.get_nei_exclude_called_marco()
    a.get_nei_ecm_macro_list()
    a.get_not_executed_function_api()
    a.get_not_covered_api()
    a.comp_with_reference(reference_file)

if __name__ == '__main__':
    sys.exit(main())