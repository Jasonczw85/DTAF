import os, sys, re, string, shutil, time, getpass, socket
import platform, random
import logging
from Bi_section import Bi_Section_Search_On_P4

class Bisec_Binary_Search_On_P4(Bi_Section_Search_On_P4):
    """
    This class is used to binary search on p4, it's derived from class of Bi_Section_Search_On_P4,
    so, the search algrithom is bi section.
    For example:
    
     <--- 6---------> failed at the start one
     |    5
     |    4   <-------------|If pass, then test upwards
     |--->3--->| test the middle one --->|
          2<---| If failed, then test downwards.
          1-------> pass at the end one 
    
    """
    
    def __init__(self, args):
        
        self._start_cl = args['start_cl']
        self._end_cl = args['end_cl']
        self._p4_instance = args['p4_instance']
        self._first_end_cl = self._end_cl

        self.logger = logging.getLogger('Bi_section_binary_search')
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(os.path.join(os.getcwd(),'Bi_section_binary_search.txt'),'w')
        fh.setLevel(logging.INFO)
        
        formatter = logging.Formatter(\
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        

    def sync_p4_src(self):
        (p4_numbers, self._mid_cl) = self.calculate_run()
        self.logger.info(self._p4_changelists)
        print p4_numbers, self._mid_cl
        print "Start to [sync] P4 to middle cl............. : ", self._mid_cl
        self.logger.info("Start to [sync] P4 to middle cl............. : %d" %(self._mid_cl))
        self.logger.info("P4 instance work space to middle cl............. : %s" %(self._p4_instance._client_root))
        self._p4_instance.connect_svr_sync_depot(self._mid_cl)

    def run_binary_search(self):
    
        while int(self._end_cl) < int(self._mid_cl):
        
            self.logger.info("endcl %d and midcl %d" %(self._end_cl, self._mid_cl))
            ret_pass_to_build_cl, build_kit_pass = self.build_kit_to_pass()
            
            if ret_pass_to_build_cl > self._end_cl and \
               ret_pass_to_build_cl != self._mid_cl:
                print "Update mid_cl"
                self._mid_cl = ret_pass_to_build_cl
            if build_kit_pass == 0:
                kit_test_ret = self.run_kit_testing()
            else:
                print "No changelist can pass the build"
                sys.exit(1)

            if kit_test_ret:
                print "Kit itaf runtime test: failed at mid_cl", self._mid_cl
                self.logger.info("Kit itaf runtime test: Failed at %d" %self._mid_cl)
                print "Update change list: start_cl = mid_cl"
                self._start_cl = self._mid_cl

            else: # run kit testing pass
                print "Kit itaf runtime test: Passed at mid_cl", self._mid_cl
                self.logger.info("Kit itaf runtime test: Passed at %d" %self._mid_cl)
                print "Update change list: end_cl = mid_cl"
                self._end_cl = self._mid_cl
                print "New enc_cl is ", self._end_cl

            self.sync_p4_src()
            self.logger.info("Sync p4 src to midcl %d" %self._mid_cl)
            
        self.logger.info("Out from loop: endcl %d and midcl %d" %(self._end_cl, self._mid_cl))
        
        if self._end_cl == self._first_end_cl:
            self._p4_instance.connect_svr_sync_depot(self._end_cl)
            ret_pass_to_build_cl, build_kit_pass = self.build_kit_to_pass()
            if build_kit_pass == 0:
                kit_test_ret = self.run_kit_testing()
            else:
                print "No change list can pass the build"
                sys.exit(1)
            if kit_test_ret:
                print "Kit itaf runtime test: failed at end_cl, Please check", self._end_cl
                return
            
        print "Found the changelist bring the failure", self._start_cl
        return self._start_cl
        
    def build_kit_to_pass(self):
        
        return

    def run_kit_testing(self):
        
        return
        
