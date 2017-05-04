from p4_opr import P4_Ops 
from optparse import OptionParser
import sys

def test_p4():

    print "Start to test P4"
    kwargs={ \
    'port': "10.204.4.28:1999", \
    'user': "hxzhan", \
    'password': "Dolby.123456", \
    #'client_name': "",  \
    #'client_root': "/home/hxzhan/testp4", \
    #'client_root': "", \
    'depot': "//depot/ger/dlb_intrinsics/main/dlb_intrinsics/..." \
    }
    p4_test = P4_Ops(**kwargs)
    
    sync_cl = "dlb_intrinsics_v1.9_rc02"
    print "Start to test ........................", sync_cl

    success = p4_test.connect_svr_sync_depot(sync_cl) 
    p4_test.get_current_p4_numbers(5)
    
    sync_cl = 2015922
    print "Start to test ........................", sync_cl

    success = p4_test.connect_svr_sync_depot(sync_cl) 
    p4_test.get_current_p4_numbers(2)

    sync_cl = "2014/11/01"
    print "Start to test ........................", sync_cl

    success = p4_test.connect_svr_sync_depot(sync_cl)
    # get a tuple
    
    print success[0]
    
    p4_test.connect_svr_sync_depot()
    p4_test.get_current_p4_numbers(4)
    p4_test.cleanup_remote_client()
    print "Pass to test P4"

    
def test_p4_concurrency():

    print "Start to test P4 Concunrrency"
    
    
    #dest_cl_file = "p4_changelist.log"
    #saveout = sys.stdout
    #f1 = open(dest_cl_file, "w+")
    #sys.stdout = f1
    
   
    kwargs1={ \
    'port': "10.204.4.28:1999", \
    'user': "hxzhan", \
    'password': "Dolby.123456", \
    #'client_name': "",  \
    #'client_root': "/home/atgqa/testp4", \
    #'client_root': "", \
    'depot': "//depot/ger/dlb_intrinsics/main/dlb_intrinsics/..." \
    }
    
    kwargs2={ \
    'port': "10.204.4.28:1999", \
    'user': "hxzhan", \
    'password': "Dolby.123456", \
    #'client_name': "",  \
    #'client_root': "/home/atgqa/testp4_2", \
    #'client_root': "", \
    'depot': "//depot/ger/dlb_intrinsics/main/dlb_intrinsics/..." \
    }    
    
    
    p4_test1 = P4_Ops(**kwargs1)
    p4_test2 = P4_Ops(**kwargs2)
    
    sync_cl1 = "dlb_intrinsics_v1.9_rc01"
    print "Start to test ........................", sync_cl1
    success1 = p4_test1.connect_svr_sync_depot(sync_cl1) 
    p4_test1.get_current_p4_numbers(4)

    
    
    sync_cl2 = 2015922
    print "Start to test ........................", sync_cl2
    success2 = p4_test2.connect_svr_sync_depot(sync_cl2) 
    p4_test2.get_current_p4_numbers(4)

    print "Start to clean up test1 client"
    p4_test1.cleanup_remote_client()
    print "Start to clean up test2 client"
    p4_test2.cleanup_remote_client()
    
    #f1.close()
    #sys.stdout = saveout
    #f1.close()
    print "Pass to test P4 Concunrrency"
    

if __name__ == '__main__':
    
    test_p4()
    
    test_p4_concurrency()