#!/usr/bin/env python

import os
import sys
import shutil
import pdb
src_dir = os.path.join(os.path.dirname(__file__), '..', "lib")
sys.path.append(src_dir)
from p4_opr import P4_Ops

def get_di_src_from_p4(p4_repo, p4_test):
    
	success = p4_test.connect_svr_sync_depot()
	return success[0]

def delete_client(p4_test):

	p4_test.cleanup_remote_client()	

def main():
	p4_repo = "//depot/ger/dlb_intrinsics/main/..."
	client_root = os.path.join(os.getcwd(), '../../..', 'Source', 'DLB_intrinsics_main')
	args_di = dict()
	args_di = { \
	'port': "10.204.4.28:1999", \
	'user': "hxzhan", \
	'password' : "Dolby.123456", \
	'client_root' : client_root, \
	'depot' : p4_repo \
	}
	if os.path.exists(client_root):	
		print "------Clean up the source code folder------"
		shutil.rmtree(client_root)
		os.mkdir(client_root)
	
	
	p4_test = P4_Ops(**args_di) 
	get_di_src_from_p4(p4_repo, p4_test)
	delete_client(p4_test) 

if __name__ == '__main__':
	sys.exit(main())
